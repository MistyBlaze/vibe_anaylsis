# Flight Delay Dataset Analysis (2018–2024)

## Download status
- Attempted to install the `kagglehub` helper library and download `shubhamsingh42/flight-delay-dataset-2018-2024`.
- The environment blocks outbound HTTPS requests through the proxy (HTTP 403), so neither `pip install kagglehub` nor any Kaggle download requests can succeed.
- Because the dataset cannot be retrieved in this environment, no data files were added to the repository.

## How to download locally (when network access is available)
1. Generate a Kaggle API token from https://www.kaggle.com/settings/account ("Create New Token").
2. Place the downloaded `kaggle.json` in `~/.kaggle/` and ensure it has permissions `600` (`chmod 600 ~/.kaggle/kaggle.json`).
3. From the repository root, run:
   ```bash
   pip install kagglehub  # or `pip install kaggle`
   kaggle datasets download -d shubhamsingh42/flight-delay-dataset-2018-2024 -p data/flight-delay-dataset-2018-2024
   unzip data/flight-delay-dataset-2018-2024/flight-delay-dataset-2018-2024.zip -d data/flight-delay-dataset-2018-2024
   ```
4. Verify the extracted CSV files before running any analysis notebooks or scripts.

## Suggested analysis workflow (once data is available)
- **Data validation**: Inspect column names (likely includes `FL_DATE`, `OP_CARRIER`, `ORIGIN`, `DEST`, `ARR_DELAY`, `DEP_DELAY`, etc.), check for missing values, and confirm date ranges.
- **Feature engineering**:
  - Parse `FL_DATE` into `datetime` and derive `year`, `month`, `day_of_week`, and `is_peak_travel_season` flags.
  - Create delay flags (`arr_delay_flag = ARR_DELAY > 15`, `dep_delay_flag = DEP_DELAY > 15`).
- **Core metrics**:
  - Overall on-time performance: share of flights with arrival delay ≤ 15 minutes.
  - Average and median arrival/departure delays by carrier, airport, and route.
  - Cancellation and diversion rates (if the columns are present).
  - Distribution of delay causes (weather, carrier, NAS, late aircraft, security) if the dataset exposes them.
- **Temporal patterns**:
  - Monthly trend of average arrival delay and cancellation rate from 2018–2024.
  - Compare peak months (e.g., summer and winter holidays) vs. off-peak periods.
- **Airport-level insights**:
  - Identify airports with the highest average delay minutes and worst on-time percentages.
  - Map hub airports vs. regional airports to contrast performance.
- **Carrier benchmarking**:
  - Rank carriers by on-time percentage and average delay duration.
  - Highlight carriers with consistent improvements or deteriorations over time.

### Example starter code (to run once the CSVs are present)
```python
import pandas as pd
from pathlib import Path

data_dir = Path("data/flight-delay-dataset-2018-2024")
files = list(data_dir.glob("*.csv"))
frames = [pd.read_csv(f, parse_dates=["FL_DATE"]) for f in files]
df = pd.concat(frames, ignore_index=True)

# Basic delay flags
for col in ["ARR_DELAY", "DEP_DELAY"]:
    if col in df:
        df[f"{col.lower()}_flag"] = df[col] > 15

# Monthly arrival delay summary
monthly = (
    df
    .assign(month=lambda d: d["FL_DATE"].dt.to_period("M"))
    .groupby("month")
    .agg(
        flights=("FL_DATE", "size"),
        avg_arr_delay=("ARR_DELAY", "mean"),
        on_time_rate=("arr_delay_flag", lambda x: 1 - x.mean()),
    )
    .reset_index()
)
monthly["month"] = monthly["month"].astype(str)
monthly.to_csv("analysis/monthly_delay_summary.csv", index=False)
print(monthly.head())
```

## Next steps
- Re-run the download steps once network access is available.
- Execute the starter code (or a notebook) to populate summary CSVs and charts.
- Update this document with actual findings (e.g., top delayed carriers, seasonal spikes, improvement trends) after running the analysis.
