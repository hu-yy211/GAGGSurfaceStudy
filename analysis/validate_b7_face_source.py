#!/usr/bin/env python3
"""Validate B7.1 uniform sampling on the 2.5 mm square source face."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def variance(values: list[float], centre: float) -> float:
    return sum((value - centre) ** 2 for value in values) / len(values)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--expect-events", type=int, default=5000)
    parser.add_argument("--face-size-mm", type=float, default=2.5)
    args = parser.parse_args()

    with args.input.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != args.expect_events:
        raise ValueError(f"expected {args.expect_events} rows, found {len(rows)}")

    xs: list[float] = []
    ys: list[float] = []
    for expected_id, row in enumerate(rows):
        if int(row["event_id"]) != expected_id:
            raise ValueError("event IDs are not contiguous")
        if row["source_particle"] != "gamma":
            raise ValueError(f"event {expected_id}: source is not gamma")
        if abs(float(row["source_energy_keV"]) - 1.0) > 1.0e-12:
            raise ValueError(f"event {expected_id}: diagnostic energy changed")
        if abs(float(row["source_z_mm"]) - 30.0) > 1.0e-12:
            raise ValueError(f"event {expected_id}: source z changed")
        xs.append(float(row["source_x_mm"]))
        ys.append(float(row["source_y_mm"]))

    half = 0.5 * args.face_size_mm
    if any(not (-half <= value <= half) for value in xs + ys):
        raise ValueError("sample outside square source face")

    mean_x, mean_y = mean(xs), mean(ys)
    variance_expected = args.face_size_mm**2 / 12.0
    variance_x = variance(xs, mean_x)
    variance_y = variance(ys, mean_y)
    covariance = mean([(x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)])
    correlation = covariance / math.sqrt(variance_x * variance_y)

    bins_per_axis = 5
    counts = [[0 for _ in range(bins_per_axis)] for _ in range(bins_per_axis)]
    for x, y in zip(xs, ys):
        x_bin = min(bins_per_axis - 1,
                    int((x + half) / args.face_size_mm * bins_per_axis))
        y_bin = min(bins_per_axis - 1,
                    int((y + half) / args.face_size_mm * bins_per_axis))
        counts[y_bin][x_bin] += 1
    expected_bin = len(xs) / (bins_per_axis * bins_per_axis)
    chi_square = sum(
        (count - expected_bin) ** 2 / expected_bin
        for row in counts for count in row
    )
    reduced_chi_square = chi_square / (bins_per_axis**2 - 1)

    checks = {
        "mean_x": abs(mean_x) < 0.03,
        "mean_y": abs(mean_y) < 0.03,
        "variance_x": abs(variance_x / variance_expected - 1.0) < 0.05,
        "variance_y": abs(variance_y / variance_expected - 1.0) < 0.05,
        "xy_correlation": abs(correlation) < 0.04,
        "edge_coverage_x": min(xs) < -1.20 and max(xs) > 1.20,
        "edge_coverage_y": min(ys) < -1.20 and max(ys) > 1.20,
        "grid_uniformity": 0.25 < reduced_chi_square < 2.0,
    }
    status = "PASS" if all(checks.values()) else "FAIL"

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "events": len(xs),
        "face_size_mm": args.face_size_mm,
        "x_range_mm": [min(xs), max(xs)],
        "y_range_mm": [min(ys), max(ys)],
        "mean_x_mm": mean_x,
        "mean_y_mm": mean_y,
        "expected_variance_mm2": variance_expected,
        "variance_x_mm2": variance_x,
        "variance_y_mm2": variance_y,
        "xy_correlation": correlation,
        "grid_reduced_chi_square": reduced_chi_square,
        "checks": checks,
        "status": status,
    }
    summary_path = args.output_dir / "face_source_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    figure, axes = plt.subplots(1, 3, figsize=(14.0, 4.6))
    axes[0].scatter(xs, ys, s=3, alpha=0.25, color="#2878B5")
    axes[0].set(xlim=(-half, half), ylim=(-half, half), aspect="equal",
                xlabel="source x (mm)", ylabel="source y (mm)",
                title="B7.1 sampled source positions")
    axes[1].hist(xs, bins=25, range=(-half, half), color="#3A86FF")
    axes[1].set(xlabel="source x (mm)", ylabel="events", title="x distribution")
    axes[2].hist(ys, bins=25, range=(-half, half), color="#6A994E")
    axes[2].set(xlabel="source y (mm)", ylabel="events", title="y distribution")
    for axis in axes:
        axis.grid(alpha=0.2)
    figure.suptitle("Uniform 2.5 mm x 2.5 mm effective annihilation-source face")
    figure.tight_layout()
    plot_path = args.output_dir / "face_source_sampling.png"
    figure.savefig(plot_path, dpi=180)
    plt.close(figure)

    print(
        f"[b7.1] events={len(xs)} x_range=[{min(xs):.6f},{max(xs):.6f}] "
        f"y_range=[{min(ys):.6f},{max(ys):.6f}]"
    )
    print(
        f"[b7.1] mean=({mean_x:.6f},{mean_y:.6f}) "
        f"variance=({variance_x:.6f},{variance_y:.6f}) "
        f"expected_variance={variance_expected:.6f} corr={correlation:.6f}"
    )
    print(f"[b7.1] grid_reduced_chi_square={reduced_chi_square:.6f}")
    print(f"[b7.1] wrote={summary_path}")
    print(f"[b7.1] wrote={plot_path}")
    print(f"[b7.1] face_source_sampling status={status}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
