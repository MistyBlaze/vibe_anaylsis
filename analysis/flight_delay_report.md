# Flight Delay Dataset Analysis (2018–2024)

## Overall performance

* Flights analyzed: 582,425
* Average arrival delay: 10.66 minutes
* Average departure delay: 15.97 minutes
* On-time arrival rate (≤15 min): 76.65%
* Cancellation rate: 3.79%
* Diversion rate: 0.28%

## Monthly trend overview

| month   | flights | avg_arr_delay | avg_dep_delay | on_time_rate | cancellation_rate |
| ------- | ------- | ------------- | ------------- | ------------ | ----------------- |
| 2024-01 | 582,425 |         10.66 |         15.97 |        76.6% |              3.8% |

## Carrier ranking (top 10 by flight volume)

| OP_CARRIER | flights | avg_arr_delay | on_time_rate |
| ---------- | ------- | ------------- | ------------ |
| AA         | 147,443 |         16.28 |        73.7% |
| DL         | 116,199 |          7.58 |        80.1% |
| WN         | 115,389 |          6.42 |        77.3% |
| UA         | 104,791 |         10.15 |        78.6% |
| AS         |  29,057 |          9.95 |        74.7% |
| NK         |  20,415 |          9.68 |        74.5% |
| B6         |  19,580 |         13.52 |        71.8% |
| F9         |  14,379 |         14.72 |        73.5% |
| G4         |   8,596 |         10.53 |        78.3% |
| HA         |   6,576 |         10.66 |        74.4% |

## Origin airport performance (top 10 by departures)

| ORIGIN | flights | avg_arr_delay | on_time_rate |
| ------ | ------- | ------------- | ------------ |
| ATL    |  26,363 |          7.28 |        79.8% |
| DEN    |  24,500 |         10.69 |        74.7% |
| DFW    |  23,743 |         17.21 |        70.5% |
| ORD    |  22,999 |         21.89 |        67.2% |
| CLT    |  19,126 |         11.75 |        75.0% |
| PHX    |  15,573 |          7.73 |        80.0% |
| LAX    |  15,341 |          5.31 |        81.4% |
| LAS    |  15,053 |          6.11 |        79.0% |
| MCO    |  14,296 |         12.47 |        74.2% |
| SEA    |  13,140 |          9.35 |        76.8% |

## Busiest routes (top 10 by flights)

| ORIGIN | DEST | flights | avg_arr_delay | on_time_rate |
| ------ | ---- | ------- | ------------- | ------------ |
| OGG    | HNL  |   1,001 |          9.31 |        76.6% |
| HNL    | OGG  |     994 |          5.20 |        81.1% |
| LAX    | SFO  |     858 |         11.52 |        68.5% |
| SFO    | LAX  |     857 |          2.70 |        80.1% |
| PHX    | DEN  |     832 |          4.77 |        81.8% |
| DEN    | PHX  |     831 |          6.89 |        74.5% |
| ATL    | MCO  |     792 |          9.42 |        76.7% |
| MCO    | ATL  |     792 |         12.45 |        76.1% |
| LGA    | ORD  |     789 |         10.55 |        76.9% |
| ORD    | LGA  |     789 |         19.96 |        69.2% |

## Delay minutes by cause

| Cause               | Delay Minutes |
| ------------------- | ------------- |
| Late Aircraft Delay |  4,115,702.00 |
| Carrier Delay       |  3,316,361.00 |
| Nas Delay           |  1,819,379.00 |
| Weather Delay       |  1,079,912.00 |
| Security Delay      |     22,832.00 |
