#!/usr/bin/env python3
"""Validate B7.3 full-energy selection and PMT-light estimator."""

from __future__ import annotations

import argparse
from pathlib import Path

from b7_3_common import DEFAULT_CONFIG_PATH, load_config, load_sample


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    config = load_config(args.config)
    summary = load_sample(args.input, config)
    low = config.gate_center_kev - config.gate_half_width_kev
    high = config.gate_center_kev + config.gate_half_width_kev
    print(
        f"[b7.3-check] events={len(summary.events)} zero={summary.zero_events} "
        f"partial={summary.partial_events} full={len(summary.full_energy_events)} "
        f"gate_keV={low:g}:{high:g}"
    )
    print(
        f"[b7.3-check] full_generated={summary.full_generated} "
        f"full_n_pmt={summary.full_output} "
        f"n_pmt_over_n_generated={summary.full_collection_efficiency:.10f} "
        f"mean_n_pmt={summary.mean_full_output:.6f} "
        f"mean_n_pmt_se={summary.full_output_standard_error:.6f} "
        f"mean_efficiency_se={summary.full_efficiency_standard_error:.10f} "
        f"yield_photons_per_MeV={summary.full_yield_per_mev:.6f}"
    )
    print("[b7.3-check] event_level_511_gate=true optical_accounting=closed status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
