#!/usr/bin/env python3
"""Validate and plot the Na-22 positron-annihilation vertex audit."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def one_value(rows: list[dict[str, str]], key: str) -> float:
    values = {float(row[key]) for row in rows}
    if len(values) != 1:
        raise ValueError(f"inconsistent {key}: {sorted(values)}")
    return values.pop()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vertices", required=True, type=Path)
    parser.add_argument("--fates", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--expect-events", type=int, default=100000)
    args = parser.parse_args()

    vertices = load_rows(args.vertices)
    fates = load_rows(args.fates)
    if not vertices:
        raise ValueError("annihilation vertex CSV is empty")

    vertex_keys = [
        (int(row["event_id"]), int(row["parent_positron_track_id"]))
        for row in vertices
    ]
    if len(vertex_keys) != len(set(vertex_keys)):
        raise ValueError("duplicate event/parent-track annihilation records")
    fate_keys = [
        (int(row["event_id"]), int(row["positron_track_id"]))
        for row in fates
    ]
    if len(fate_keys) != len(set(fate_keys)):
        raise ValueError("duplicate positron fate records")
    if any(int(row["event_id"]) >= args.expect_events for row in vertices + fates):
        raise ValueError("event ID outside requested run")

    source_x = one_value(vertices, "source_x_mm")
    source_y = one_value(vertices, "source_y_mm")
    source_z = one_value(vertices, "source_z_mm")
    gagg_z_min = one_value(vertices, "gagg_z_min_mm")
    gagg_z_max = one_value(vertices, "gagg_z_max_mm")
    if gagg_z_min >= gagg_z_max:
        raise ValueError("invalid runtime GAGG z range")

    xs = [float(row["annihilation_x_mm"]) for row in vertices]
    zs = [float(row["annihilation_z_mm"]) for row in vertices]
    distances = [float(row["distance_from_Na22_source_mm"]) for row in vertices]
    energies = [
        float(row["positron_energy_before_annihilation_keV"])
        for row in vertices
    ]
    gamma_counts = [int(row["annihilation_gamma_count"]) for row in vertices]
    exact_volumes = Counter(row["annihilation_volume"] for row in vertices)
    categories = Counter(
        "World / vacuum" if row["annihilation_volume"] == "World"
        else "GAGG" if row["annihilation_volume"] == "GAGG"
        else "Other detector material"
        for row in vertices
    )
    fates_counter = Counter(row["fate"] for row in fates)
    annihilated_fate_keys = {
        (int(row["event_id"]), int(row["positron_track_id"]))
        for row in fates if row["fate"] == "annihilated"
    }
    if annihilated_fate_keys != set(vertex_keys):
        raise ValueError("annihilation vertex and positron fate records disagree")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(figsize=(10.5, 5.8))
    axis.hist(zs, bins=120, color="#2878B5", alpha=0.85)
    axis.axvspan(gagg_z_min, gagg_z_max, color="#F2C14E", alpha=0.25,
                 label=f"GAGG z=[{gagg_z_min:g}, {gagg_z_max:g}] mm")
    axis.axvline(source_z, color="#D62828", linestyle="--",
                 label=f"Na-22 source z={source_z:g} mm")
    axis.axvline(gagg_z_max, color="#E09F3E", linestyle=":",
                 label=f"GAGG entrance z={gagg_z_max:g} mm")
    axis.set_xlabel("Annihilation z (mm)")
    axis.set_ylabel("Unique positron annihilations")
    axis.set_title("Na-22 positron annihilation vertices: z distribution")
    axis.grid(alpha=0.2)
    axis.legend()
    figure.tight_layout()
    z_plot = args.output_dir / "annihilation_z_histogram.png"
    figure.savefig(z_plot, dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(10.5, 5.8))
    axis.hist(distances, bins=120, color="#3A86FF", alpha=0.85)
    axis.axvline(1.0, color="#D62828", linestyle="--",
                 label="1 mm from Na-22 source")
    axis.set_xlabel("Distance from Na-22 source (mm)")
    axis.set_ylabel("Unique positron annihilations")
    axis.set_title(
        f"Annihilation distance from source ({source_x:g}, {source_y:g}, {source_z:g}) mm"
    )
    axis.grid(alpha=0.2)
    axis.legend()
    figure.tight_layout()
    distance_plot = args.output_dir / "annihilation_distance_histogram.png"
    figure.savefig(distance_plot, dpi=180)
    plt.close(figure)

    volume_names, volume_counts = zip(*exact_volumes.most_common())
    figure_height = max(4.8, 0.55 * len(volume_names) + 1.8)
    figure, axis = plt.subplots(figsize=(11.0, figure_height))
    axis.barh(volume_names[::-1], volume_counts[::-1], color="#6A994E")
    axis.set_xlabel("Unique positron annihilations")
    axis.set_title("Annihilation physical-volume counts")
    axis.grid(axis="x", alpha=0.2)
    for index, count in enumerate(volume_counts[::-1]):
        axis.text(count, index, f" {count}", va="center")
    figure.tight_layout()
    volume_plot = args.output_dir / "annihilation_volume_counts.png"
    figure.savefig(volume_plot, dpi=180)
    plt.close(figure)

    scatter_plot = args.output_dir / "annihilation_xz_scatter.png"
    scatter_written = len(vertices) >= 20
    if scatter_written:
        stride = max(1, len(vertices) // 50000)
        figure, axis = plt.subplots(figsize=(10.5, 7.0))
        axis.scatter(xs[::stride], zs[::stride], s=4, alpha=0.35,
                     color="#4361EE", rasterized=True)
        axis.axhspan(gagg_z_min, gagg_z_max, color="#F2C14E", alpha=0.18,
                     label=f"GAGG z=[{gagg_z_min:g}, {gagg_z_max:g}] mm")
        axis.axhline(gagg_z_max, color="#E09F3E", linestyle=":",
                     label=f"GAGG entrance z={gagg_z_max:g} mm")
        axis.scatter([source_x], [source_z], marker="*", s=160,
                     color="#D62828", label=f"Na-22 source z={source_z:g} mm")
        axis.set_xlabel("Annihilation x (mm)")
        axis.set_ylabel("Annihilation z (mm)")
        axis.set_title("Unique positron annihilation vertices: x-z projection")
        axis.grid(alpha=0.2)
        axis.legend()
        figure.tight_layout()
        figure.savefig(scatter_plot, dpi=180)
        plt.close(figure)

    near_source = sum(distance < 1.0 for distance in distances)
    summary = {
        "requested_events": args.expect_events,
        "positrons_created": len(fates),
        "unique_annihilation_vertices": len(vertices),
        "annihilation_gamma_count_total": sum(gamma_counts),
        "annihilation_gamma_multiplicity": dict(sorted(Counter(gamma_counts).items())),
        "annihilations_within_1mm_of_source": near_source,
        "annihilation_categories": dict(categories),
        "annihilation_exact_volumes": dict(exact_volumes.most_common()),
        "positron_fates": dict(fates_counter),
        "source_position_mm": [source_x, source_y, source_z],
        "gagg_z_range_mm": [gagg_z_min, gagg_z_max],
        "positron_energy_before_annihilation_keV": {
            "minimum": min(energies),
            "maximum": max(energies),
            "nonzero_count": sum(energy > 1.0e-9 for energy in energies),
        },
        "scatter_written": scatter_written,
        "status": "PASS" if fates_counter.get("unresolved", 0) == 0 else "FAIL",
    }
    summary_path = args.output_dir / "annihilation_audit_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"[annihilation-plot] positrons_created={len(fates)}")
    print(f"[annihilation-plot] vertices={len(vertices)} near_source_1mm={near_source}")
    print(f"[annihilation-plot] categories={dict(categories)}")
    print(f"[annihilation-plot] fates={dict(fates_counter)}")
    print(f"[annihilation-plot] source_z_mm={source_z} gagg_z_mm=[{gagg_z_min},{gagg_z_max}]")
    print(f"[annihilation-plot] wrote={summary_path}")
    print(f"[annihilation-plot] status={summary['status']}")
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
