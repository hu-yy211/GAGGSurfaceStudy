#!/usr/bin/env python3
"""Plot B3 energy deposition and scintillation/collection diagnostics."""

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from b3_common import DEFAULT_CONFIG_PATH, load_config, load_gamma_sample


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    config = load_config(args.config)
    summary = load_gamma_sample(args.input, config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    edep = [event.edep_kev for event in summary.events]
    generated = [event.generated for event in summary.events]

    summary_path = args.output_dir / "b3_gamma_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow([
            "events", "zero_edep_events", "partial_energy_events",
            "full_energy_events", "total_yield_photons_per_MeV",
            "full_yield_photons_per_MeV", "full_collection_efficiency",
        ])
        writer.writerow([
            len(summary.events), summary.zero_edep_events,
            summary.partial_energy_events, summary.full_energy_events,
            f"{summary.total_yield_per_mev:.10f}",
            f"{summary.full_energy_yield_per_mev:.10f}",
            f"{summary.full_energy_collection_efficiency:.10f}",
        ])

    figure, axis = plt.subplots(figsize=(8.6, 5.4))
    axis.hist(edep, bins=34, range=(-0.5, 511.5), color="#2878B5", edgecolor="white")
    low = config.gamma_energy_kev - config.full_energy_half_width_kev
    high = config.gamma_energy_kev + config.full_energy_half_width_kev
    axis.axvspan(low, high, color="#D95F02", alpha=0.25, label="Full-energy gate")
    axis.set(xlabel="Energy deposited in GAGG (keV)", ylabel="Events / bin", title="B3: 511 keV gamma energy deposition")
    axis.grid(axis="y", alpha=0.25)
    axis.legend()
    axis.text(0.02, 0.95, f"zero: {summary.zero_edep_events}\npartial: {summary.partial_energy_events}\nfull: {summary.full_energy_events}", transform=axis.transAxes, va="top", bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85})
    figure.tight_layout()
    spectrum_path = args.output_dir / "b3_energy_deposition.png"
    figure.savefig(spectrum_path, dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(8.6, 5.4))
    axis.plot([0, config.gamma_energy_kev], [0, config.gamma_energy_kev * config.expected_yield_per_mev / 1000.0], color="#D95F02", linewidth=2, label="54000 photons/MeV")
    axis.scatter(edep, generated, color="#2878B5", s=28, alpha=0.72, label="Geant4 events")
    axis.set(xlabel="Energy deposited in GAGG (keV)", ylabel="Generated scintillation photons", title="B3: scintillation yield validation")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    yield_path = args.output_dir / "b3_scintillation_yield.png"
    figure.savefig(yield_path, dpi=180)
    plt.close(figure)

    print(f"[b3-plot] wrote={summary_path}")
    print(f"[b3-plot] wrote={spectrum_path}")
    print(f"[b3-plot] wrote={yield_path}")
    print("[b3-plot] status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
