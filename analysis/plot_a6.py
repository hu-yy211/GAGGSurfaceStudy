#!/usr/bin/env python3
"""Create A6 gamma energy-deposition and light-yield plots."""

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from validate_a6 import load_gamma_sample


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    summary = load_gamma_sample(args.input)
    rows = load_rows(args.input)
    edep = [float(row["edep_keV"]) for row in rows]
    generated = [int(row["generated"]) for row in rows]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = args.output_dir / "a6_gamma_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "events",
                "zero_edep_events",
                "partial_energy_events",
                "full_energy_events",
                "total_edep_keV",
                "total_generated",
                "total_yield_photons_per_MeV",
                "full_edep_keV",
                "full_generated",
                "full_energy_yield_photons_per_MeV",
            ]
        )
        writer.writerow(
            [
                summary.events,
                summary.zero_edep_events,
                summary.partial_energy_events,
                summary.full_energy_events,
                f"{summary.total_edep_kev:.10f}",
                summary.total_generated,
                f"{summary.total_yield_per_mev:.10f}",
                f"{summary.full_edep_kev:.10f}",
                summary.full_generated,
                f"{summary.full_energy_yield_per_mev:.10f}",
            ]
        )

    fig, axis = plt.subplots(figsize=(8.6, 5.4))
    axis.hist(edep, bins=34, range=(-0.5, 662.5), color="#2878B5",
              edgecolor="white", linewidth=0.6)
    axis.axvspan(661.5, 662.5, color="#D95F02", alpha=0.23,
                 label="Full-energy gate")
    axis.axvline(662.0, color="#D95F02", linestyle="--", linewidth=1.8)
    axis.set_xlabel("Energy deposited in GAGG (keV)")
    axis.set_ylabel("Events / bin")
    axis.set_title("A6: 662 keV gamma energy deposition")
    axis.grid(axis="y", alpha=0.25)
    axis.legend()
    axis.text(
        0.02,
        0.95,
        f"zero: {summary.zero_edep_events}\n"
        f"partial: {summary.partial_energy_events}\n"
        f"full: {summary.full_energy_events}",
        transform=axis.transAxes,
        va="top",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85},
    )
    fig.tight_layout()
    spectrum_path = args.output_dir / "a6_energy_deposition.png"
    fig.savefig(spectrum_path, dpi=180)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(8.6, 5.4))
    expected_x = [0.0, 662.0]
    expected_y = [0.0, 54.0 * 662.0]
    axis.plot(expected_x, expected_y, color="#D95F02", linewidth=2.0,
              label="54000 photons/MeV")
    axis.scatter(edep, generated, color="#2878B5", s=28, alpha=0.72,
                 label="Geant4 events")
    axis.set_xlabel("Energy deposited in GAGG (keV)")
    axis.set_ylabel("Generated scintillation photons")
    axis.set_title("A6 gamma-event scintillation yield")
    axis.grid(alpha=0.25)
    axis.legend()
    fig.tight_layout()
    yield_path = args.output_dir / "a6_gamma_light_yield.png"
    fig.savefig(yield_path, dpi=180)
    plt.close(fig)

    print(f"[a6-plot] wrote={summary_path}")
    print(f"[a6-plot] wrote={spectrum_path}")
    print(f"[a6-plot] wrote={yield_path}")
    print("[a6-plot] status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
