#!/usr/bin/env python3
"""Plot the B7.3 GAGG energy response and gated PMT-light distribution."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from b7_3_common import DEFAULT_CONFIG_PATH, load_config, load_sample


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    config = load_config(args.config)
    summary = load_sample(args.input, config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    low = config.gate_center_kev - config.gate_half_width_kev
    high = config.gate_center_kev + config.gate_half_width_kev

    summary_path = args.output_dir / "b7_3_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow([
            "events", "zero_events", "partial_events", "full_energy_events",
            "gate_low_keV", "gate_high_keV", "full_generated", "full_n_pmt",
            "n_pmt_over_n_generated", "mean_n_pmt_per_full_event",
            "mean_n_pmt_standard_error", "mean_efficiency_standard_error",
            "mean_n_generated_per_full_event",
        ])
        writer.writerow([
            len(summary.events), summary.zero_events, summary.partial_events,
            len(summary.full_energy_events), low, high, summary.full_generated,
            summary.full_output, f"{summary.full_collection_efficiency:.10f}",
            f"{summary.mean_full_output:.6f}",
            f"{summary.full_output_standard_error:.6f}",
            f"{summary.full_efficiency_standard_error:.10f}",
            f"{summary.mean_full_generated:.6f}",
        ])

    figure, axes = plt.subplots(1, 2, figsize=(12.0, 4.8))
    positive_edep = [event.edep_kev for event in summary.events if event.edep_kev > 0.0]
    axes[0].hist(positive_edep, bins=120, range=(0.0, 512.0), color="#2878B5", edgecolor="none")
    axes[0].axvspan(low, high, color="#D95F02", alpha=0.35, label=f"{low:g}–{high:g} keV gate")
    axes[0].set(xlabel="Event-total Edep in GAGG (keV)", ylabel="Events / bin", title="B7.3 deposited-energy spectrum")
    axes[0].legend()
    axes[0].grid(axis="y", alpha=0.25)

    gated_output = [event.output for event in summary.full_energy_events]
    axes[1].hist(gated_output, bins=30, color="#3A923A", edgecolor="white")
    axes[1].axvline(
        summary.mean_full_output, color="#C44E52", linewidth=2,
        label=f"mean = {summary.mean_full_output:.0f} ± {summary.full_output_standard_error:.0f} (SE)",
    )
    axes[1].set(xlabel="N_PMT per selected event", ylabel="Events / bin", title="511 keV-gated PMT optical photons")
    axes[1].legend()
    axes[1].grid(axis="y", alpha=0.25)
    figure.suptitle("2.5 mm square effective annihilation source, z = +30 mm, all polished")
    figure.tight_layout()
    figure_path = args.output_dir / "b7_3_full_energy_response.png"
    figure.savefig(figure_path, dpi=180)
    plt.close(figure)
    print(f"[b7.3-plot] wrote={summary_path}")
    print(f"[b7.3-plot] wrote={figure_path}")
    print("[b7.3-plot] status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
