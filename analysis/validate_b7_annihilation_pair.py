#!/usr/bin/env python3
"""Validate B7.2 same-vertex, back-to-back 511 keV gamma pairs."""

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
    return mean([(value - centre) ** 2 for value in values])


def correlation(first: list[float], second: list[float]) -> float:
    first_mean, second_mean = mean(first), mean(second)
    covariance = mean([
        (a - first_mean) * (b - second_mean)
        for a, b in zip(first, second)
    ])
    return covariance / math.sqrt(
        variance(first, first_mean) * variance(second, second_mean)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--expect-events", type=int, default=10000)
    parser.add_argument("--face-size-mm", type=float, default=2.5)
    args = parser.parse_args()

    with args.input.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != args.expect_events:
        raise ValueError(f"expected {args.expect_events} rows, found {len(rows)}")

    xs: list[float] = []
    ys: list[float] = []
    directions: list[tuple[float, float, float]] = []
    dots: list[float] = []
    maximum_antiparallel_residual = 0.0
    maximum_norm_residual = 0.0
    for expected_id, row in enumerate(rows):
        if int(row["event_id"]) != expected_id:
            raise ValueError("event IDs are not contiguous")
        if int(row["primary_vertex_count"]) != 1 or int(row["primary_count"]) != 2:
            raise ValueError(f"event {expected_id}: not two primaries at one vertex")
        if float(row["gamma1_energy_keV"]) != 511.0 or float(row["gamma2_energy_keV"]) != 511.0:
            raise ValueError(f"event {expected_id}: gamma energy is not 511 keV")
        if float(row["source_z_mm"]) != 30.0:
            raise ValueError(f"event {expected_id}: source z is not 30 mm")

        first = tuple(float(row[f"gamma1_d{axis}"]) for axis in "xyz")
        second = tuple(float(row[f"gamma2_d{axis}"]) for axis in "xyz")
        first_norm = math.sqrt(sum(value * value for value in first))
        second_norm = math.sqrt(sum(value * value for value in second))
        maximum_norm_residual = max(
            maximum_norm_residual, abs(first_norm - 1.0), abs(second_norm - 1.0)
        )
        maximum_antiparallel_residual = max(
            maximum_antiparallel_residual,
            max(abs(a + b) for a, b in zip(first, second)),
        )
        xs.append(float(row["source_x_mm"]))
        ys.append(float(row["source_y_mm"]))
        directions.append(first)
        dots.append(float(row["direction_dot"]))

    half = 0.5 * args.face_size_mm
    components = [[direction[index] for direction in directions] for index in range(3)]
    component_means = [mean(values) for values in components]
    second_moments = [mean([value * value for value in values]) for values in components]
    cosines = components[2]
    phis = [math.atan2(y, x) % (2.0 * math.pi) for x, y, _ in directions]

    phi_bins = 12
    phi_counts = [0] * phi_bins
    for phi in phis:
        phi_counts[min(phi_bins - 1, int(phi / (2.0 * math.pi) * phi_bins))] += 1
    expected_phi_count = len(phis) / phi_bins
    phi_chi_square = sum(
        (count - expected_phi_count) ** 2 / expected_phi_count
        for count in phi_counts
    )
    phi_reduced_chi_square = phi_chi_square / (phi_bins - 1)

    checks = {
        "source_face_bounds": all(-half <= value <= half for value in xs + ys),
        "source_face_means": abs(mean(xs)) < 0.03 and abs(mean(ys)) < 0.03,
        "unit_directions": maximum_norm_residual < 2.0e-11,
        "exactly_antiparallel": maximum_antiparallel_residual < 2.0e-12,
        "direction_dot": max(abs(value + 1.0) for value in dots) < 2.0e-12,
        "direction_means": all(abs(value) < 0.02 for value in component_means),
        "direction_second_moments": all(
            abs(value - 1.0 / 3.0) < 0.02 for value in second_moments
        ),
        "cos_theta_coverage": min(cosines) < -0.98 and max(cosines) > 0.98,
        "phi_uniformity": 0.25 < phi_reduced_chi_square < 2.0,
        "position_direction_independence": all(
            abs(correlation(position, component)) < 0.04
            for position in (xs, ys) for component in components
        ),
    }
    status = "PASS" if all(checks.values()) else "FAIL"

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "events": len(rows),
        "primary_vertices_per_event": 1,
        "primaries_per_event": 2,
        "gamma_energy_keV": 511.0,
        "source_position_z_mm": 30.0,
        "source_x_range_mm": [min(xs), max(xs)],
        "source_y_range_mm": [min(ys), max(ys)],
        "source_xy_mean_mm": [mean(xs), mean(ys)],
        "direction_component_means": component_means,
        "direction_second_moments": second_moments,
        "cos_theta_range": [min(cosines), max(cosines)],
        "phi_reduced_chi_square": phi_reduced_chi_square,
        "direction_dot_range": [min(dots), max(dots)],
        "maximum_unit_norm_residual": maximum_norm_residual,
        "maximum_antiparallel_component_residual": maximum_antiparallel_residual,
        "checks": checks,
        "status": status,
    }
    summary_path = args.output_dir / "annihilation_pair_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    figure, axes = plt.subplots(2, 2, figsize=(12.5, 9.0))
    axes[0, 0].scatter(xs, ys, s=2, alpha=0.2, color="#2878B5")
    axes[0, 0].set(xlim=(-half, half), ylim=(-half, half), aspect="equal",
                   xlabel="source x (mm)", ylabel="source y (mm)",
                   title="2.5 mm square source face")
    axes[0, 1].hist(cosines, bins=30, range=(-1.0, 1.0), color="#3A86FF")
    axes[0, 1].set(xlabel=r"$\cos\theta$ of gamma 1", ylabel="events",
                   title="4pi polar-angle sampling")
    axes[1, 0].hist(phis, bins=24, range=(0.0, 2.0 * math.pi), color="#6A994E")
    axes[1, 0].set(xlabel=r"$\phi$ of gamma 1 (rad)", ylabel="events",
                   title="4pi azimuth sampling")
    axes[1, 1].bar([r"$-1.000000$"], [len(dots)], color="#D95F02", width=0.5)
    axes[1, 1].set(xlabel=r"$\hat d_1\cdot\hat d_2$", ylabel="events",
                   title="Back-to-back direction check")
    for axis in axes.flat:
        axis.grid(alpha=0.2)
    figure.suptitle("B7.2 effective e+e- annihilation source: two 511 keV gammas")
    figure.tight_layout()
    plot_path = args.output_dir / "annihilation_pair_validation.png"
    figure.savefig(plot_path, dpi=180)
    plt.close(figure)

    print(
        f"[b7.2] events={len(rows)} vertices_per_event=1 primaries_per_event=2 "
        f"gamma_energy_keV=511"
    )
    print(
        f"[b7.2] direction_mean={component_means} "
        f"second_moment={second_moments}"
    )
    print(
        f"[b7.2] cos_theta_range=[{min(cosines):.6f},{max(cosines):.6f}] "
        f"phi_reduced_chi_square={phi_reduced_chi_square:.6f}"
    )
    print(
        f"[b7.2] dot_range=[{min(dots):.12f},{max(dots):.12f}] "
        f"max_antiparallel_residual={maximum_antiparallel_residual:.3e}"
    )
    print(f"[b7.2] wrote={summary_path}")
    print(f"[b7.2] wrote={plot_path}")
    print(f"[b7.2] annihilation_pair_source status={status}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
