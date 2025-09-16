#!/usr/bin/env python3
"""Render lightweight SVG charts from the aggregated flight delay summary tables."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Sequence, Tuple

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("analysis/figures"),
        help="Directory containing the precomputed CSV summary tables.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("analysis/figures"),
        help="Directory where SVG charts will be written.",
    )
    return parser.parse_args()


def _svg_header(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        "<style>text{font-family:Inter,Helvetica,Arial,sans-serif;font-size:14px;fill:#1f2933;}</style>\n"
    )


def _svg_footer() -> str:
    return "</svg>\n"


def _format_float(value: float, decimals: int = 1) -> str:
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".")


def _ticks(max_value: float, tick_count: int = 5) -> List[float]:
    if max_value <= 0:
        return [0]
    step = max_value / tick_count
    return [step * i for i in range(tick_count + 1)]


def _horizontal_bar_chart(
    labels: Sequence[str],
    values: Sequence[float],
    title: str,
    axis_label: str,
    width: int = 840,
    height: int = 520,
    margin: int = 80,
    value_suffix: str = "",
) -> str:
    if not labels:
        raise ValueError("Cannot draw chart without labels")
    max_value = max(values) if values else 0
    chart_width = width - margin * 2
    chart_height = height - margin * 2
    bar_space = chart_height / len(labels)
    bar_height = bar_space * 0.6
    svg_parts: List[str] = [
        _svg_header(width, height),
        f'<text x="{width / 2}" y="{margin / 2}" text-anchor="middle" font-size="18" font-weight="600">{title}</text>',
        f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="#cbd2d9" stroke-width="1"/>',
        f'<line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#cbd2d9" stroke-width="1"/>',
    ]

    ticks = _ticks(max_value)
    for tick in ticks:
        x = margin + (0 if max_value == 0 else chart_width * tick / max_value)
        svg_parts.append(
            f'<line x1="{x}" y1="{height - margin}" x2="{x}" y2="{height - margin + 8}" stroke="#cbd2d9" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{x}" y="{height - margin + 28}" text-anchor="middle">{_format_float(tick)}</text>'
        )

    svg_parts.append(
        f'<text x="{margin + chart_width / 2}" y="{height - margin + 55}" text-anchor="middle" font-size="13">{axis_label}</text>'
    )

    palette = ["#2563eb", "#10b981", "#f97316", "#a855f7", "#ef4444"]
    for idx, (label, value) in enumerate(zip(labels, values)):
        y = margin + idx * bar_space + (bar_space - bar_height) / 2
        bar_length = 0 if max_value == 0 else chart_width * value / max_value
        color = palette[idx % len(palette)]
        svg_parts.append(
            f'<rect x="{margin}" y="{y}" width="{bar_length}" height="{bar_height}" fill="{color}" rx="4"/>'
        )
        svg_parts.append(
            f'<text x="{margin - 10}" y="{y + bar_height / 2 + 5}" text-anchor="end" font-weight="500">{label}</text>'
        )
        svg_parts.append(
            f'<text x="{margin + bar_length + 8}" y="{y + bar_height / 2 + 5}">{_format_float(value)}{value_suffix}</text>'
        )

    svg_parts.append(_svg_footer())
    return "\n".join(svg_parts)


def _grouped_bar_chart(
    categories: Sequence[str],
    series: Sequence[Tuple[str, Sequence[float]]],
    title: str,
    axis_label: str,
    width: int = 840,
    height: int = 520,
    margin: int = 80,
    value_suffix: str = "",
) -> str:
    if not categories or not series:
        raise ValueError("Cannot draw chart without categories and data series")
    series_lengths = {len(values) for _, values in series}
    if len(series_lengths) != 1:
        raise ValueError("All data series must be the same length")

    data_length = next(iter(series_lengths))
    if data_length != len(categories):
        raise ValueError("Series length must match number of categories")

    max_value = max((max(values) for _, values in series), default=0)
    chart_width = width - margin * 2
    chart_height = height - margin * 2
    group_width = chart_width / len(categories)
    bar_width = group_width / (len(series) + 1)

    palette = ["#2563eb", "#f97316", "#10b981", "#a855f7"]
    svg_parts = [
        _svg_header(width, height),
        f'<text x="{width / 2}" y="{margin / 2}" text-anchor="middle" font-size="18" font-weight="600">{title}</text>',
        f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="#cbd2d9" stroke-width="1"/>',
        f'<line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#cbd2d9" stroke-width="1"/>',
    ]

    ticks = _ticks(max_value)
    for tick in ticks:
        y = height - margin - (0 if max_value == 0 else chart_height * tick / max_value)
        svg_parts.append(
            f'<line x1="{margin - 8}" y1="{y}" x2="{margin}" y2="{y}" stroke="#cbd2d9" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{margin - 12}" y="{y + 5}" text-anchor="end">{_format_float(tick)}</text>'
        )

    svg_parts.append(
        f'<text x="{margin - 55}" y="{margin + chart_height / 2}" transform="rotate(-90 {margin - 55},{margin + chart_height / 2})" text-anchor="middle" font-size="13">{axis_label}</text>'
    )

    for cat_idx, category in enumerate(categories):
        base_x = margin + cat_idx * group_width + (group_width - len(series) * bar_width) / 2
        svg_parts.append(
            f'<text x="{margin + cat_idx * group_width + group_width / 2}" y="{height - margin + 28}" text-anchor="middle">{category}</text>'
        )
        for series_idx, (series_label, values) in enumerate(series):
            value = values[cat_idx]
            bar_height = 0 if max_value == 0 else chart_height * value / max_value
            x = base_x + series_idx * bar_width
            y = height - margin - bar_height
            color = palette[series_idx % len(palette)]
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="4"/>'
            )
            svg_parts.append(
                f'<text x="{x + bar_width / 2}" y="{y - 6}" text-anchor="middle">{_format_float(value)}{value_suffix}</text>'
            )

    # Legend
    legend_x = width - margin - 140
    legend_y = margin
    for idx, (series_label, _) in enumerate(series):
        color = palette[idx % len(palette)]
        y = legend_y + idx * 24
        svg_parts.append(f'<rect x="{legend_x}" y="{y - 12}" width="18" height="18" fill="{color}" rx="4"/>')
        svg_parts.append(f'<text x="{legend_x + 26}" y="{y + 2}" font-size="13">{series_label}</text>')

    svg_parts.append(_svg_footer())
    return "\n".join(svg_parts)


def render_monthly_chart(monthly: pd.DataFrame, output_dir: Path) -> None:
    monthly = monthly.copy()
    monthly["month"] = pd.to_datetime(monthly["month"], errors="coerce")
    monthly["month_label"] = monthly["month"].dt.strftime("%Y-%m")
    if monthly["month_label"].isna().any():
        fallback = monthly.index.to_series().astype(str)
        monthly.loc[monthly["month_label"].isna(), "month_label"] = fallback[monthly["month_label"].isna()]
    categories = monthly["month_label"].tolist()
    series = [
        ("Avg arrival delay", monthly["avg_arr_delay"].astype(float).tolist()),
        ("Avg departure delay", monthly["avg_dep_delay"].astype(float).tolist()),
    ]
    svg = _grouped_bar_chart(
        categories,
        series,
        title="Average arrival vs. departure delay",
        axis_label="Delay (minutes)",
    )
    (output_dir / "monthly_delay_trend.svg").write_text(svg)


def render_carrier_chart(carrier: pd.DataFrame, output_dir: Path) -> None:
    top_carriers = carrier.sort_values("flights", ascending=False).head(10)
    labels = top_carriers["carrier"].tolist()
    values = top_carriers["avg_arr_delay"].astype(float).tolist()
    svg = _horizontal_bar_chart(
        labels,
        values,
        title="Top carriers by flights – avg arrival delay",
        axis_label="Average delay (minutes)",
    )
    (output_dir / "carrier_avg_delay.svg").write_text(svg)


def render_origin_chart(origin: pd.DataFrame, output_dir: Path) -> None:
    top_origins = origin.sort_values("flights", ascending=False).head(10)
    labels = top_origins["origin"].tolist()
    values = [rate * 100 for rate in top_origins["on_time_rate"].astype(float)]
    svg = _horizontal_bar_chart(
        labels,
        values,
        title="Top origin airports – on-time arrival rate",
        axis_label="On-time arrivals (%)",
        value_suffix="%",
    )
    (output_dir / "origin_on_time_rate.svg").write_text(svg)


def render_delay_cause_chart(delay_causes: pd.DataFrame, output_dir: Path) -> None:
    data = delay_causes.rename(columns=str.strip)
    labels = data["Cause"].tolist()
    values = data["Delay Minutes"].astype(float).tolist()
    svg = _horizontal_bar_chart(
        labels,
        values,
        title="Total delay minutes by cause",
        axis_label="Delay minutes",
    )
    (output_dir / "delay_cause_minutes.svg").write_text(svg)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    monthly = pd.read_csv(args.input_dir / "monthly_summary.csv")
    carrier = pd.read_csv(args.input_dir / "carrier_top10.csv")
    origin = pd.read_csv(args.input_dir / "origin_top10.csv")
    delay_causes = pd.read_csv(args.input_dir / "delay_causes.csv")

    render_monthly_chart(monthly, args.output_dir)
    render_carrier_chart(carrier, args.output_dir)
    render_origin_chart(origin, args.output_dir)
    render_delay_cause_chart(delay_causes, args.output_dir)


if __name__ == "__main__":
    main()
