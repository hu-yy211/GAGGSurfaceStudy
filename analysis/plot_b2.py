#!/usr/bin/env python3
"""Summarize and plot the validated B2 roughness/position response grid."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt

from b2_common import DEFAULT_CONFIG_PATH
from validate_b2 import load_grid


STATE_LABELS = {
    "all_polished": "all polished",
    "bottom_rough": "bottom rough",
    "top_rough": "top rough",
    "side_rough": "side rough",
    "bottom_polished_others_rough": "bottom polished, others rough",
    "top_polished_others_rough": "top polished, others rough",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()

    config, summaries = load_grid(args.input_dir, args.config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    sigma_values = [point.value_rad for point in config.sigmas]
    colors = ["#4778C7", "#E39C37", "#60A561", "#BC5C66", "#8D6AB8", "#4BA3A3"]

    summary_path = args.output_dir / "b2_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "surface_state",
                "position_tag",
                "source_z_mm",
                "sigma_alpha_rad",
                "generated",
                "n_pmt",
                "efficiency",
                "normalized_to_all_polished_same_position",
                "top_interactions",
                "bottom_interactions",
                "side_interactions",
            ]
        )
        for state in config.states:
            for position in config.positions:
                for sigma in config.sigmas:
                    summary = summaries[(state, position.tag, sigma.tag)]
                    reference = summaries[("all_polished", position.tag, sigma.tag)]
                    writer.writerow(
                        [
                            state,
                            position.tag,
                            position.xyz_mm[2],
                            sigma.value_rad,
                            summary.generated,
                            summary.output,
                            summary.efficiency,
                            summary.efficiency / reference.efficiency,
                            summary.top_interactions,
                            summary.bottom_interactions,
                            summary.side_interactions,
                        ]
                    )

    smoothness_path = args.output_dir / "b2_smoothness.csv"
    with smoothness_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "surface_state",
                "position_tag",
                "response_span",
                "max_adjacent_efficiency_jump",
                "predeclared_jump_limit",
            ]
        )
        for state in config.states:
            for position in config.positions:
                efficiencies = [
                    summaries[(state, position.tag, sigma.tag)].efficiency
                    for sigma in config.sigmas
                ]
                jumps = [
                    abs(right - left)
                    for left, right in zip(efficiencies, efficiencies[1:])
                ]
                writer.writerow(
                    [
                        state,
                        position.tag,
                        max(efficiencies) - min(efficiencies),
                        max(jumps),
                        config.max_adjacent_efficiency_jump,
                    ]
                )

    figure, axes = plt.subplots(1, len(config.positions), figsize=(15.0, 5.2), sharey=True)
    for axis, position in zip(axes, config.positions):
        for color, state in zip(colors, config.states):
            axis.plot(
                sigma_values,
                [
                    summaries[(state, position.tag, sigma.tag)].efficiency
                    for sigma in config.sigmas
                ],
                marker="o",
                linewidth=1.7,
                color=color,
                label=STATE_LABELS[state],
            )
        axis.set_title(f"source z = {position.xyz_mm[2]:g} mm")
        axis.set_xlabel("shared sigma_alpha (rad)")
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("N_PMT / N_generated")
    handles, labels = axes[-1].get_legend_handles_labels()
    figure.legend(handles, labels, loc="lower center", ncol=3, fontsize=8)
    figure.suptitle("B2 optical-only roughness scan (predeclared grid; not fitted)")
    figure.tight_layout(rect=(0.0, 0.13, 1.0, 0.94))
    efficiency_path = args.output_dir / "b2_sigma_scan_efficiency.png"
    figure.savefig(efficiency_path, dpi=180)
    plt.close(figure)

    figure, axes = plt.subplots(1, len(config.positions), figsize=(15.0, 5.2), sharey=True)
    for axis, position in zip(axes, config.positions):
        for color, state in zip(colors, config.states):
            values = []
            for sigma in config.sigmas:
                summary = summaries[(state, position.tag, sigma.tag)]
                reference = summaries[("all_polished", position.tag, sigma.tag)]
                values.append(summary.efficiency / reference.efficiency)
            axis.plot(
                sigma_values,
                values,
                marker="o",
                linewidth=1.7,
                color=color,
                label=STATE_LABELS[state],
            )
        axis.axhline(1.0, color="#333333", linewidth=1.0, linestyle="--")
        axis.set_title(f"source z = {position.xyz_mm[2]:g} mm")
        axis.set_xlabel("shared sigma_alpha (rad)")
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("normalized to all polished at the same position")
    handles, labels = axes[-1].get_legend_handles_labels()
    figure.legend(handles, labels, loc="lower center", ncol=3, fontsize=8)
    figure.suptitle("B2 relative optical collection (no selected sigma_alpha)")
    figure.tight_layout(rect=(0.0, 0.13, 1.0, 0.94))
    normalized_path = args.output_dir / "b2_sigma_scan_normalized.png"
    figure.savefig(normalized_path, dpi=180)
    plt.close(figure)

    print(f"[b2-plot] summary={summary_path}")
    print(f"[b2-plot] smoothness={smoothness_path}")
    print(f"[b2-plot] efficiency={efficiency_path}")
    print(f"[b2-plot] normalized={normalized_path}")
    print(
        "[b2-plot] optical_only=true selected_sigma=false "
        "experimental_order_tested=false status=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
