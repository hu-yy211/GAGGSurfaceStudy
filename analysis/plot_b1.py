#!/usr/bin/env python3
"""Create B1 optical-only surface-switching diagnostic plots."""

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt

from validate_b1 import ROUGH_FACES, STATES, load_comparison


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--expect-events", type=int, default=50)
    parser.add_argument("--photons-per-event", type=int, default=100)
    parser.add_argument("--sigma-alpha", type=float, default=0.20)
    args = parser.parse_args()

    summaries = load_comparison(
        args.input_dir,
        args.expect_events,
        args.photons_per_event,
        args.sigma_alpha,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    reference = summaries["all_polished"].efficiency
    labels = [state.replace("_", "\n") for state in STATES]
    colors = ["#4778C7", "#E39C37", "#60A561", "#BC5C66", "#8D6AB8", "#4BA3A3"]

    summary_path = args.output_dir / "b1_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "surface_state",
                "rough_faces",
                "sigma_alpha_rad",
                "generated",
                "n_pmt",
                "efficiency",
                "normalized_to_all_polished",
                "top_interactions",
                "bottom_interactions",
                "side_interactions",
            ]
        )
        for state in STATES:
            summary = summaries[state]
            writer.writerow(
                [
                    state,
                    "+".join(ROUGH_FACES[state]) or "none",
                    args.sigma_alpha,
                    summary.generated,
                    summary.output,
                    summary.efficiency,
                    summary.efficiency / reference,
                    summary.top_interactions,
                    summary.bottom_interactions,
                    summary.side_interactions,
                ]
            )

    figure, axis = plt.subplots(figsize=(10.5, 5.8))
    normalized = [
        summaries[state].efficiency / reference for state in STATES
    ]
    bars = axis.bar(range(len(STATES)), normalized, color=colors)
    axis.axhline(1.0, color="#333333", linewidth=1.0, linestyle="--")
    axis.set_xticks(range(len(STATES)), labels, fontsize=8)
    axis.set_ylabel("N_PMT/N_generated, normalized to all polished")
    axis.set_title(
        f"B1 optical-only switching diagnostic (shared sigma_alpha="
        f"{args.sigma_alpha:.2f} rad; not fitted)"
    )
    axis.set_ylim(0.0, max(normalized) * 1.18)
    axis.grid(axis="y", alpha=0.25)
    for bar, value in zip(bars, normalized):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.3f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    figure.tight_layout()
    efficiency_path = args.output_dir / "b1_collection_efficiency.png"
    figure.savefig(efficiency_path, dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(10.5, 5.8))
    generated = summaries["all_polished"].generated
    top = [summaries[state].top_interactions / generated for state in STATES]
    bottom = [
        summaries[state].bottom_interactions / generated for state in STATES
    ]
    side = [
        summaries[state].side_interactions / generated for state in STATES
    ]
    axis.bar(range(len(STATES)), top, label="top", color="#6B8FD6")
    axis.bar(
        range(len(STATES)),
        bottom,
        bottom=top,
        label="bottom",
        color="#E2A44F",
    )
    axis.bar(
        range(len(STATES)),
        side,
        bottom=[a + b for a, b in zip(top, bottom)],
        label="side",
        color="#68AA75",
    )
    axis.set_xticks(range(len(STATES)), labels, fontsize=8)
    axis.set_ylabel("Boundary interactions per generated photon")
    axis.set_title("B1 independent face-counter diagnostics")
    axis.legend()
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    interactions_path = args.output_dir / "b1_face_interactions.png"
    figure.savefig(interactions_path, dpi=180)
    plt.close(figure)

    print(f"[b1-plot] summary={summary_path}")
    print(f"[b1-plot] efficiency={efficiency_path}")
    print(f"[b1-plot] interactions={interactions_path}")
    print("[b1-plot] experimental_order_tested=false status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
