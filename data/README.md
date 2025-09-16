# Data Directory

The Kaggle dataset `shubhamsingh42/flight-delay-dataset-2018-2024` could not be downloaded in this environment because all outgoing HTTPS requests are blocked by a proxy (HTTP 403).

To populate this folder on a machine with network access:

```bash
export KAGGLE_USERNAME="<your_username>"
export KAGGLE_KEY="<your_token>"
./scripts/download_flight_delay_dataset.sh
```

The helper script stores the archive and extracted CSV files under `data/flight-delay-dataset-2018-2024/`. Once the files are present, run `python analysis/generate_flight_delay_report.py` from the repository root to create the Markdown summary.

Both the report generator and chart builder now scan the data directory recursively and automatically extract any Kaggle-provided zip archives you drop here, so keeping the original download intact is sufficient.
