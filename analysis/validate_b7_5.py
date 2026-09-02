#!/usr/bin/env python3
"""Validate and summarize the paired B7.5 end-face comparison without plotting."""

from __future__ import annotations

import argparse
import csv
import math
import random
from pathlib import Path

from b4_common import quantile
from b7_5_common import DEFAULT_CONFIG_PATH, load_config, load_paired_samples


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    config = load_config(args.config)
    summaries = load_paired_samples(args.input_dir, args.reference, config)
    reference = summaries["all_polished"]
    bottom = summaries["bottom_rough"]
    top = summaries["top_rough"]
    both = summaries["top_bottom_rough"]
    if len({len(summary.full_energy_events) for summary in summaries.values()}) != 1:
        raise ValueError("B7.5 paired samples selected different full-energy counts")

    alpha = (1.0 - config.confidence_level) / 2.0
    generator = random.Random(config.bootstrap_seed)
    boot_to_reference = {state: [] for state in config.states}
    boot_bottom_top: list[float] = []
    boot_both_bottom: list[float] = []
    boot_both_top: list[float] = []
    count = len(reference.full_energy_events)
    for _ in range(config.bootstrap_samples):
        indices = [generator.randrange(count) for _ in range(count)]
        ref_out = sum(reference.full_energy_events[index].output for index in indices)
        bottom_out = sum(bottom.full_energy_events[index].output for index in indices)
        top_out = sum(top.full_energy_events[index].output for index in indices)
        both_out = sum(both.full_energy_events[index].output for index in indices)
        boot_to_reference["bottom_rough"].append(bottom_out / ref_out)
        boot_to_reference["top_rough"].append(top_out / ref_out)
        boot_to_reference["top_bottom_rough"].append(both_out / ref_out)
        boot_bottom_top.append(bottom_out / top_out)
        boot_both_bottom.append(both_out / bottom_out)
        boot_both_top.append(both_out / top_out)

    output_path = args.input_dir / "b7_5_endface_summary.csv"
    fields = [
        "state", "sigma_alpha_rad", "events", "full_energy_events",
        "full_generated", "full_n_pmt", "collection_efficiency",
        "mean_n_pmt", "mean_n_pmt_se", "normalized_to_all_polished",
        "normalized_ci95_low", "normalized_ci95_high", "experiment_normalized",
    ]
    bootstrap = {
        "all_polished": [1.0],
        **boot_to_reference,
    }
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for state in ("all_polished", *config.states):
            summary = summaries[state]
            normalized = summary.full_collection_efficiency / reference.full_collection_efficiency
            values = bootstrap[state]
            low = high = 1.0 if state == "all_polished" else None
            if low is None:
                low = quantile(values, alpha)
                high = quantile(values, 1.0 - alpha)
            writer.writerow({
                "state": state,
                "sigma_alpha_rad": config.response.sigma_alpha_rad if state == "all_polished" else config.sigma,
                "events": len(summary.events),
                "full_energy_events": len(summary.full_energy_events),
                "full_generated": summary.full_generated,
                "full_n_pmt": summary.full_output,
                "collection_efficiency": f"{summary.full_collection_efficiency:.12f}",
                "mean_n_pmt": f"{summary.mean_full_output:.6f}",
                "mean_n_pmt_se": f"{summary.full_output_standard_error:.6f}",
                "normalized_to_all_polished": f"{normalized:.12f}",
                "normalized_ci95_low": f"{low:.12f}",
                "normalized_ci95_high": f"{high:.12f}",
                "experiment_normalized": (
                    "" if config.measured_ratios[state] is None
                    else f"{config.measured_ratios[state]:.6f}"
                ),
            })

    bottom_over_top = bottom.full_output / top.full_output
    ratio_low = quantile(boot_bottom_top, alpha)
    ratio_high = quantile(boot_bottom_top, 1.0 - alpha)
    difference = bottom.mean_full_output - top.mean_full_output
    paired_differences = [
        bottom.full_energy_events[index].output - top.full_energy_events[index].output
        for index in range(count)
    ]
    mean_difference = sum(paired_differences) / count
    variance = sum((value - mean_difference) ** 2 for value in paired_differences) / (count - 1)
    difference_se = math.sqrt(variance / count)
    comparison_path = args.input_dir / "b7_5_endface_comparison.csv"
    with comparison_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["metric", "value", "ci95_low", "ci95_high"])
        writer.writerow(["bottom_over_top_n_pmt", f"{bottom_over_top:.12f}", f"{ratio_low:.12f}", f"{ratio_high:.12f}"])
        writer.writerow([
            "top_bottom_over_bottom_n_pmt",
            f"{both.full_output / bottom.full_output:.12f}",
            f"{quantile(boot_both_bottom, alpha):.12f}",
            f"{quantile(boot_both_bottom, 1.0 - alpha):.12f}",
        ])
        writer.writerow([
            "top_bottom_over_top_n_pmt",
            f"{both.full_output / top.full_output:.12f}",
            f"{quantile(boot_both_top, alpha):.12f}",
            f"{quantile(boot_both_top, 1.0 - alpha):.12f}",
        ])
        writer.writerow(["bottom_minus_top_mean_n_pmt", f"{difference:.6f}", "", ""])
        writer.writerow(["paired_difference_standard_error", f"{difference_se:.6f}", "", ""])

    print(
        f"[b7.5-check] events={len(reference.events)} full={count} sigma_rad={config.sigma:g} "
        "history_pairing=exact optical_accounting=closed"
    )
    for state in config.states:
        summary = summaries[state]
        normalized = summary.full_collection_efficiency / reference.full_collection_efficiency
        print(
            f"[b7.5-result] state={state} full_n_pmt={summary.full_output} "
            f"mean_n_pmt={summary.mean_full_output:.6f} "
            f"efficiency={summary.full_collection_efficiency:.10f} "
            f"normalized={normalized:.6f}"
        )
    print(
        f"[b7.5-comparison] bottom_over_top={bottom_over_top:.6f} "
        f"ci95={ratio_low:.6f}:{ratio_high:.6f} "
        f"bottom_minus_top_mean_n_pmt={difference:.6f} "
        f"paired_se={difference_se:.6f} no_plot=true status=PASS"
    )
    both_over_bottom = both.full_output / bottom.full_output
    both_over_top = both.full_output / top.full_output
    both_bottom_low = quantile(boot_both_bottom, alpha)
    both_top_low = quantile(boot_both_top, alpha)
    print(
        f"[b7.5-new-state] state=top_bottom_rough "
        f"full_n_pmt={both.full_output} mean_n_pmt={both.mean_full_output:.6f} "
        f"efficiency={both.full_collection_efficiency:.10f} "
        f"normalized={both.full_collection_efficiency / reference.full_collection_efficiency:.6f} "
        f"over_bottom={both_over_bottom:.6f} over_top={both_over_top:.6f} "
        f"higher_than_both={(both_bottom_low > 1.0 and both_top_low > 1.0)} "
        "no_plot=true status=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
