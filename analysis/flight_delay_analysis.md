# Flight Delay Dataset Analysis (2018–2024)

## Current status
- Outbound HTTPS traffic from this environment is blocked by a proxy, so Kaggle downloads fail with `curl: (56) CONNECT tunnel failed, response 403`.
- Installing helper libraries such as `kagglehub` via `pip` also fails for the same reason.
- Because the dataset cannot be retrieved here, no CSV files are stored in the repository yet.

## Downloading the dataset locally (when network access is available)
1. Generate a Kaggle API token from <https://www.kaggle.com/settings/account> and keep the username/key handy.
2. On a machine with internet access, export your credentials in the current shell:
   ```bash
   export KAGGLE_USERNAME="<your_username>"
   export KAGGLE_KEY="<your_token>"
   ```
3. From the repository root, run the helper script which uses the Kaggle CLI when available and falls back to the Kaggle API via `curl`:
   ```bash
   ./scripts/download_flight_delay_dataset.sh
   ```
   The archive is saved to `data/flight-delay-dataset-2018-2024/flight-delay-dataset-2018-2024.zip` and is extracted into the same directory.
4. (Optional) To keep the zip file, leave it in place; otherwise, delete it after extraction to save space.

## Generating the Markdown report
Once the CSV files are present in `data/flight-delay-dataset-2018-2024/`, stream them into aggregated metrics with:

```bash
python analysis/generate_flight_delay_report.py
```

Key flags:

- `--chunksize` controls how many rows are read at a time (default `250000`).
- `--limit-files` is handy for quick smoke tests (for example, `--limit-files 1`).
- `--output` allows writing the report to an alternate location.

The script writes `analysis/flight_delay_report.md` and is designed to handle the multi-million-row dataset without loading everything into memory.

## Report contents (produced once data is available)
The generator compiles:

- **Overall performance**: total flights, average arrival/departure delays, on-time rate (≤15 minutes), cancellation/diversion rates.
- **Monthly trend table**: month-by-month flights, average delays, and reliability rates.
- **Carrier leaderboard**: top 10 carriers by flight volume with average arrival delay and on-time percentage.
- **Origin airport view**: top 10 departure airports by volume with the same reliability metrics.
- **Busiest routes**: leading origin/destination pairs by flight count and delay performance.
- **Delay causes**: total delay minutes attributed to carrier, weather, NAS, security, and late aircraft factors when the dataset exposes those columns.

## After the dataset is available
- Re-run the download script if new Kaggle updates are published.
- Execute `analysis/generate_flight_delay_report.py` to refresh the Markdown summary.
- Augment this document with actual findings (e.g., carriers with the worst delays, seasonal spikes, improvements over time) using the generated report as evidence.
