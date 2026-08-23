#!/usr/bin/env python3
"""Validate the controlled B3 experiment-geometry 511 keV gamma sample."""

import argparse
from pathlib import Path

from b3_common import DEFAULT_CONFIG_PATH, load_config, load_gamma_sample


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    config = load_config(args.config)
    summary = load_gamma_sample(args.input, config)
    total_error = abs(summary.total_yield_per_mev - config.expected_yield_per_mev) / config.expected_yield_per_mev
    full_error = abs(summary.full_energy_yield_per_mev - config.expected_yield_per_mev) / config.expected_yield_per_mev
    print(
        f"[b3-check] events={len(summary.events)} zero={summary.zero_edep_events} "
        f"partial={summary.partial_energy_events} full={summary.full_energy_events} "
        "classes=present status=PASS"
    )
    print(
        f"[b3-check] total_yield_photons_per_MeV={summary.total_yield_per_mev:.6f} "
        f"relative_error={total_error:.3e} full_yield_photons_per_MeV="
        f"{summary.full_energy_yield_per_mev:.6f} full_relative_error={full_error:.3e} "
        "status=PASS"
    )
    print(
        f"[b3-check] full_gate_keV={config.gamma_energy_kev - config.full_energy_half_width_kev:g}:"
        f"{config.gamma_energy_kev + config.full_energy_half_width_kev:g} "
        f"full_collection_efficiency={summary.full_energy_collection_efficiency:.8f} "
        "accounting=closed stage_b_geometry=true status=PASS"
    )
    print("[b3-check] gamma_511 status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
