# Robustness checks

Test period: 2025-07-01 to 2026-10-31; bootstrap: 2000 resamples of whole weeks.

## 1. Cost differences with 95% confidence intervals (shortage cost 10x)

| method                                   | cost vs simple rule [95% CI]   | cost vs peak rule [95% CI]   |
|:-----------------------------------------|:-------------------------------|:-----------------------------|
| Rule: peak of the last 28 days           | +133.7% [+103.8, +167.4]       | +0.0% [+0.0, +0.0]           |
| Rule: same hour last week + 20% headroom | +0.0% [+0.0, +0.0]             | -57.2% [-63.1, -50.9]        |
| LightGBM quantile model                  | -5.9% [-7.8, -4.1]             | -59.7% [-64.9, -53.9]        |
| Conformal, calibrated once               | -7.2% [-9.2, -5.4]             | -60.3% [-65.4, -54.6]        |
| Conformal, re-calibrated daily           | -5.9% [-8.4, -3.6]             | -59.7% [-64.9, -53.9]        |

## 2. Calibration stability (target: 10% of hours short)

| method                                   |   hours short overall (%) |   avg monthly distance from target (pts) |   worst month (% short) |
|:-----------------------------------------|--------------------------:|-----------------------------------------:|------------------------:|
| Rule: peak of the last 28 days           |                       0.4 |                                      9.6 |                     2.2 |
| Rule: same hour last week + 20% headroom |                      14.7 |                                      7.7 |                    34   |
| LightGBM quantile model                  |                      20.3 |                                     10.7 |                    35.2 |
| Conformal, calibrated once               |                      12.7 |                                      6.2 |                    27.4 |
| Conformal, re-calibrated daily           |                      11.1 |                                      3.9 |                    19.8 |

## 3. Sensitivity to the assumed cost ratio

| shortage cost   |   target short (%) | method                                   |   hours short (%) | cost vs simple rule   |
|:----------------|-------------------:|:-----------------------------------------|------------------:|:----------------------|
| 5x              |                 20 | Rule: peak of the last 28 days           |               0.4 | +163.4%               |
| 5x              |                 20 | Rule: same hour last week + 20% headroom |              14.7 | +0.0%                 |
| 5x              |                 20 | LightGBM quantile model                  |              27.9 | -7.6%                 |
| 5x              |                 20 | Conformal, calibrated once               |              21.8 | -7.9%                 |
| 5x              |                 20 | Conformal, re-calibrated daily           |              20.8 | -7.5%                 |
| 10x             |                 10 | Rule: peak of the last 28 days           |               0.4 | +133.7%               |
| 10x             |                 10 | Rule: same hour last week + 20% headroom |              14.7 | +0.0%                 |
| 10x             |                 10 | LightGBM quantile model                  |              20.3 | -5.9%                 |
| 10x             |                 10 | Conformal, calibrated once               |              12.7 | -7.2%                 |
| 10x             |                 10 | Conformal, re-calibrated daily           |              11.1 | -5.9%                 |
| 20x             |                  5 | Rule: peak of the last 28 days           |               0.4 | +91.7%                |
| 20x             |                  5 | Rule: same hour last week + 20% headroom |              14.7 | +0.0%                 |
| 20x             |                  5 | LightGBM quantile model                  |              14.5 | -7.4%                 |
| 20x             |                  5 | Conformal, calibrated once               |               7.6 | -11.0%                |
| 20x             |                  5 | Conformal, re-calibrated daily           |               6.2 | -9.0%                 |
