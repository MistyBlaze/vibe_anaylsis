"""Helpers for locating Kaggle CSV exports locally."""
from __future__ import annotations

from pathlib import Path
from typing import List
import zipfile


def collect_csv_files(data_dir: Path) -> List[Path]:
    """Return all CSV files under ``data_dir``.

    If no CSV files are present, look for ``.zip`` archives inside the
    directory (recursively) and extract them next to the archive so the
    CSVs become available for downstream processing.
    """

    csv_files = sorted(p for p in data_dir.rglob("*.csv") if p.is_file())
    if csv_files:
        return csv_files

    extracted_any = False
    for zip_path in sorted(p for p in data_dir.rglob("*.zip") if p.is_file()):
        try:
            with zipfile.ZipFile(zip_path) as archive:
                members = [
                    info
                    for info in archive.infolist()
                    if not info.is_dir() and info.filename.lower().endswith(".csv")
                ]
                if not members:
                    continue
                archive.extractall(path=zip_path.parent)
                extracted_any = True
        except zipfile.BadZipFile:
            continue

    if extracted_any:
        return sorted(p for p in data_dir.rglob("*.csv") if p.is_file())
    return []
