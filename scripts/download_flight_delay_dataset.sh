#!/usr/bin/env bash
set -euo pipefail

if ! command -v unzip >/dev/null 2>&1; then
  echo "Error: unzip command is required to extract the dataset." >&2
  exit 1
fi

DATA_DIR="data/flight-delay-dataset-2018-2024"
ZIP_PATH="$DATA_DIR/flight-delay-dataset-2018-2024.zip"

if [[ -z "${KAGGLE_USERNAME:-}" || -z "${KAGGLE_KEY:-}" ]]; then
  cat >&2 <<'MSG'
Error: Kaggle credentials are required.

Set the KAGGLE_USERNAME and KAGGLE_KEY environment variables with the
values from your kaggle.json token before running this script:

  export KAGGLE_USERNAME="<your_username>"
  export KAGGLE_KEY="<your_token>"
MSG
  exit 1
fi

mkdir -p "$DATA_DIR"

if command -v kaggle >/dev/null 2>&1; then
  kaggle datasets download -d shubhamsingh42/flight-delay-dataset-2018-2024 -p "$DATA_DIR" --force
else
  echo "Kaggle CLI not found. Falling back to curl." >&2
  curl --fail --location \
    --user "${KAGGLE_USERNAME}:${KAGGLE_KEY}" \
    -o "$ZIP_PATH" \
    "https://www.kaggle.com/api/v1/datasets/download/shubhamsingh42/flight-delay-dataset-2018-2024"
fi

if [[ ! -f "$ZIP_PATH" ]]; then
  ZIP_PATH=$(ls "$DATA_DIR"/flight-delay-dataset-2018-2024.zip 2>/dev/null | head -n 1 || true)
fi

if [[ ! -f "$ZIP_PATH" ]]; then
  echo "Download did not produce the expected zip archive." >&2
  exit 1
fi

echo "Extracting $(basename "$ZIP_PATH") to $DATA_DIR" >&2
unzip -o "$ZIP_PATH" -d "$DATA_DIR" >/dev/null

echo "Dataset ready in $DATA_DIR" >&2
