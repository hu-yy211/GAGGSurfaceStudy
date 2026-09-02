#!/usr/bin/env python3
"""Create the B4 six-state prediction versus measurement chart and table."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from b3_common import load_gamma_sample
from b4_common import DEFAULT_CONFIG_PATH, load_config, make_comparison, state_filename


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
    summaries = {
        state: load_gamma_sample(
            args.input_dir / state_filename(state), config.b3,
            expected_state=state, expected_sigma=config.shared_sigma_alpha_rad,
        )
        for state in config.states
    }
    rows = make_comparison(config, summaries)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "b4_six_state_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow([
            "state", "full_energy_events", "full_generated", "n_pmt",
            "n_pmt_per_generated", "simulation_normalized", "ci95_low",
            "ci95_high", "measured_normalized", "simulation_minus_measured",
            "shared_sigma_alpha_rad",
            "gamma_source_mode", "source_z_mm",
        ])
        for row in rows:
            writer.writerow([
                row.state, row.full_energy_events, row.generated, row.output,
                f"{row.efficiency:.10f}", f"{row.normalized:.10f}",
                f"{row.ci_low:.10f}", f"{row.ci_high:.10f}",
                f"{row.measured:.10f}", f"{row.residual:.10f}",
                f"{config.shared_sigma_alpha_rad:.10f}",
                config.b3.gamma_source_mode,
                f"{config.b3.source_position_mm[2]:.10f}",
            ])

    x = list(range(len(rows)))
    width = 0.36
    simulated = [row.normalized for row in rows]
    measured = [row.measured for row in rows]
    errors = [
        [row.normalized - row.ci_low for row in rows],
        [row.ci_high - row.normalized for row in rows],
    ]
    figure, axis = plt.subplots(figsize=(13.4, 6.5))
    simulation_label = (
        f"Geant4, {config.b3.source_label}, "
        f"shared sigma={config.shared_sigma_alpha_rad:.2f} rad"
    )
    axis.bar([value - width / 2 for value in x], simulated, width, color="#2878B5", label=simulation_label, yerr=errors, capsize=3)
    axis.bar([value + width / 2 for value in x], measured, width, color="#D95F02", label="Experiment (preliminary)")
    axis.axhline(1.0, color="#555555", linestyle="--", linewidth=1)
    axis.set_xticks(x, [LABELS[row.state] for row in rows])
    axis.set_ylabel("Relative 511 keV light output (all polished = 1)")
    axis.set_title("B4: six surface states — prediction versus experiment\n" + config.b3.source_label)
    axis.grid(axis="y", alpha=0.25)
    axis.legend()
    figure.tight_layout()
    comparison_path = args.output_dir / "b4_prediction_vs_experiment.png"
    figure.savefig(comparison_path, dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(11.5, 5.4))
    residuals = [row.residual for row in rows]
    colors = ["#6A994E" if abs(value) < 0.1 else "#C14953" for value in residuals]
    axis.bar(x, residuals, color=colors)
    axis.axhline(0.0, color="#333333", linewidth=1.2)
    axis.set_xticks(x, [LABELS[row.state] for row in rows])
    axis.set_ylabel("Simulation − experiment")
    axis.set_title("B4 model discrepancy (not a fit objective)")
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    residual_path = args.output_dir / "b4_model_residuals.png"
    figure.savefig(residual_path, dpi=180)
    plt.close(figure)

    print(f"[b4-plot] wrote={summary_path}")
    print(f"[b4-plot] wrote={comparison_path}")
    print(f"[b4-plot] wrote={residual_path}")
    print("[b4-plot] status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
