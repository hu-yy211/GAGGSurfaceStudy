#!/usr/bin/env python3
"""Create A4 LUT-switching comparison tables and plots."""

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from validate_a4 import SURFACES, load_summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    summaries = [
        load_summary(args.input_dir / f"{surface}.csv", surface)
        for surface in SURFACES
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = args.output_dir / "a4_surface_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "surface",
                "generated",
                "output",
                "efficiency",
                "binomial_standard_error",
                "surface_absorption",
                "crystal_absorption",
                "reflector_absorption",
                "other_absorption",
                "other_world_exit",
                "lut_interactions",
            ]
        )
        for summary in summaries:
            writer.writerow(
                [
                    summary.surface,
                    summary.generated,
                    summary.output,
                    f"{summary.efficiency:.10f}",
                    f"{summary.standard_error:.10f}",
                    summary.surface_absorption,
                    summary.crystal_absorption,
                    summary.reflector_absorption,
                    summary.other_absorption,
                    summary.other_world_exit,
                    summary.lut_interactions,
                ]
            )

    labels = [summary.surface for summary in summaries]
    efficiencies = [summary.efficiency for summary in summaries]
    errors = [summary.standard_error for summary in summaries]
    fig, axis = plt.subplots(figsize=(10.4, 5.8))
    bars = axis.bar(
        labels,
        efficiencies,
        yerr=errors,
        capsize=5,
        color=["#2878B5", "#D95F02", "#7A5195", "#6A994E"],
    )
    axis.set_ylabel("N_output / N_generated")
    axis.set_title("A4 LUT switching with fixed isotropic optical source")
    axis.grid(axis="y", alpha=0.25)
    axis.set_axisbelow(True)
    axis.set_ylim(0.0, max(efficiencies) * 1.22)
    plt.setp(axis.get_xticklabels(), rotation=18, ha="right")
    for bar, value in zip(bars, efficiencies):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:.4f}",
            ha="center",
            va="bottom",
        )
    fig.text(
        0.5,
        0.01,
        "Functional A4 comparison only; the Fig. 4 ordering criterion starts at A7.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0.0, 0.04, 1.0, 1.0))
    efficiency_path = args.output_dir / "a4_surface_efficiency.png"
    fig.savefig(efficiency_path, dpi=180)
    plt.close(fig)

    categories = [
        ("Output", [summary.output for summary in summaries], "#2878B5"),
        (
            "GAGG bulk absorption",
            [summary.crystal_absorption for summary in summaries],
            "#D95F02",
        ),
        (
            "Surface absorption",
            [summary.surface_absorption for summary in summaries],
            "#7A5195",
        ),
        (
            "Other terminal",
            [
                summary.reflector_absorption
                + summary.other_absorption
                + summary.other_world_exit
                for summary in summaries
            ],
            "#777777",
        ),
    ]
    fig, axis = plt.subplots(figsize=(10.4, 5.8))
    bottom = [0.0] * len(summaries)
    for label, values, color in categories:
        fractions = [
            value / summary.generated
            for value, summary in zip(values, summaries)
        ]
        axis.bar(labels, fractions, bottom=bottom, label=label, color=color)
        bottom = [left + right for left, right in zip(bottom, fractions)]
    axis.set_ylabel("Fraction of generated photons")
    axis.set_title("A4 photon-accounting breakdown")
    axis.set_ylim(0.0, 1.0)
    axis.grid(axis="y", alpha=0.25)
    axis.set_axisbelow(True)
    axis.legend(loc="upper right")
    plt.setp(axis.get_xticklabels(), rotation=18, ha="right")
    fig.tight_layout()
    outcomes_path = args.output_dir / "a4_terminal_outcomes.png"
    fig.savefig(outcomes_path, dpi=180)
    plt.close(fig)

    print(f"[a4-plot] wrote={summary_path}")
    print(f"[a4-plot] wrote={efficiency_path}")
    print(f"[a4-plot] wrote={outcomes_path}")
    print("[a4-plot] status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
