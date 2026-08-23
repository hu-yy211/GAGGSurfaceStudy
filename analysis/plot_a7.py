#!/usr/bin/env python3
"""Plot the paired A7 full-energy LUT comparison."""

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from validate_a7 import FIG4_ORDER, SURFACES, load_comparison, ordering_matches


COLORS = ["#2878B5", "#D95F02", "#7A5195", "#6A994E"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--expect-events", type=int, default=100)
    args = parser.parse_args()

    summaries = load_comparison(args.input_dir, args.expect_events)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    reference = summaries["polishedvm2000air"].mean_efficiency

    summary_path = args.output_dir / "a7_fig4_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "surface",
                "primary_events",
                "full_energy_events",
                "mean_output",
                "mean_efficiency",
                "standard_error",
                "ci95_low",
                "ci95_high",
                "normalized_to_polishedvm2000air",
            ]
        )
        for surface in SURFACES:
            summary = summaries[surface]
            ci_low, ci_high = summary.ci95
            writer.writerow(
                [
                    surface,
                    summary.events,
                    len(summary.full_events),
                    f"{summary.mean_output:.10f}",
                    f"{summary.mean_efficiency:.10f}",
                    f"{summary.standard_error:.10f}",
                    f"{ci_low:.10f}",
                    f"{ci_high:.10f}",
                    f"{summary.mean_efficiency / reference:.10f}",
                ]
            )

    labels = list(SURFACES)
    means = [summaries[surface].mean_efficiency for surface in SURFACES]
    errors = [1.959963984540054 * summaries[surface].standard_error
              for surface in SURFACES]
    fig, axis = plt.subplots(figsize=(10.6, 5.8))
    bars = axis.bar(labels, means, yerr=errors, capsize=5, color=COLORS)
    axis.set_ylabel("Mean N_output / N_generated (full-energy events)")
    axis.set_title("A7 paired 662 keV LUT comparison (95% CI)")
    axis.grid(axis="y", alpha=0.25)
    axis.set_axisbelow(True)
    lower = max(0.0, min(mean - error for mean, error in zip(means, errors)) - 0.03)
    upper = max(mean + error for mean, error in zip(means, errors)) + 0.03
    axis.set_ylim(lower, upper)
    plt.setp(axis.get_xticklabels(), rotation=18, ha="right")
    for bar, value in zip(bars, means):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:.4f}",
            ha="center",
            va="bottom",
        )
    order_status = "PASS" if ordering_matches(summaries) else "FAIL"
    fig.text(
        0.5,
        0.01,
        "Fig. 4 target: " + " > ".join(FIG4_ORDER)
        + f"   |   observed status: {order_status}",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0.0, 0.04, 1.0, 1.0))
    efficiency_path = args.output_dir / "a7_full_energy_efficiency.png"
    fig.savefig(efficiency_path, dpi=180)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(10.2, 5.8))
    all_outputs = [
        event.output
        for surface in SURFACES
        for event in summaries[surface].full_events
    ]
    output_min = min(all_outputs)
    output_max = max(all_outputs)
    for surface, color in zip(SURFACES, COLORS):
        axis.hist(
            [event.output for event in summaries[surface].full_events],
            bins=18,
            range=(output_min, output_max),
            histtype="step",
            linewidth=2.0,
            color=color,
            label=surface,
        )
    axis.set_xlabel("N_output per 662 keV full-energy event")
    axis.set_ylabel("Events / bin")
    axis.set_title("A7 full-energy light-output distributions")
    axis.grid(alpha=0.25)
    axis.legend()
    fig.tight_layout()
    distribution_path = args.output_dir / "a7_full_energy_distributions.png"
    fig.savefig(distribution_path, dpi=180)
    plt.close(fig)

    print(f"[a7-plot] wrote={summary_path}")
    print(f"[a7-plot] wrote={efficiency_path}")
    print(f"[a7-plot] wrote={distribution_path}")
    print(f"[a7-plot] ordering_status={order_status}")
    print("[a7-plot] status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
