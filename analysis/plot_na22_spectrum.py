#!/usr/bin/env python3
"""Build a one-entry-per-event Na-22 GAGG deposited-energy histogram."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


FEATURES_KEV = {
    "511 photopeak": 511.0,
    "511 Compton edge": 340.7,
    "1274.5 photopeak": 1274.5,
    "1274.5 Compton edge": 1061.7,
    "511+511": 1022.0,
    "511+1274.5": 1785.5,
    "511+511+1274.5": 2296.5,
}


def window_count(values: list[float], centre: float, half_width: float) -> int:
    return sum(abs(value - centre) <= half_width for value in values)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--expect-events", type=int, default=100000)
    args = parser.parse_args()

    with args.input.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != args.expect_events:
        raise ValueError(f"expected {args.expect_events} events, found {len(rows)}")

    edep: list[float] = []
    optical_columns = (
        "scintillation", "generated", "output", "crystal_absorption",
        "reflector_absorption", "other_absorption", "surface_absorption",
        "other_world_exit", "lut_interactions", "unclassified",
    )
    for expected_id, row in enumerate(rows):
        if int(row["event_id"]) != expected_id:
            raise ValueError("event IDs are not contiguous")
        if row["source_particle"] != "na22":
            raise ValueError(f"event {expected_id}: primary is not na22")
        if abs(float(row["source_energy_keV"])) > 1.0e-12:
            raise ValueError(f"event {expected_id}: Na22 ion is not stationary")
        position = tuple(float(row[key]) for key in
                         ("source_x_mm", "source_y_mm", "source_z_mm"))
        if position != (0.0, 0.0, 30.0):
            raise ValueError(f"event {expected_id}: source position={position}")
        if any(int(row[key]) != 0 for key in optical_columns):
            raise ValueError(f"event {expected_id}: optical accounting is nonzero")
        value = float(row["edep_keV"])
        if value < 0.0:
            raise ValueError(f"event {expected_id}: negative Edep")
        edep.append(value)

    bin_count = 2500
    low, high = 0.0, 2500.0
    width = (high - low) / bin_count
    histogram = [0] * bin_count
    overflow = 0
    for value in edep:
        if low <= value < high:
            histogram[int((value - low) / width)] += 1
        elif value >= high:
            overflow += 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    histogram_path = args.output_dir / "edep_gagg_histogram.csv"
    with histogram_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["bin_low_keV", "bin_high_keV", "bin_center_keV", "events"])
        for index, count in enumerate(histogram):
            bin_low = low + index * width
            writer.writerow([bin_low, bin_low + width, bin_low + 0.5 * width, count])

    nonzero = [value for value in edep if value > 0.0]
    peak_windows = {
        label: window_count(nonzero, energy, 2.0)
        for label, energy in FEATURES_KEV.items()
        if "photopeak" in label or "+" in label
    }
    edge_bands = {}
    for label, energy in FEATURES_KEV.items():
        if "edge" not in label:
            continue
        edge_bands[label] = {
            "below_20keV": sum(energy - 20.0 <= value < energy for value in nonzero),
            "above_20keV": sum(energy < value <= energy + 20.0 for value in nonzero),
        }

    summary = {
        "events": len(edep),
        "nonzero_edep_events": len(nonzero),
        "zero_edep_events": len(edep) - len(nonzero),
        "histogram_range_keV": [low, high],
        "histogram_bins": bin_count,
        "overflow_events": overflow,
        "maximum_edep_keV": max(edep),
        "peak_window_half_width_keV": 2.0,
        "peak_window_counts": peak_windows,
        "compton_edge_band_counts": edge_bands,
        "optical_physics_expected": "off",
    }
    summary_path = args.output_dir / "na22_spectrum_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    centres = [low + (index + 0.5) * width for index in range(bin_count)]
    plot_counts = histogram.copy()
    plot_counts[0] = 0  # omit zero-deposit events from the visible spectrum
    figure, axis = plt.subplots(figsize=(13.0, 6.5))
    axis.step(centres, plot_counts, where="mid", color="#2878B5", linewidth=1.0)
    axis.set_yscale("log")
    axis.set_xlim(low, high)
    positive_counts = [count for count in plot_counts if count > 0]
    axis.set_ylim(0.8, max(positive_counts) * 2.0 if positive_counts else 2.0)
    for label, energy in FEATURES_KEV.items():
        edge = "edge" in label
        axis.axvline(
            energy, color="#D95F02" if not edge else "#6A994E",
            linestyle="--" if not edge else ":", linewidth=1.0,
        )
        axis.text(
            energy + 8.0, axis.get_ylim()[1] / (1.8 if not edge else 3.0),
            label, rotation=90, va="top", fontsize=8,
            color="#D95F02" if not edge else "#4F772D",
        )
    axis.set_xlabel("Event-level total Edep in GAGG (keV)")
    axis.set_ylabel("Events per 1 keV bin")
    axis.set_title(
        "Geant4 Na-22 decay: GAGG event-level deposited-energy spectrum\n"
        "100,000 stationary Na-22 ions, source 20 mm from +z crystal face; optical off"
    )
    axis.grid(alpha=0.2)
    figure.tight_layout()
    plot_path = args.output_dir / "edep_gagg_spectrum.png"
    figure.savefig(plot_path, dpi=180)
    plt.close(figure)

    print(f"[na22-spectrum] events={len(edep)} nonzero={len(nonzero)} overflow={overflow}")
    for label, count in peak_windows.items():
        print(f"[na22-spectrum] window={label!r} count={count}")
    for label, counts in edge_bands.items():
        print(
            f"[na22-spectrum] edge={label!r} below={counts['below_20keV']} "
            f"above={counts['above_20keV']}"
        )
    print(f"[na22-spectrum] wrote={histogram_path}")
    print(f"[na22-spectrum] wrote={summary_path}")
    print(f"[na22-spectrum] wrote={plot_path}")
    print("[na22-spectrum] event_level=true optical=off status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
