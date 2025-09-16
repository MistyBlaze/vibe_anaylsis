#!/usr/bin/env python3
"""Generate a Markdown report for the flight delay dataset."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

DELAY_CAUSE_COLUMNS = {
    "CARRIER_DELAY": "carrier_delay_sum",
    "WEATHER_DELAY": "weather_delay_sum",
    "NAS_DELAY": "nas_delay_sum",
    "SECURITY_DELAY": "security_delay_sum",
    "LATE_AIRCRAFT_DELAY": "late_aircraft_delay_sum",
}

COLUMN_ALIASES = {
    "FL_DATE": ["FL_DATE", "FlightDate"],
    "OP_CARRIER": [
        "OP_CARRIER",
        "IATA_Code_Marketing_Airline",
        "Marketing_Airline_Network",
        "IATA_Code_Operating_Airline",
        "Operating_Airline",
        "Operating_Airline ",
    ],
    "OP_UNIQUE_CARRIER": [
        "OP_UNIQUE_CARRIER",
        "DOT_ID_Marketing_Airline",
        "DOT_ID_Operating_Airline",
    ],
    "ORIGIN": ["ORIGIN", "Origin"],
    "DEST": ["DEST", "Dest"],
    "ARR_DELAY": ["ARR_DELAY", "ArrDelay", "ArrDelayMinutes"],
    "DEP_DELAY": ["DEP_DELAY", "DepDelay", "DepDelayMinutes"],
    "CANCELLED": ["CANCELLED", "Cancelled"],
    "DIVERTED": ["DIVERTED", "Diverted"],
    "CARRIER_DELAY": ["CARRIER_DELAY", "CarrierDelay"],
    "WEATHER_DELAY": ["WEATHER_DELAY", "WeatherDelay"],
    "NAS_DELAY": ["NAS_DELAY", "NASDelay"],
    "SECURITY_DELAY": ["SECURITY_DELAY", "SecurityDelay"],
    "LATE_AIRCRAFT_DELAY": ["LATE_AIRCRAFT_DELAY", "LateAircraftDelay"],
}

BASE_METRIC_FIELDS = [
    "flights",
    "arr_delay_sum",
    "arr_delay_count",
    "arr_delay_over_15",
    "dep_delay_sum",
    "dep_delay_count",
    "dep_delay_over_15",
    "cancelled",
    "diverted",
]

METRIC_FIELDS = BASE_METRIC_FIELDS + list(DELAY_CAUSE_COLUMNS.values())
COUNT_FIELDS = {
    "flights",
    "arr_delay_count",
    "arr_delay_over_15",
    "dep_delay_count",
    "dep_delay_over_15",
    "cancelled",
    "diverted",
}
SUM_FIELDS = set(METRIC_FIELDS) - COUNT_FIELDS
COLUMN_TO_METRICS = {
    "ARR_DELAY": {"arr_delay_sum", "arr_delay_count", "arr_delay_over_15"},
    "DEP_DELAY": {"dep_delay_sum", "dep_delay_count", "dep_delay_over_15"},
    "CANCELLED": {"cancelled"},
    "DIVERTED": {"diverted"},
}
for source_col, target_field in DELAY_CAUSE_COLUMNS.items():
    COLUMN_TO_METRICS.setdefault(source_col, set()).add(target_field)

DESIRED_COLUMNS = [
    "FL_DATE",
    "OP_CARRIER",
    "OP_UNIQUE_CARRIER",
    "ORIGIN",
    "DEST",
    "ARR_DELAY",
    "DEP_DELAY",
    "CANCELLED",
    "DIVERTED",
] + list(DELAY_CAUSE_COLUMNS.keys())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/flight-delay-dataset-2018-2024"),
        help="Directory containing the downloaded Kaggle CSV files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("analysis/flight_delay_report.md"),
        help="Path where the Markdown report should be written.",
    )
    parser.add_argument(
        "--chunksize",
        type=int,
        default=250_000,
        help="Number of rows to read per chunk when streaming large CSV files.",
    )
    parser.add_argument(
        "--limit-files",
        type=int,
        default=None,
        help="Optional limit on how many CSV files to process (useful for smoke tests).",
    )
    return parser.parse_args()


def new_stats() -> Dict[str, float]:
    stats = {}
    for field in METRIC_FIELDS:
        stats[field] = 0.0 if field in SUM_FIELDS else 0
    return stats


def normalize_flag(series: pd.Series) -> pd.Series:
    if series.empty:
        return pd.Series(dtype="int64")
    if pd.api.types.is_bool_dtype(series):
        return series.astype("int64")
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().any():
        return numeric.fillna(0).astype("int64")
    normalized = series.astype(str).str.strip().str.upper()
    mapping = {
        "Y": 1,
        "YES": 1,
        "TRUE": 1,
        "T": 1,
        "1": 1,
    }
    return normalized.map(mapping).fillna(0).astype("int64")


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace(0, np.nan)
    return numerator / denominator


def determine_available_columns(path: Path) -> Tuple[List[str], Dict[str, str]]:
    header = pd.read_csv(path, nrows=0)
    columns = list(header.columns)
    column_map: Dict[str, str] = {}
    for canonical in DESIRED_COLUMNS:
        aliases = COLUMN_ALIASES.get(canonical, [canonical])
        for alias in aliases:
            if alias in columns:
                column_map[canonical] = alias
                break
    if "FL_DATE" not in column_map:
        raise ValueError(f"FL_DATE column not found in {path}")
    usecols = sorted(set(column_map.values()))
    return usecols, column_map


def preprocess_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    chunk = chunk.copy()
    chunk["FL_DATE"] = pd.to_datetime(chunk["FL_DATE"], errors="coerce")
    chunk = chunk.dropna(subset=["FL_DATE"])
    chunk["month"] = chunk["FL_DATE"].dt.to_period("M")

    if "ARR_DELAY" in chunk.columns:
        chunk["ARR_DELAY"] = pd.to_numeric(chunk["ARR_DELAY"], errors="coerce")
        chunk["arr_delay_over_15"] = (chunk["ARR_DELAY"] > 15).astype("int64")
    if "DEP_DELAY" in chunk.columns:
        chunk["DEP_DELAY"] = pd.to_numeric(chunk["DEP_DELAY"], errors="coerce")
        chunk["dep_delay_over_15"] = (chunk["DEP_DELAY"] > 15).astype("int64")
    if "CANCELLED" in chunk.columns:
        chunk["CANCELLED"] = normalize_flag(chunk["CANCELLED"])
    if "DIVERTED" in chunk.columns:
        chunk["DIVERTED"] = normalize_flag(chunk["DIVERTED"])
    for cause_col in DELAY_CAUSE_COLUMNS:
        if cause_col in chunk.columns:
            chunk[cause_col] = pd.to_numeric(chunk[cause_col], errors="coerce").fillna(0.0)
    return chunk


def build_agg_spec(chunk: pd.DataFrame) -> Dict[str, Tuple[str, str]]:
    spec: Dict[str, Tuple[str, str]] = {"flights": ("FL_DATE", "size")}
    if "ARR_DELAY" in chunk.columns:
        spec.update(
            {
                "arr_delay_sum": ("ARR_DELAY", "sum"),
                "arr_delay_count": ("ARR_DELAY", "count"),
                "arr_delay_over_15": ("arr_delay_over_15", "sum"),
            }
        )
    if "DEP_DELAY" in chunk.columns:
        spec.update(
            {
                "dep_delay_sum": ("DEP_DELAY", "sum"),
                "dep_delay_count": ("DEP_DELAY", "count"),
                "dep_delay_over_15": ("dep_delay_over_15", "sum"),
            }
        )
    if "CANCELLED" in chunk.columns:
        spec["cancelled"] = ("CANCELLED", "sum")
    if "DIVERTED" in chunk.columns:
        spec["diverted"] = ("DIVERTED", "sum")
    for cause_col, field_name in DELAY_CAUSE_COLUMNS.items():
        if cause_col in chunk.columns:
            spec[field_name] = (cause_col, "sum")
    return spec


def update_table(
    table: Dict[Tuple, Dict[str, float]],
    grouped: pd.DataFrame,
) -> None:
    if grouped.empty:
        return
    for keys, row in grouped.iterrows():
        key_tuple = keys if isinstance(keys, tuple) else (keys,)
        stats = table[key_tuple]
        stats["flights"] += int(row["flights"])
        for field in grouped.columns:
            if field == "flights":
                continue
            value = row[field]
            if pd.isna(value):
                continue
            if field in SUM_FIELDS:
                stats[field] += float(value)
            else:
                stats[field] += int(value)


def update_metrics_present(metrics_present: set, chunk: pd.DataFrame) -> None:
    for column, metrics in COLUMN_TO_METRICS.items():
        if column in chunk.columns:
            metrics_present.update(metrics)


def update_overall(overall: Dict[str, float], chunk: pd.DataFrame) -> None:
    overall["flights"] += int(len(chunk))
    if "ARR_DELAY" in chunk.columns:
        overall["arr_delay_sum"] += float(chunk["ARR_DELAY"].sum(skipna=True))
        overall["arr_delay_count"] += int(chunk["ARR_DELAY"].count())
        if "arr_delay_over_15" in chunk.columns:
            overall["arr_delay_over_15"] += int(chunk["arr_delay_over_15"].sum())
    if "DEP_DELAY" in chunk.columns:
        overall["dep_delay_sum"] += float(chunk["DEP_DELAY"].sum(skipna=True))
        overall["dep_delay_count"] += int(chunk["DEP_DELAY"].count())
        if "dep_delay_over_15" in chunk.columns:
            overall["dep_delay_over_15"] += int(chunk["dep_delay_over_15"].sum())
    if "CANCELLED" in chunk.columns:
        overall["cancelled"] += int(chunk["CANCELLED"].sum())
    if "DIVERTED" in chunk.columns:
        overall["diverted"] += int(chunk["DIVERTED"].sum())
    for cause_col, field_name in DELAY_CAUSE_COLUMNS.items():
        if cause_col in chunk.columns:
            overall[field_name] += float(chunk[cause_col].sum())


def finalize_table(table: Dict[Tuple, Dict[str, float]], key_names: Iterable[str]) -> pd.DataFrame:
    records: List[Dict[str, float]] = []
    for keys, metrics in table.items():
        record = {name: value for name, value in zip(key_names, keys)}
        record.update(metrics)
        records.append(record)
    if not records:
        return pd.DataFrame(columns=list(key_names) + METRIC_FIELDS)
    return pd.DataFrame(records)


def enrich_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    result = df.copy()
    if {"arr_delay_sum", "arr_delay_count"}.issubset(result.columns):
        result["avg_arr_delay"] = safe_divide(result["arr_delay_sum"], result["arr_delay_count"])
    if {"dep_delay_sum", "dep_delay_count"}.issubset(result.columns):
        result["avg_dep_delay"] = safe_divide(result["dep_delay_sum"], result["dep_delay_count"])
    if {"arr_delay_over_15", "arr_delay_count"}.issubset(result.columns):
        result["on_time_rate"] = 1 - safe_divide(result["arr_delay_over_15"], result["arr_delay_count"])
    if {"dep_delay_over_15", "dep_delay_count"}.issubset(result.columns):
        result["departure_delay_rate"] = safe_divide(result["dep_delay_over_15"], result["dep_delay_count"])
    if {"cancelled", "flights"}.issubset(result.columns):
        result["cancellation_rate"] = safe_divide(result["cancelled"], result["flights"])
    if {"diverted", "flights"}.issubset(result.columns):
        result["diversion_rate"] = safe_divide(result["diverted"], result["flights"])
    return result


def format_markdown_table(
    df: pd.DataFrame,
    float_columns: Iterable[str] = (),
    percent_columns: Iterable[str] = (),
) -> str:
    if df.empty:
        return "_No data available._"

    float_columns = set(float_columns)
    percent_columns = set(percent_columns)
    columns = list(df.columns)
    formatted_rows: List[List[str]] = []

    numeric_cols = {col for col in columns if pd.api.types.is_numeric_dtype(df[col])}
    int_like_columns = {col for col in columns if col in COUNT_FIELDS}

    for _, row in df.iterrows():
        formatted_row: List[str] = []
        for col in columns:
            value = row[col]
            if pd.isna(value):
                formatted_row.append("")
            elif col in percent_columns:
                formatted_row.append(f"{value * 100:.1f}%")
            elif col in int_like_columns:
                formatted_row.append(f"{int(round(float(value))):,}")
            elif col in float_columns or col in numeric_cols:
                formatted_row.append(f"{float(value):,.2f}")
            else:
                formatted_row.append(str(value))
        formatted_rows.append(formatted_row)

    widths = [len(str(col)) for col in columns]
    for row in formatted_rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    header_cells = [f"{columns[idx]}".ljust(widths[idx]) for idx in range(len(columns))]
    header = "| " + " | ".join(header_cells) + " |"
    separator = "| " + " | ".join("-" * widths[idx] for idx in range(len(columns))) + " |"

    body_lines = []
    for row in formatted_rows:
        cells = []
        for idx, cell in enumerate(row):
            if columns[idx] in numeric_cols or columns[idx] in float_columns or columns[idx] in percent_columns:
                cells.append(cell.rjust(widths[idx]))
            else:
                cells.append(cell.ljust(widths[idx]))
        body_lines.append("| " + " | ".join(cells) + " |")

    return "\n".join([header, separator] + body_lines)


def summarise_cause_totals(overall: Dict[str, float]) -> pd.DataFrame:
    records = []
    for column, field in DELAY_CAUSE_COLUMNS.items():
        total_minutes = overall.get(field, 0.0)
        if total_minutes:
            records.append({"Cause": column.replace("_", " ").title(), "Delay Minutes": total_minutes})
    return pd.DataFrame(records)


def build_report(
    output_path: Path,
    monthly: pd.DataFrame,
    carrier: pd.DataFrame,
    origin: pd.DataFrame,
    route: pd.DataFrame,
    overall: Dict[str, float],
    metrics_present: set,
) -> None:
    lines: List[str] = ["# Flight Delay Dataset Analysis (2018–2024)", ""]

    if overall["flights"] == 0:
        lines.append("No flights were processed. Ensure the dataset CSV files are present in the data directory.")
    else:
        lines.append("## Overall performance")
        lines.append("")
        bullets = []
        bullets.append(f"* Flights analyzed: {overall['flights']:,}")
        if "arr_delay_sum" in metrics_present and overall.get("arr_delay_count"):
            avg_arr = overall["arr_delay_sum"] / overall["arr_delay_count"] if overall["arr_delay_count"] else float("nan")
            bullets.append(f"* Average arrival delay: {avg_arr:.2f} minutes")
        if "dep_delay_sum" in metrics_present and overall.get("dep_delay_count"):
            avg_dep = overall["dep_delay_sum"] / overall["dep_delay_count"] if overall["dep_delay_count"] else float("nan")
            bullets.append(f"* Average departure delay: {avg_dep:.2f} minutes")
        if "arr_delay_over_15" in metrics_present and overall.get("arr_delay_count"):
            on_time_rate = 1 - (overall["arr_delay_over_15"] / overall["arr_delay_count"]) if overall["arr_delay_count"] else float("nan")
            bullets.append(f"* On-time arrival rate (≤15 min): {on_time_rate * 100:.2f}%")
        if "cancelled" in metrics_present and overall.get("flights"):
            bullets.append(
                f"* Cancellation rate: {overall['cancelled'] / overall['flights'] * 100:.2f}%"
            )
        if "diverted" in metrics_present and overall.get("flights"):
            bullets.append(
                f"* Diversion rate: {overall['diverted'] / overall['flights'] * 100:.2f}%"
            )
        lines.extend(bullets)
        lines.append("")

    if not monthly.empty:
        monthly_sorted = monthly.sort_values("month")
        display_cols = ["month", "flights"]
        percent_cols = []
        float_cols = []
        if "avg_arr_delay" in monthly_sorted.columns:
            display_cols.append("avg_arr_delay")
            float_cols.append("avg_arr_delay")
        if "avg_dep_delay" in monthly_sorted.columns:
            display_cols.append("avg_dep_delay")
            float_cols.append("avg_dep_delay")
        if "on_time_rate" in monthly_sorted.columns:
            display_cols.append("on_time_rate")
            percent_cols.append("on_time_rate")
        if "cancellation_rate" in monthly_sorted.columns:
            display_cols.append("cancellation_rate")
            percent_cols.append("cancellation_rate")
        lines.append("## Monthly trend overview")
        lines.append("")
        lines.append(format_markdown_table(monthly_sorted[display_cols], float_cols, percent_cols))
        lines.append("")

    if not carrier.empty and "avg_arr_delay" in carrier.columns:
        top_carriers = carrier.sort_values("flights", ascending=False)
        top_carriers = top_carriers.head(10)
        display_cols = ["OP_CARRIER", "flights", "avg_arr_delay"]
        percent_cols = []
        float_cols = ["avg_arr_delay"]
        if "on_time_rate" in carrier.columns:
            display_cols.append("on_time_rate")
            percent_cols.append("on_time_rate")
        lines.append("## Carrier ranking (top 10 by flight volume)")
        lines.append("")
        lines.append(format_markdown_table(top_carriers[display_cols], float_cols, percent_cols))
        lines.append("")

    if not origin.empty and "avg_arr_delay" in origin.columns:
        busy_airports = origin.sort_values("flights", ascending=False).head(10)
        display_cols = ["ORIGIN", "flights", "avg_arr_delay"]
        percent_cols = []
        float_cols = ["avg_arr_delay"]
        if "on_time_rate" in origin.columns:
            display_cols.append("on_time_rate")
            percent_cols.append("on_time_rate")
        lines.append("## Origin airport performance (top 10 by departures)")
        lines.append("")
        lines.append(format_markdown_table(busy_airports[display_cols], float_cols, percent_cols))
        lines.append("")

    if not route.empty and "avg_arr_delay" in route.columns:
        top_routes = route.sort_values("flights", ascending=False).head(10)
        display_cols = ["ORIGIN", "DEST", "flights", "avg_arr_delay"]
        percent_cols = []
        float_cols = ["avg_arr_delay"]
        if "on_time_rate" in route.columns:
            display_cols.append("on_time_rate")
            percent_cols.append("on_time_rate")
        lines.append("## Busiest routes (top 10 by flights)")
        lines.append("")
        lines.append(format_markdown_table(top_routes[display_cols], float_cols, percent_cols))
        lines.append("")

    cause_totals = summarise_cause_totals(overall)
    if not cause_totals.empty:
        lines.append("## Delay minutes by cause")
        lines.append("")
        cause_totals_sorted = cause_totals.sort_values("Delay Minutes", ascending=False)
        lines.append(
            format_markdown_table(
                cause_totals_sorted,
                float_columns=["Delay Minutes"],
            )
        )
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def process_dataset(args: argparse.Namespace) -> None:
    if not args.data_dir.exists():
        raise SystemExit(
            f"Data directory {args.data_dir} does not exist. Download the Kaggle dataset before running this script."
        )

    csv_files = sorted(args.data_dir.glob("*.csv"))
    if args.limit_files is not None:
        csv_files = csv_files[: args.limit_files]

    if not csv_files:
        raise SystemExit(
            f"No CSV files found in {args.data_dir}. Ensure the Kaggle archive is extracted into this directory."
        )

    monthly_stats: Dict[Tuple, Dict[str, float]] = defaultdict(new_stats)
    carrier_stats: Dict[Tuple, Dict[str, float]] = defaultdict(new_stats)
    origin_stats: Dict[Tuple, Dict[str, float]] = defaultdict(new_stats)
    route_stats: Dict[Tuple, Dict[str, float]] = defaultdict(new_stats)
    overall_stats = new_stats()
    metrics_present: set = set()

    for path in csv_files:
        usecols, column_map = determine_available_columns(path)
        parse_dates = [column_map["FL_DATE"]] if "FL_DATE" in column_map else []
        rename_map = {actual: canonical for canonical, actual in column_map.items()}
        reader = pd.read_csv(
            path,
            usecols=usecols,
            parse_dates=parse_dates,
            chunksize=args.chunksize,
        )
        for chunk in reader:
            chunk = chunk.rename(columns=rename_map)
            chunk = preprocess_chunk(chunk)
            if chunk.empty:
                continue
            update_metrics_present(metrics_present, chunk)
            update_overall(overall_stats, chunk)

            agg_spec = build_agg_spec(chunk)
            monthly_grouped = chunk.groupby("month", observed=True).agg(**agg_spec)
            update_table(monthly_stats, monthly_grouped)

            if "OP_CARRIER" in chunk.columns:
                carrier_grouped = chunk.groupby("OP_CARRIER", observed=True).agg(**agg_spec)
                update_table(carrier_stats, carrier_grouped)
            if "ORIGIN" in chunk.columns:
                origin_grouped = chunk.groupby("ORIGIN", observed=True).agg(**agg_spec)
                update_table(origin_stats, origin_grouped)
            if {"ORIGIN", "DEST"}.issubset(chunk.columns):
                route_grouped = chunk.groupby(["ORIGIN", "DEST"], observed=True).agg(**agg_spec)
                update_table(route_stats, route_grouped)

    monthly_df = enrich_metrics(finalize_table(monthly_stats, ["month"]))
    if "month" in monthly_df.columns:
        monthly_df["month"] = monthly_df["month"].astype(str)

    carrier_df = enrich_metrics(finalize_table(carrier_stats, ["OP_CARRIER"]))
    origin_df = enrich_metrics(finalize_table(origin_stats, ["ORIGIN"]))
    route_df = enrich_metrics(finalize_table(route_stats, ["ORIGIN", "DEST"]))

    build_report(args.output, monthly_df, carrier_df, origin_df, route_df, overall_stats, metrics_present)


def main() -> None:
    args = parse_args()
    try:
        process_dataset(args)
    except Exception as exc:  # pragma: no cover - runtime error path
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
