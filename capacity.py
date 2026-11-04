"""Day-ahead capacity planning under uncertain traffic.

Every evening, choose how much capacity to run for each hour of tomorrow. Capacity costs CO per unit
and hour; load that is not served costs CU per unit. Minimising CO*capacity + CU*unserved load gives
the newsvendor rule: plan for the quantile Q = 1 - CO/CU of tomorrow's load (here the 90th percentile).
"""
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

DATA = Path("data/hourly.csv")
OUT = Path("results")
CO, CU = 1.0, 10.0                      # cost of one unit of capacity vs one unit of unserved load
Q = 1 - CO / CU                         # = 0.9
TRAIN_END, CAL_END = "2025-01-01", "2025-07-01"
FEATURES = ["hour", "dow", "month", "lag24", "lag48", "lag168", "lag336", "mean7d_samehour"]


def load():
    df = pd.read_csv(DATA, parse_dates=["ts"]).set_index("ts").asfreq("h")
    df["views"] = df["views"].interpolate()
    unit = df["views"].median() / 10     # 1 capacity unit = a tenth of a typical hour's load
    df["load"] = df["views"] / unit
    for lag in (24, 48, 168, 336):       # all known by the evening before
        df[f"lag{lag}"] = df["load"].shift(lag)
    df["mean7d_samehour"] = sum(df["load"].shift(24 * k) for k in range(1, 8)) / 7
    df["peak28d"] = df["load"].shift(24).rolling(24 * 28).max()
    df["hour"], df["dow"], df["month"] = df.index.hour, df.index.day_of_week, df.index.month
    return df.dropna()


def evaluate(name, cap, load):
    short = np.maximum(load - cap, 0)
    return {"method": name,
            "total cost": round(float((CO * cap + CU * short).sum())),
            "hours short (%)": round(100 * float((short > 0).mean()), 1),
            "unserved load (%)": round(100 * float(short.sum() / load.sum()), 2),
            "avg capacity": round(float(cap.mean()), 2)}


def main():
    df = load()
    train = df[df.index < TRAIN_END]
    cal = df[(df.index >= TRAIN_END) & (df.index < CAL_END)]
    test = df[df.index >= CAL_END]
    y = test["load"].to_numpy()
    params = dict(n_estimators=400, learning_rate=0.05, num_leaves=31, verbose=-1)

    caps = {
        "Rule: peak of the last 28 days": test["peak28d"].to_numpy(),
        "Rule: same hour last week + 20% headroom": 1.2 * test["lag168"].to_numpy(),
    }

    qmodel = lgb.LGBMRegressor(objective="quantile", alpha=Q, **params).fit(train[FEATURES], train["load"])
    caps[f"LightGBM quantile model ({Q:.0%})"] = qmodel.predict(test[FEATURES])

    # Point forecast on the log scale, then a conformal offset so that ~90% of hours are covered
    pmodel = lgb.LGBMRegressor(objective="regression", **params).fit(train[FEATURES], np.log(train["load"]))
    residuals = pd.Series(np.log(df["load"]) - pmodel.predict(df[FEATURES]), index=df.index)
    point = pmodel.predict(test[FEATURES])
    once = np.quantile(residuals.loc[cal.index], Q)
    caps["LightGBM + conformal, calibrated once"] = np.exp(point + once)
    daily = residuals.shift(24).rolling(24 * 28).quantile(Q).loc[test.index].to_numpy()
    caps["LightGBM + conformal, re-calibrated daily (last 28 days)"] = np.exp(point + daily)

    table = pd.DataFrame([evaluate(name, cap, y) for name, cap in caps.items()])
    base = table.loc[0, "total cost"]
    table["cost vs 28-day peak rule"] = (100 * (table["total cost"] - base) / base).round(1).astype(str) + "%"

    spikes = y >= np.quantile(y, 0.99)
    spike_rows = [{"method": n, "hours short during top-1% traffic (%)":
                   round(100 * float((y[spikes] > c[spikes]).mean()), 1)} for n, c in caps.items()]

    monthly = pd.DataFrame({name: pd.Series(y > cap, index=test.index).resample("MS").mean() * 100
                            for name, cap in caps.items() if "conformal" in name}).round(1)

    OUT.mkdir(exist_ok=True)
    lines = ["# Day-ahead capacity planning: results", "",
             f"Train: until {TRAIN_END}; calibration: until {CAL_END}; test: {test.index.min():%Y-%m-%d} "
             f"to {test.index.max():%Y-%m-%d} ({len(test)} hours). Costs: capacity {CO}, unserved load {CU}; "
             f"target: about {100 * (1 - Q):.0f}% of hours short.", "",
             table.to_markdown(index=False), "",
             "## During traffic spikes", "", pd.DataFrame(spike_rows).to_markdown(index=False), "",
             "## Hours short per month (%), conformal methods", "", monthly.to_markdown()]
    (OUT / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
