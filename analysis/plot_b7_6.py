#!/usr/bin/env python3
"""Plot B7.6 terminal budgets, deltas and PMT-path diagnostics."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


STATES = (
    "all_polished", "bottom_rough", "top_rough",
    "top_bottom_rough", "side_rough",
)
LABELS = {
    "all_polished": "All polished",
    "bottom_rough": "Bottom rough",
    "top_rough": "Top rough",
    "top_bottom_rough": "Top + bottom rough",
    "side_rough": "Side rough",
}
COLORS = {
    "output": "#2878B5",
    "crystal_absorption": "#7A5195",
    "top_surface_absorption": "#E6A700",
    "black_surface_absorption": "#333333",
    "other": "#A7A7A7",
}


def read_rows(path: Path, expected_states=STATES) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = {row["state"]: row for row in csv.DictReader(stream)}
    if tuple(state for state in expected_states if state in rows) != expected_states:
        raise ValueError(f"B7.6 plot input lacks states: {path}")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    budgets = read_rows(args.input_dir / "b7_6_terminal_budget.csv")
    deltas = read_rows(args.input_dir / "b7_6_delta_budget.csv", STATES[1:])
    transport = read_rows(args.input_dir / "b7_6_transport_metrics.csv")
    x = list(range(len(STATES)))

    channels = ("output", "crystal_absorption", "top_surface_absorption", "black_surface_absorption", "other")
    values = {channel: [] for channel in channels}
    explicit = set(channels[:-1])
    terminal_names = [
        key.removeprefix("fraction_")
        for key in budgets["all_polished"]
        if key.startswith("fraction_")
    ]
    for state in STATES:
        for channel in channels[:-1]:
            values[channel].append(float(budgets[state][f"fraction_{channel}"]))
        values["other"].append(sum(
            float(budgets[state][f"fraction_{channel}"])
            for channel in terminal_names if channel not in explicit
        ))
    names = {
        "output": "PMT window",
        "crystal_absorption": "GAGG self-absorption",
        "top_surface_absorption": "Top/ESR surface absorption",
        "black_surface_absorption": "Black-structure absorption",
        "other": "Other outcomes",
    }
    figure, axis = plt.subplots(figsize=(11.8, 6.2))
    bottom = [0.0] * len(STATES)
    for channel in channels:
        axis.bar(x, values[channel], bottom=bottom, color=COLORS[channel], label=names[channel])
        bottom = [left + right for left, right in zip(bottom, values[channel])]
    axis.set_xticks(x, [LABELS[state] for state in STATES], rotation=8)
    axis.set_ylabel("Fraction of generated photons")
    axis.set_title("B7.6 full-energy photon terminal budget, sigma=0.70 rad")
    axis.set_ylim(0.0, 1.02)
    axis.grid(axis="y", alpha=0.25)
    axis.legend(ncol=3, loc="upper center")
    figure.tight_layout()
    budget_path = args.output_dir / "b7_6_terminal_budget.png"
    figure.savefig(budget_path, dpi=180)
    plt.close(figure)

    rough_states = STATES[1:]
    figure, axis = plt.subplots(figsize=(11.8, 6.0))
    width = 0.16
    for index, channel in enumerate(channels):
        channel_values = []
        for state in rough_states:
            if channel != "other":
                channel_values.append(float(deltas[state][f"delta_fraction_{channel}"]))
            else:
                channel_values.append(sum(
                    float(deltas[state][f"delta_fraction_{item}"])
                    for item in terminal_names if item not in explicit
                ))
        offset = (index - 2) * width
        axis.bar([item + offset for item in range(len(rough_states))], channel_values, width, color=COLORS[channel], label=names[channel])
    axis.axhline(0.0, color="#333333", linewidth=1)
    axis.set_xticks(range(len(rough_states)), [LABELS[state] for state in rough_states], rotation=8)
    axis.set_ylabel("Change in fraction versus all polished")
    axis.set_title("B7.6 where the collection change goes")
    axis.grid(axis="y", alpha=0.25)
    axis.legend(ncol=3, loc="upper center")
    figure.tight_layout()
    delta_path = args.output_dir / "b7_6_delta_terminal_budget.png"
    figure.savefig(delta_path, dpi=180)
    plt.close(figure)

    metrics = (
        ("total_path_per_generated_mm", "Total path / generated photon (mm)"),
        ("output_path_per_photon_mm", "Path / PMT photon (mm)"),
        ("output_face_interactions_per_photon", "Crystal-face hits / PMT photon"),
        ("output_incidence_angle_deg_mean", "Mean PMT incidence angle (deg)"),
    )
    figure, axes = plt.subplots(2, 2, figsize=(12.0, 8.0))
    for axis, (field, label) in zip(axes.flat, metrics):
        metric_values = [float(transport[state][field]) for state in STATES]
        bars = axis.bar(x, metric_values, color="#2878B5")
        axis.set_xticks(x, [LABELS[state] for state in STATES], rotation=18, ha="right")
        axis.set_ylabel(label)
        axis.grid(axis="y", alpha=0.25)
        axis.bar_label(bars, fmt="%.2f", padding=2, fontsize=8)
    figure.suptitle("B7.6 optical transport burden of collected photons")
    figure.tight_layout()
    transport_path = args.output_dir / "b7_6_output_transport.png"
    figure.savefig(transport_path, dpi=180)
    plt.close(figure)

    print(f"[b7.6-plot] wrote={budget_path}")
    print(f"[b7.6-plot] wrote={delta_path}")
    print(f"[b7.6-plot] wrote={transport_path}")
    print("[b7.6-plot] status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
