# Day-ahead capacity planning: results

Train: until 2025-01-01; calibration: until 2025-07-01; test: 2025-07-01 to 2026-10-31 (11712 hours). Costs: capacity 1.0, unserved load 10.0; target: about 10% of hours short.

| method                                                   |   total cost |   hours short (%) |   unserved load (%) |   avg capacity | cost vs 28-day peak rule   |
|:---------------------------------------------------------|-------------:|------------------:|--------------------:|---------------:|:---------------------------|
| Rule: peak of the last 28 days                           |       393241 |               0.4 |                0.63 |          33    | 0.0%                       |
| Rule: same hour last week + 20% headroom                 |       168236 |              14.7 |                3.79 |          10.92 | -57.2%                     |
| LightGBM quantile model (90%)                            |       158394 |              20.3 |                4.13 |           9.77 | -59.7%                     |
| LightGBM + conformal, calibrated once                    |       156046 |              12.7 |                3.31 |          10.32 | -60.3%                     |
| LightGBM + conformal, re-calibrated daily (last 28 days) |       158389 |              11.1 |                2.89 |          10.9  | -59.7%                     |

## During traffic spikes

| method                                                   |   hours short during top-1% traffic (%) |
|:---------------------------------------------------------|----------------------------------------:|
| Rule: peak of the last 28 days                           |                                    31.4 |
| Rule: same hour last week + 20% headroom                 |                                    80.5 |
| LightGBM quantile model (90%)                            |                                    92.4 |
| LightGBM + conformal, calibrated once                    |                                    88.1 |
| LightGBM + conformal, re-calibrated daily (last 28 days) |                                    81.4 |

## Hours short per month (%), conformal methods

| ts                  |   LightGBM + conformal, calibrated once |   LightGBM + conformal, re-calibrated daily (last 28 days) |
|:--------------------|----------------------------------------:|-----------------------------------------------------------:|
| 2025-07-01 00:00:00 |                                    24.5 |                                                       17.1 |
| 2025-08-01 00:00:00 |                                    18.1 |                                                       12.8 |
| 2025-09-01 00:00:00 |                                     3.1 |                                                        1   |
| 2025-10-01 00:00:00 |                                    14   |                                                       19.8 |
| 2025-11-01 00:00:00 |                                    27.4 |                                                        9.3 |
| 2025-12-01 00:00:00 |                                     4.6 |                                                        5.6 |
| 2026-01-01 00:00:00 |                                    14.7 |                                                       14.2 |
| 2026-02-01 00:00:00 |                                     4.8 |                                                        5.7 |
| 2026-03-01 00:00:00 |                                     5   |                                                       11.2 |
| 2026-04-01 00:00:00 |                                    10.6 |                                                       14.6 |
| 2026-05-01 00:00:00 |                                    16   |                                                       11   |
| 2026-06-01 00:00:00 |                                    16.2 |                                                       11.5 |
| 2026-07-01 00:00:00 |                                    18.8 |                                                       15.7 |
| 2026-08-01 00:00:00 |                                    10.2 |                                                        9.4 |
| 2026-09-01 00:00:00 |                                     6.5 |                                                        6   |
| 2026-10-01 00:00:00 |                                     7.4 |                                                       11.4 |
