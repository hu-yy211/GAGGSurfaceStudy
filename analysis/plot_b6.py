#!/usr/bin/env python3
"""Write B6 location-resolved loss tables and diagnostic figures."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from b6_common import DEFAULT_CONFIG_PATH
from validate_b6 import load_budgets, validate_budgets


LABELS = {
    "all_polished": "All polished",
    "bottom_rough": "Bottom rough",
    "top_rough": "Top rough",
    "side_rough": "Side rough",
    "bottom_polished_others_rough": "Bottom polished,\nothers rough",
    "top_polished_others_rough": "Top polished,\nothers rough",
}
COLORS = {
    "output": "#2878B5",
    "crystal_absorption": "#7A5195",
    "top_surface_absorption": "#E6A700",
    "black_surface_absorption": "#333333",
    "other": "#A7A7A7",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--b4-input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    config, budgets = load_budgets(args.input_dir, args.b4_input_dir, args.config)
    validate_budgets(config, budgets)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = args.output_dir / "b6_loss_budget.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as stream:
        fieldnames = [
            "sigma_alpha_rad", "state", "full_energy_events", "generated",
            *[f"fraction_{channel}" for channel in config.terminal_channels],
            "fraction_surface_absorption",
            *[f"per_generated_{channel}" for channel in config.face_interactions],
        ]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for sigma in config.b5.sigmas:
            for state in config.b5.b4.states:
                budget = budgets[(sigma, state)]
                row = {
                    "sigma_alpha_rad": f"{sigma:.10f}",
                    "state": state,
                    "full_energy_events": budget.full_energy_events,
                    "generated": budget.generated,
                    "fraction_surface_absorption": f"{budget.fraction('surface_absorption'):.10f}",
                }
                row.update({
                    f"fraction_{channel}": f"{budget.fraction(channel):.10f}"
                    for channel in config.terminal_channels
                })
                row.update({
                    f"per_generated_{channel}": f"{budget.fraction(channel):.10f}"
                    for channel in config.face_interactions
                })
                writer.writerow(row)

    sigma = config.comparison_sigma
    states = config.b5.b4.states
    x = list(range(len(states)))
    stack_channels = (
        "output", "crystal_absorption", "top_surface_absorption",
        "black_surface_absorption", "other",
    )
    stack_values = {channel: [] for channel in stack_channels}
    explicit = set(stack_channels[:-1])
    for state in states:
        budget = budgets[(sigma, state)]
        for channel in stack_channels[:-1]:
            stack_values[channel].append(budget.fraction(channel))
        other = sum(
            budget.fraction(channel)
            for channel in config.terminal_channels
            if channel not in explicit
        )
        stack_values["other"].append(other)
    figure, axis = plt.subplots(figsize=(12.2, 6.4))
    bottom = [0.0] * len(states)
    names = {
        "output": "PMT receiver",
        "crystal_absorption": "GAGG self-absorption",
        "top_surface_absorption": "Top ESR absorption",
        "black_surface_absorption": "Black-structure absorption",
        "other": "Other terminal outcomes",
    }
    for channel in stack_channels:
        axis.bar(x, stack_values[channel], bottom=bottom, color=COLORS[channel], label=names[channel])
        bottom = [left + right for left, right in zip(bottom, stack_values[channel])]
    axis.set_xticks(x, [LABELS[state] for state in states])
    axis.set_ylabel("Fraction of generated photons")
    axis.set_title("B6: full-energy photon terminal budget, shared sigma=0.20 rad")
    axis.set_ylim(0, 1.02)
    axis.grid(axis="y", alpha=0.25)
    axis.legend(ncol=3, loc="upper center")
    figure.tight_layout()
    budget_path = args.output_dir / "b6_terminal_budget_sigma020.png"
    figure.savefig(budget_path, dpi=180)
    plt.close(figure)

    delta_channels = (
        "output", "crystal_absorption", "top_surface_absorption",
        "black_surface_absorption", "other",
    )
    rough_states = states[1:]
    reference = budgets[(sigma, "all_polished")]
    width = 0.16
    figure, axis = plt.subplots(figsize=(12.5, 6.2))
    for channel_index, channel in enumerate(delta_channels):
        values = []
        for state in rough_states:
            budget = budgets[(sigma, state)]
            if channel == "other":
                selected = set(delta_channels[:-1])
                value = sum(
                    budget.fraction(item) - reference.fraction(item)
                    for item in config.terminal_channels
                    if item not in selected
                )
            else:
                value = budget.fraction(channel) - reference.fraction(channel)
            values.append(value)
        offset = (channel_index - (len(delta_channels) - 1) / 2) * width
        axis.bar([value + offset for value in range(len(rough_states))], values, width, color=COLORS[channel], label=names[channel])
    axis.axhline(0.0, color="#333333", linewidth=1)
    axis.set_xticks(range(len(rough_states)), [LABELS[state] for state in rough_states])
    axis.set_ylabel("Change in photon fraction vs all polished")
    axis.set_title("B6: where the collection change goes, shared sigma=0.20 rad")
    axis.grid(axis="y", alpha=0.25)
    axis.legend(ncol=3, loc="upper center")
    figure.tight_layout()
    delta_path = args.output_dir / "b6_delta_loss_channels_sigma020.png"
    figure.savefig(delta_path, dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(12.2, 6.0))
    interaction_colors = ["#E6A700", "#2878B5", "#6A994E"]
    for channel_index, channel in enumerate(config.face_interactions):
        values = [budgets[(sigma, state)].fraction(channel) for state in states]
        offset = (channel_index - 1) * 0.24
        axis.bar([value + offset for value in x], values, 0.24, color=interaction_colors[channel_index], label=channel.replace("_surface_interactions", "").title())
    axis.set_yscale("log")
    axis.set_xticks(x, [LABELS[state] for state in states])
    axis.set_ylabel("Boundary interactions per generated photon (log scale)")
    axis.set_title("B6: face interaction burden, shared sigma=0.20 rad")
    axis.grid(axis="y", alpha=0.25, which="both")
    axis.legend()
    figure.tight_layout()
    interactions_path = args.output_dir / "b6_face_interactions_sigma020.png"
    figure.savefig(interactions_path, dpi=180)
    plt.close(figure)

    print(f"[b6-plot] wrote={summary_path}")
    print(f"[b6-plot] wrote={budget_path}")
    print(f"[b6-plot] wrote={delta_path}")
    print(f"[b6-plot] wrote={interactions_path}")
    print("[b6-plot] status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
