"""Robustness checks for the capacity-planning results.

1. Bootstrap confidence intervals for cost differences between methods, resampling whole weeks
   (hours within a week are strongly correlated, so resampling single hours would be too optimistic).
2. Sensitivity to the assumed cost ratio: shortage cost 5x, 10x and 20x the capacity cost.
3. Calibration stability: average distance, per month, from the target share of short hours.
"""
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from capacity import CAL_END, FEATURES, TRAIN_END, load

OUT = Path("results")
CO = 1.0
B = 2000
RNG = np.random.default_rng(0)
PARAMS = dict(n_estimators=400, learning_rate=0.05, num_leaves=31, verbose=-1)
SIMPLE = "Rule: same hour last week + 20% headroom"
PEAK = "Rule: peak of the last 28 days"


def split(df):
    train = df[df.index < TRAIN_END]
    cal = df[(df.index >= TRAIN_END) & (df.index < CAL_END)]
    test = df[df.index >= CAL_END]
    return train, cal, test


def point_model(df, train):
    """Point forecast on the log scale; its residuals feed the conformal offsets."""
    model = lgb.LGBMRegressor(objective="regression", **PARAMS).fit(train[FEATURES], np.log(train["load"]))
    residuals = pd.Series(np.log(df["load"]) - model.predict(df[FEATURES]), index=df.index)
    return model, residuals


def build_caps(q, train, cal, test, model, residuals):
    caps = {PEAK: test["peak28d"].to_numpy(), SIMPLE: 1.2 * test["lag168"].to_numpy()}
    qmodel = lgb.LGBMRegressor(objective="quantile", alpha=q, **PARAMS).fit(train[FEATURES], train["load"])
    caps["LightGBM quantile model"] = qmodel.predict(test[FEATURES])
    point = model.predict(test[FEATURES])
    caps["Conformal, calibrated once"] = np.exp(point + np.quantile(residuals.loc[cal.index], q))
    daily = residuals.shift(24).rolling(24 * 28).quantile(q).loc[test.index].to_numpy()
    caps["Conformal, re-calibrated daily"] = np.exp(point + daily)
    return caps


def hourly_cost(cap, y, cu):
    return CO * cap + cu * np.maximum(y - cap, 0)


def bootstrap_diff(cost_a, cost_b, weeks):
    """Percent difference in total cost (a vs b), with a 95% interval from resampling whole weeks."""
    wa = pd.Series(cost_a).groupby(weeks).sum().to_numpy()
    wb = pd.Series(cost_b).groupby(weeks).sum().to_numpy()
    idx = RNG.integers(0, len(wa), size=(B, len(wa)))
    diffs = 100 * (wa[idx].sum(1) - wb[idx].sum(1)) / wb[idx].sum(1)
    point = 100 * (wa.sum() - wb.sum()) / wb.sum()
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return f"{point:+.1f}% [{lo:+.1f}, {hi:+.1f}]"


def main():
    df = load()
    train, cal, test = split(df)
    y = test["load"].to_numpy()
    weeks = ((test.index - test.index[0]).days // 7).to_numpy()
    model, residuals = point_model(df, train)

    # 1 + 3: main setting (shortage cost 10x)
    cu = 10.0
    q = 1 - CO / cu
    caps = build_caps(q, train, cal, test, model, residuals)
    costs = {name: hourly_cost(cap, y, cu) for name, cap in caps.items()}
    boot_rows = [{"method": name,
                  "cost vs simple rule [95% CI]": bootstrap_diff(costs[name], costs[SIMPLE], weeks),
                  "cost vs peak rule [95% CI]": bootstrap_diff(costs[name], costs[PEAK], weeks)}
                 for name in caps]

    target = 100 * (1 - q)
    calib_rows = []
    for name, cap in caps.items():
        monthly = pd.Series(y > cap, index=test.index).resample("MS").mean() * 100
        calib_rows.append({"method": name,
                           "hours short overall (%)": round(float((y > cap).mean() * 100), 1),
                           "avg monthly distance from target (pts)": round(float((monthly - target).abs().mean()), 1),
                           "worst month (% short)": round(float(monthly.max()), 1)})

    # 2: sensitivity to the cost ratio
    sens_rows = []
    for cu in (5.0, 10.0, 20.0):
        q = 1 - CO / cu
        caps_cu = build_caps(q, train, cal, test, model, residuals)
        base = hourly_cost(caps_cu[SIMPLE], y, cu).sum()
        for name, cap in caps_cu.items():
            total = hourly_cost(cap, y, cu).sum()
            sens_rows.append({"shortage cost": f"{cu:.0f}x", "target short (%)": round(100 * (1 - q), 1),
                              "method": name, "hours short (%)": round(float((y > cap).mean() * 100), 1),
                              "cost vs simple rule": f"{100 * (total - base) / base:+.1f}%"})

    lines = ["# Robustness checks", "",
             f"Test period: {test.index.min():%Y-%m-%d} to {test.index.max():%Y-%m-%d}; "
             f"bootstrap: {B} resamples of whole weeks.", "",
             "## 1. Cost differences with 95% confidence intervals (shortage cost 10x)", "",
             pd.DataFrame(boot_rows).to_markdown(index=False), "",
             f"## 2. Calibration stability (target: {target:.0f}% of hours short)", "",
             pd.DataFrame(calib_rows).to_markdown(index=False), "",
             "## 3. Sensitivity to the assumed cost ratio", "",
             pd.DataFrame(sens_rows).to_markdown(index=False)]
    OUT.mkdir(exist_ok=True)
    (OUT / "robustness.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
