#!/usr/bin/env python3
"""Validate paired B4 samples and report simulation/experiment differences."""

from __future__ import annotations

import argparse
from pathlib import Path

from b3_common import load_gamma_sample
from b4_common import DEFAULT_CONFIG_PATH, load_config, make_comparison, state_filename


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--b3-reference", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    config = load_config(args.config)
    expected_files = {state_filename(state) for state in config.states}
    actual_files = {path.name for path in args.input_dir.glob("*.csv")}
    if actual_files != expected_files:
        raise ValueError(
            f"B4 CSV set mismatch: missing={sorted(expected_files - actual_files)}, "
            f"unexpected={sorted(actual_files - expected_files)}"
        )
    summaries = {
        state: load_gamma_sample(
            args.input_dir / state_filename(state),
            config.b3,
            expected_state=state,
            expected_sigma=config.shared_sigma_alpha_rad,
        )
        for state in config.states
    }
    reference_events = summaries["all_polished"].events
    reference_history = tuple(
        (event.event_id, event.source_position_mm, event.edep_kev, event.generated)
        for event in reference_events
    )
    for state in config.states[1:]:
        history = tuple(
            (event.event_id, event.source_position_mm, event.edep_kev, event.generated)
            for event in summaries[state].events
        )
        if history != reference_history:
            raise ValueError(f"gamma/Edep/generated event pairing failed for {state}")
    repeat_status = "not_required"
    if config.require_exact_b3_repeat:
        b3_reference = load_gamma_sample(args.b3_reference, config.b3)
        if b3_reference.events != summaries["all_polished"].events:
            raise ValueError("B4 all-polished sample is not an exact B3 repeat")
        repeat_status = "exact"

    rows = make_comparison(config, summaries)
    for row in rows:
        print(
            f"[b4-check] state={row.state} full_events={row.full_energy_events} "
            f"efficiency={row.efficiency:.8f} normalized={row.normalized:.6f} "
            f"ci95={row.ci_low:.6f}:{row.ci_high:.6f} "
            f"measured={row.measured:.3f} residual={row.residual:+.6f} status=PASS"
        )
    print(
        f"[b4-check] pairing=exact b3_repeat={repeat_status} accounting=closed "
        "shared_sigma=true per_face_fit=false experimental_agreement_gate=false status=PASS"
    )
    print("[b4-check] six_state_comparison status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
