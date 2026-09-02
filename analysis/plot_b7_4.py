#!/usr/bin/env python3
"""Plot the B7.4 sigma trends, objective and best six-state comparison."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from b7_4_common import (
    DEFAULT_CONFIG_PATH, best_positive_score, best_score,
    load_config, load_scan,
)


LABELS = {
    "all_polished": "All polished",
    "bottom_rough": "Bottom rough",
    "top_rough": "Top rough",
    "side_rough": "Side rough",
    "bottom_polished_others_rough": "Bottom polished,\nothers rough",
    "top_polished_others_rough": "Top polished,\nothers rough",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    config = load_config(args.config)
    _, rows, scores = load_scan(args.input_dir, config)
    best = best_score(scores)
    best_positive = best_positive_score(scores)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = args.output_dir / "b7_4_sigma_scan_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow([
            "sigma_alpha_rad", "state", "full_energy_events", "full_generated",
            "n_pmt", "n_pmt_per_generated", "simulation_normalized", "ci95_low",
            "ci95_high", "measured_normalized", "simulation_minus_measured",
        ])
        for row in rows:
            writer.writerow([
                row.sigma, row.state, row.full_events, row.generated, row.output,
                f"{row.efficiency:.10f}", f"{row.normalized:.10f}",
                f"{row.ci_low:.10f}", f"{row.ci_high:.10f}",
                f"{row.measured:.10f}", f"{row.residual:.10f}",
            ])
    score_path = args.output_dir / "b7_4_sigma_scores.csv"
    with score_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["sigma_alpha_rad", "rmse_non_reference", "mae_non_reference", "pair_order_fraction", "selected_best", "selected_best_positive"])
        for score in scores:
            writer.writerow([score.sigma, f"{score.rmse:.10f}", f"{score.mae:.10f}", f"{score.pair_order_fraction:.10f}", int(score == best), int(score == best_positive)])

    figure, axes = plt.subplots(2, 3, figsize=(14.0, 8.2), sharex=True)
    for axis, state in zip(axes.flat, config.states):
        state_rows = [row for row in rows if row.state == state]
        x = [row.sigma for row in state_rows]
        y = [row.normalized for row in state_rows]
        errors = [
            [row.normalized - row.ci_low for row in state_rows],
            [row.ci_high - row.normalized for row in state_rows],
        ]
        axis.errorbar(x, y, yerr=errors, marker="o", capsize=3, color="#2878B5", label="Geant4")
        axis.axhline(state_rows[0].measured, color="#D95F02", linestyle="--", label="Experiment")
        axis.axvline(best.sigma, color="#555555", linestyle=":", alpha=0.8)
        axis.set_title(LABELS[state])
        axis.grid(alpha=0.25)
    for axis in axes[-1, :]:
        axis.set_xlabel("Shared sigma_alpha (rad)")
    for axis in axes[:, 0]:
        axis.set_ylabel("Relative light output")
    axes[0, 0].legend()
    figure.suptitle(f"B7.4 shared-roughness scan; RMSE best sigma = {best.sigma:g} rad")
    figure.tight_layout()
    trends_path = args.output_dir / "b7_4_sigma_trends.png"
    figure.savefig(trends_path, dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(8.5, 5.2))
    axis.plot([score.sigma for score in scores], [score.rmse for score in scores], marker="o", color="#6A5ACD")
    axis.scatter([best.sigma], [best.rmse], s=90, color="#D95F02", zorder=3, label=f"mathematical best = {best.sigma:g} rad")
    axis.scatter([best_positive.sigma], [best_positive.rmse], s=90, marker="s", color="#3A923A", zorder=3, label=f"best positive = {best_positive.sigma:g} rad")
    axis.set(xlabel="Shared sigma_alpha (rad)", ylabel="RMSE over five rough states", title="B7.4 experiment-comparison objective")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    objective_path = args.output_dir / "b7_4_sigma_objective.png"
    figure.savefig(objective_path, dpi=180)
    plt.close(figure)

    best_rows = [row for row in rows if row.sigma == best_positive.sigma]
    x = list(range(len(best_rows)))
    width = 0.36
    figure, axis = plt.subplots(figsize=(12.2, 6.2))
    errors = [
        [row.normalized - row.ci_low for row in best_rows],
        [row.ci_high - row.normalized for row in best_rows],
    ]
    axis.bar([value-width/2 for value in x], [row.normalized for row in best_rows], width, yerr=errors, capsize=3, color="#2878B5", label=f"Geant4, sigma={best_positive.sigma:g} rad")
    axis.bar([value+width/2 for value in x], [row.measured for row in best_rows], width, color="#D95F02", label="Experiment (preliminary)")
    axis.axhline(1.0, color="#555555", linestyle="--", linewidth=1)
    axis.set_xticks(x, [LABELS[row.state] for row in best_rows])
    axis.set_ylabel("Relative 511 keV light output (all polished = 1)")
    axis.set_title("B7.4 best positive coarse-grid shared roughness")
    axis.grid(axis="y", alpha=0.25)
    axis.legend()
    figure.tight_layout()
    comparison_path = args.output_dir / "b7_4_best_positive_vs_experiment.png"
    figure.savefig(comparison_path, dpi=180)
    plt.close(figure)

    for path in (summary_path, score_path, trends_path, objective_path, comparison_path):
        print(f"[b7.4-plot] wrote={path}")
    print("[b7.4-plot] status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
