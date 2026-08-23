#!/usr/bin/env python3
"""Create A5 scintillation-linearity and timing-control plots."""

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from validate_a5 import load_summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    linear = [
        load_summary(args.input_dir / f"energy_{energy}kev.csv", float(energy))
        for energy in (10, 20, 40)
    ]
    slow = load_summary(args.input_dir / "energy_20kev_slow.csv", 20.0)
    fast = linear[1]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = args.output_dir / "a5_scintillation_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "run",
                "energy_keV",
                "events",
                "edep_keV",
                "generated",
                "yield_photons_per_MeV",
                "output",
                "output_efficiency",
                "lut_interactions",
            ]
        )
        for label, summary in [
            ("fast_10keV", linear[0]),
            ("fast_20keV", fast),
            ("fast_40keV", linear[2]),
            ("slow_20keV", slow),
        ]:
            writer.writerow(
                [
                    label,
                    summary.energy_kev,
                    summary.events,
                    f"{summary.edep_kev:.10f}",
                    summary.generated,
                    f"{summary.yield_per_mev:.10f}",
                    summary.output,
                    f"{summary.output_efficiency:.10f}",
                    summary.lut_interactions,
                ]
            )

    energies = [item.edep_kev / item.events for item in linear]
    generated = [item.generated / item.events for item in linear]
    expected = [54.0 * energy for energy in energies]
    fig, axis = plt.subplots(figsize=(8.4, 5.4))
    axis.plot(energies, expected, color="#D95F02", linewidth=2.2,
              label="54000 photons/MeV")
    axis.scatter(energies, generated, color="#2878B5", s=80, zorder=3,
                 label="Geant4 scintillation")
    for x_value, y_value in zip(energies, generated):
        axis.annotate(
            f"({x_value:g}, {y_value:g})",
            (x_value, y_value),
            xytext=(7, -14),
            textcoords="offset points",
        )
    axis.set_xlabel("Energy deposited per event (keV)")
    axis.set_ylabel("Scintillation photons per event")
    axis.set_title("A5 scintillation-yield linearity")
    axis.grid(alpha=0.25)
    axis.legend()
    fig.tight_layout()
    linearity_path = args.output_dir / "a5_scintillation_linearity.png"
    fig.savefig(linearity_path, dpi=180)
    plt.close(fig)

    labels = ["62.53 ns", "190.89 ns"]
    yields = [fast.yield_per_mev, slow.yield_per_mev]
    fig, axis = plt.subplots(figsize=(7.4, 5.2))
    bars = axis.bar(labels, yields, color=["#2878B5", "#7A5195"], width=0.58)
    axis.axhline(54000.0, color="#D95F02", linestyle="--",
                 label="Specified yield")
    axis.set_ylabel("Generated photons / MeV deposited")
    axis.set_title("A5 integrated-yield timing control")
    axis.set_ylim(53980.0, 54008.0)
    axis.grid(axis="y", alpha=0.25)
    axis.legend(loc="lower left")
    for bar, value in zip(bars, yields):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:.1f}",
            ha="center",
            va="bottom",
        )
    fig.tight_layout()
    timing_path = args.output_dir / "a5_timing_control.png"
    fig.savefig(timing_path, dpi=180)
    plt.close(fig)

    print(f"[a5-plot] wrote={summary_path}")
    print(f"[a5-plot] wrote={linearity_path}")
    print(f"[a5-plot] wrote={timing_path}")
    print("[a5-plot] status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
