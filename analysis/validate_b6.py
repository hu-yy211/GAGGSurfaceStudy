#!/usr/bin/env python3
"""Validate B6 location-resolved loss budgets and report their drivers."""

from __future__ import annotations

import argparse
from pathlib import Path

from b6_common import DEFAULT_CONFIG_PATH, load_config, make_budget
from validate_b5 import load_grid, validate_grid


def load_budgets(input_dir: Path, b4_dir: Path, config_path: Path):
    config = load_config(config_path)
    b5, grid = load_grid(input_dir, b4_dir, config.b5.path)
    validate_grid(b5, grid)
    budgets = {
        (sigma, state): make_budget(config, sigma, state, grid[(sigma, state)].events)
        for sigma in b5.sigmas
        for state in b5.b4.states
    }
    return config, budgets


def validate_budgets(config, budgets):
    for key, budget in budgets.items():
        counts = budget.counts
        if config.require_surface_subtotal:
            surface_subtotal = sum(counts[channel] for channel in config.surface_locations)
            if surface_subtotal != counts["surface_absorption"]:
                raise ValueError(f"B6 surface subtotal failed at {key}")
        if config.require_terminal_balance:
            terminal_total = sum(counts[channel] for channel in config.terminal_channels)
            if terminal_total != budget.generated:
                raise ValueError(
                    f"B6 terminal balance failed at {key}: {terminal_total}/{budget.generated}"
                )
        if config.require_top_black_nonzero and (
            counts["top_surface_absorption"] <= 0
            or counts["black_surface_absorption"] <= 0
        ):
            raise ValueError(f"B6 did not exercise top/black absorption at {key}")
        if config.require_reflector_zero and counts["reflector_absorption"] != 0:
            raise ValueError(f"Stage A reflector absorption appeared at {key}")

    balance_rows = []
    for sigma in config.b5.sigmas:
        reference = budgets[(sigma, "all_polished")]
        for state in config.b5.b4.states[1:]:
            budget = budgets[(sigma, state)]
            delta_output = budget.counts["output"] - reference.counts["output"]
            loss_channels = tuple(
                channel for channel in config.terminal_channels if channel != "output"
            )
            delta_losses = {
                channel: budget.counts[channel] - reference.counts[channel]
                for channel in loss_channels
            }
            if delta_output + sum(delta_losses.values()) != 0:
                raise ValueError(f"B6 delta-loss closure failed for {sigma}/{state}")
            dominant = max(delta_losses, key=lambda channel: abs(delta_losses[channel]))
            balance_rows.append((sigma, state, delta_output, delta_losses, dominant))
    return balance_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--b4-input-dir", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    config, budgets = load_budgets(args.input_dir, args.b4_input_dir, args.config)
    balance_rows = validate_budgets(config, budgets)
    for sigma, state, delta_output, delta_losses, dominant in balance_rows:
        if sigma != config.comparison_sigma:
            continue
        generated = budgets[(sigma, state)].generated
        print(
            f"[b6-check] sigma={sigma:.2f} state={state} "
            f"delta_output={delta_output / generated:+.8f} "
            f"dominant_loss={dominant} "
            f"delta_dominant={delta_losses[dominant] / generated:+.8f} "
            "delta_balance=closed status=PASS"
        )
    print(
        f"[b6-check] budgets={len(budgets)} surface_locations=5 "
        "surface_subtotals=closed terminal_balances=closed "
        "top_black_absorption=active experimental_fit=false status=PASS"
    )
    print("[b6-check] loss_diagnostics status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
