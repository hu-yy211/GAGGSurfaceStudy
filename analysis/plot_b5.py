#!/usr/bin/env python3
"""Plot B5 shared-sigma sensitivity and write its robustness table."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from validate_b5 import load_grid, validate_grid
from b5_common import DEFAULT_CONFIG_PATH


LABELS = {
    "all_polished": "All polished",
    "bottom_rough": "Bottom rough",
    "top_rough": "Top rough",
    "side_rough": "Side rough",
    "bottom_polished_others_rough": "Bottom polished, others rough",
    "top_polished_others_rough": "Top polished, others rough",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--b4-input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    config, grid = load_grid(args.input_dir, args.b4_input_dir, args.config)
    comparisons, _, _ = validate_grid(config, grid)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = args.output_dir / "b5_shared_sigma_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow([
            "state", "sigma_alpha_rad", "n_pmt_per_generated",
            "simulation_normalized", "ci95_low", "ci95_high",
            "measured_normalized", "measured_inside_shared_sigma_envelope",
        ])
        envelopes = {
            state: (
                min(comparisons[sigma][index].normalized for sigma in config.sigmas),
                max(comparisons[sigma][index].normalized for sigma in config.sigmas),
            )
            for index, state in enumerate(config.b4.states)
        }
        for sigma in config.sigmas:
            for row in comparisons[sigma]:
                low, high = envelopes[row.state]
                writer.writerow([
                    row.state, f"{sigma:.10f}", f"{row.efficiency:.10f}",
                    f"{row.normalized:.10f}", f"{row.ci_low:.10f}",
                    f"{row.ci_high:.10f}", f"{row.measured:.10f}",
                    str(low <= row.measured <= high).lower(),
                ])

    figure, axes = plt.subplots(2, 3, figsize=(13.8, 8.4), sharex=True)
    for state_index, (axis, state) in enumerate(zip(axes.flat, config.b4.states)):
        rows = [comparisons[sigma][state_index] for sigma in config.sigmas]
        values = [row.normalized for row in rows]
        lower = [row.normalized - row.ci_low for row in rows]
        upper = [row.ci_high - row.normalized for row in rows]
        axis.errorbar(config.sigmas, values, yerr=[lower, upper], color="#2878B5", marker="o", capsize=3, linewidth=2, label="Geant4")
        axis.axhline(config.b4.measured_ratios[state], color="#D95F02", linestyle="--", linewidth=2, label="Experiment")
        axis.set_title(LABELS[state])
        axis.grid(alpha=0.25)
        axis.set_xlabel("Shared sigma_alpha (rad)")
        axis.set_ylabel("Normalized 511 keV light")
    axes.flat[0].legend()
    figure.suptitle("B5: shared-roughness sensitivity (no per-face fit)", fontsize=15)
    figure.tight_layout(rect=(0, 0, 1, 0.96))
    scan_path = args.output_dir / "b5_shared_sigma_scan.png"
    figure.savefig(scan_path, dpi=180)
    plt.close(figure)

    print(f"[b5-plot] wrote={summary_path}")
    print(f"[b5-plot] wrote={scan_path}")
    print("[b5-plot] status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
