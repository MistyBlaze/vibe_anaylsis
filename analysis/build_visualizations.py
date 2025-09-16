#!/usr/bin/env python3
"""Create summary tables and charts for the flight delay dataset."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, List

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from dataset_utils import collect_csv_files
sns.set_theme(style="whitegrid")

USECOLS = [
    "FlightDate",
    "IATA_Code_Marketing_Airline",
    "Origin",
    "Dest",
    "ArrDelay",
    "ArrDel15",
    "DepDelay",
    "DepDel15",
    "Cancelled",
    "Diverted",
    "Flights",
    "CarrierDelay",
    "WeatherDelay",
    "NASDelay",
    "SecurityDelay",
    "LateAircraftDelay",
]

RENAME_MAP = {
    "IATA_Code_Marketing_Airline": "carrier",
    "Origin": "origin",
    "Dest": "dest",
    "ArrDelay": "arr_delay",
    "ArrDel15": "arr_delay_over_15",
    "DepDelay": "dep_delay",
    "DepDel15": "dep_delay_over_15",
    "Cancelled": "cancelled",
    "Diverted": "diverted",
    "Flights": "flights",
    "CarrierDelay": "carrier_delay",
    "WeatherDelay": "weather_delay",
    "NASDelay": "nas_delay",
    "SecurityDelay": "security_delay",
    "LateAircraftDelay": "late_aircraft_delay",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/flight-delay-dataset-2018-2024"),
        help="Directory containing the Kaggle CSV export.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("analysis/figures"),
        help="Directory where figures and intermediate CSVs will be written.",
    )
    parser.add_argument(
        "--image-format",
        choices=("svg", "png"),
        default="svg",
        help="Image format used when saving charts (default: svg).",
    )
    parser.add_argument(
        "--image-dpi",
        type=int,
        default=200,
        help="DPI for raster charts; ignored when --image-format=svg.",
    )
    return parser.parse_args()


def load_dataset(csv_paths: Iterable[Path]) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for path in csv_paths:
        frame = pd.read_csv(path, usecols=USECOLS, parse_dates=["FlightDate"])
        frames.append(frame)
    if not frames:
        raise ValueError("No CSV files were provided for loading")
    combined = pd.concat(frames, ignore_index=True)
    return combined.rename(columns=RENAME_MAP)


def coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    numeric_columns = [
        "arr_delay",
        "dep_delay",
        "carrier_delay",
        "weather_delay",
        "nas_delay",
        "security_delay",
        "late_aircraft_delay",
    ]
    for column in numeric_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    indicator_columns = ["arr_delay_over_15", "dep_delay_over_15", "cancelled", "diverted", "flights"]
    for column in indicator_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce").fillna(0)
    result.loc[result["flights"] == 0, "flights"] = 1
    return result


def summarise_monthly(df: pd.DataFrame) -> pd.DataFrame:
    monthly = df.groupby("month").agg(
        flights=("flights", "sum"),
        avg_arr_delay=("arr_delay", "mean"),
        avg_dep_delay=("dep_delay", "mean"),
        delayed_arrivals=("arr_delay_over_15", "sum"),
        delayed_departures=("dep_delay_over_15", "sum"),
        cancelled=("cancelled", "sum"),
    )
    monthly["on_time_rate"] = 1 - monthly["delayed_arrivals"] / monthly["flights"]
    monthly["cancellation_rate"] = monthly["cancelled"] / monthly["flights"]
    return monthly.reset_index()


def summarise_dimension(df: pd.DataFrame, group_cols: List[str]) -> pd.DataFrame:
    grouped = df.groupby(group_cols).agg(
        flights=("flights", "sum"),
        avg_arr_delay=("arr_delay", "mean"),
        delayed_arrivals=("arr_delay_over_15", "sum"),
        cancelled=("cancelled", "sum"),
    )
    grouped["on_time_rate"] = 1 - grouped["delayed_arrivals"] / grouped["flights"]
    grouped["cancellation_rate"] = grouped["cancelled"] / grouped["flights"]
    return grouped.reset_index()


def write_tables(output_dir: Path, **tables: pd.DataFrame) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(output_dir / f"{name}.csv", index=False)


def _save_chart(fig, output_dir: Path, stem: str, image_format: str, dpi: int) -> None:
    output_path = output_dir / f"{stem}.{image_format}"
    save_kwargs = {"format": image_format}
    if image_format != "svg":
        save_kwargs["dpi"] = dpi
    fig.savefig(output_path, **save_kwargs)
    plt.close(fig)


def plot_monthly_delay(
    monthly: pd.DataFrame, output_dir: Path, image_format: str, dpi: int
) -> None:
    monthly_plot = monthly.copy()
    monthly_plot["month_label"] = monthly_plot["month"].dt.strftime("%Y-%m")
    melt_df = monthly_plot.melt(
        id_vars=["month_label"],
        value_vars=["avg_arr_delay", "avg_dep_delay"],
        var_name="metric",
        value_name="minutes",
    )
    fig, ax = plt.subplots(figsize=(10, 5))
    if len(monthly_plot) > 1:
        sns.lineplot(
            data=melt_df, x="month_label", y="minutes", hue="metric", marker="o", ax=ax
        )
    else:
        sns.barplot(data=melt_df, x="month_label", y="minutes", hue="metric", ax=ax)
    ax.set_title("Average Arrival vs Departure Delay by Month")
    ax.set_xlabel("Month")
    ax.set_ylabel("Minutes")
    fig.tight_layout()
    _save_chart(fig, output_dir, "monthly_delay_trend", image_format, dpi)


def plot_carrier_delay(
    carrier: pd.DataFrame, output_dir: Path, image_format: str, dpi: int
) -> None:
    top_carriers = carrier.sort_values("flights", ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(
        data=top_carriers,
        x="avg_arr_delay",
        y="carrier",
        hue="carrier",
        legend=False,
        ax=ax,
    )
    ax.set_title("Top 10 Carriers by Flights – Average Arrival Delay")
    ax.set_xlabel("Average Arrival Delay (minutes)")
    ax.set_ylabel("Carrier")
    fig.tight_layout()
    _save_chart(fig, output_dir, "carrier_avg_delay", image_format, dpi)


def plot_origin_on_time(
    origin: pd.DataFrame, output_dir: Path, image_format: str, dpi: int
) -> None:
    top_origins = origin.sort_values("flights", ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(
        data=top_origins,
        x="on_time_rate",
        y="origin",
        hue="origin",
        legend=False,
        ax=ax,
    )
    ax.set_title("Top 10 Origin Airports – On-Time Arrival Rate")
    ax.set_xlabel("On-Time Arrival Rate")
    ax.set_ylabel("Origin Airport")
    ax.set_xlim(0, 1)
    fig.tight_layout()
    _save_chart(fig, output_dir, "origin_on_time_rate", image_format, dpi)


def plot_delay_causes(
    df: pd.DataFrame, output_dir: Path, image_format: str, dpi: int
) -> None:
    cause_df = pd.DataFrame(
        {
            "Cause": ["Late Aircraft", "Carrier", "NAS", "Weather", "Security"],
            "Delay Minutes": [
                df["late_aircraft_delay"].sum(),
                df["carrier_delay"].sum(),
                df["nas_delay"].sum(),
                df["weather_delay"].sum(),
                df["security_delay"].sum(),
            ],
        }
    ).sort_values("Delay Minutes", ascending=False)
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(
        data=cause_df,
        x="Delay Minutes",
        y="Cause",
        hue="Cause",
        legend=False,
        ax=ax,
    )
    ax.set_title("Total Delay Minutes by Cause")
    ax.set_xlabel("Delay Minutes")
    ax.set_ylabel("Cause")
    fig.tight_layout()
    _save_chart(fig, output_dir, "delay_cause_minutes", image_format, dpi)
    cause_df.to_csv(output_dir / "delay_causes.csv", index=False)


def compute_summary(df: pd.DataFrame) -> Dict[str, float]:
    total_flights = float(df["flights"].sum())
    return {
        "date_range": [
            df["FlightDate"].min().strftime("%Y-%m-%d"),
            df["FlightDate"].max().strftime("%Y-%m-%d"),
        ],
        "total_flights": int(total_flights),
        "avg_arr_delay": float(df["arr_delay"].mean()),
        "avg_dep_delay": float(df["dep_delay"].mean()),
        "on_time_rate": float(1 - df["arr_delay_over_15"].sum() / total_flights),
        "cancellation_rate": float(df["cancelled"].sum() / total_flights),
        "diversion_rate": float(df["diverted"].sum() / total_flights),
    }


def main() -> None:
    args = parse_args()
    if not args.data_dir.exists():
        raise SystemExit(f"Data directory {args.data_dir} does not exist")
    csv_files = collect_csv_files(args.data_dir)
    if not csv_files:
        raise SystemExit(
            f"No CSV files found in {args.data_dir}. Place the Kaggle CSVs or zip archive in this directory."
        )

    raw = load_dataset(csv_files)
    raw["month"] = raw["FlightDate"].dt.to_period("M").dt.to_timestamp()
    numeric = coerce_numeric(raw)

    monthly = summarise_monthly(numeric)
    carrier = summarise_dimension(numeric, ["carrier"])
    origin = summarise_dimension(numeric, ["origin"])
    route = summarise_dimension(numeric, ["origin", "dest"])

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_tables(
        args.output_dir,
        monthly_summary=monthly,
        carrier_top10=carrier.sort_values("flights", ascending=False).head(10),
        origin_top10=origin.sort_values("flights", ascending=False).head(10),
        route_top10=route.sort_values("flights", ascending=False).head(10),
    )

    plot_monthly_delay(monthly, args.output_dir, args.image_format, args.image_dpi)
    plot_carrier_delay(carrier, args.output_dir, args.image_format, args.image_dpi)
    plot_origin_on_time(origin, args.output_dir, args.image_format, args.image_dpi)
    plot_delay_causes(numeric, args.output_dir, args.image_format, args.image_dpi)

    summary = compute_summary(numeric)
    summary_path = args.output_dir / "summary_metrics.json"
    summary_series = pd.Series(summary)
    summary_path.write_text(summary_series.to_json(indent=2))


if __name__ == "__main__":
    main()
