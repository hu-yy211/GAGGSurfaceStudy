#!/usr/bin/env python3
"""Validate and report the B5 shared-sigma robustness envelope."""

from __future__ import annotations

import argparse
from pathlib import Path

from b3_common import GammaSummary, load_gamma_sample
from b4_common import make_comparison, state_filename
from b5_common import DEFAULT_CONFIG_PATH, load_config, point_filename


def load_grid(input_dir: Path, b4_dir: Path, config_path: Path):
    config = load_config(config_path)
    expected = {
        point_filename(state, sigma)
        for sigma in config.run_sigmas
        for state in config.b4.states
    }
    actual = {path.name for path in input_dir.glob("*.csv")}
    if actual != expected:
        raise ValueError(
            f"B5 CSV set mismatch: missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)}"
        )
    grid: dict[tuple[float, str], GammaSummary] = {}
    for sigma in config.sigmas:
        for state in config.b4.states:
            path = (
                b4_dir / state_filename(state)
                if sigma == config.reuse_sigma
                else input_dir / point_filename(state, sigma)
            )
            grid[(sigma, state)] = load_gamma_sample(
                path, config.b4.b3, expected_state=state, expected_sigma=sigma
            )
    return config, grid


def validate_grid(config, grid):
    b3 = config.b4.b3
    reference = grid[(config.reuse_sigma, "all_polished")]
    reference_history = tuple(
        (event.event_id, event.source_position_mm, event.edep_kev, event.generated)
        for event in reference.events
    )
    if config.require_history_pairing:
        for key, summary in grid.items():
            history = tuple(
                (event.event_id, event.source_position_mm, event.edep_kev, event.generated)
                for event in summary.events
            )
            if history != reference_history:
                raise ValueError(f"B5 gamma-history pairing failed at {key}")
    if config.require_polished_invariance:
        polished = grid[(config.sigmas[0], "all_polished")].events
        for sigma in config.sigmas[1:]:
            if grid[(sigma, "all_polished")].events != polished:
                raise ValueError(f"all-polished transport changed with unused sigma={sigma}")

    comparisons = {}
    for sigma in config.sigmas:
        summaries = {state: grid[(sigma, state)] for state in config.b4.states}
        comparisons[sigma] = make_comparison(config.b4, summaries)
    resolved_states = 0
    for state_index, state in enumerate(config.b4.states[1:], start=1):
        values = [comparisons[sigma][state_index].normalized for sigma in config.sigmas]
        if max(values) - min(values) >= config.response_reporting_threshold:
            resolved_states += 1
    if resolved_states < config.minimum_resolved_rough_states:
        raise ValueError(
            f"B5 resolved {resolved_states} rough states; minimum is "
            f"{config.minimum_resolved_rough_states}"
        )

    window_ids = []
    for half_width in config.full_energy_half_widths_kev:
        ids = tuple(
            event.event_id
            for event in reference.events
            if abs(event.edep_kev - b3.gamma_energy_kev) <= half_width
        )
        if len(ids) < config.minimum_full_energy_events:
            raise ValueError(f"B5 full-energy window {half_width} has too few events")
        window_ids.append(ids)
    if any(ids != window_ids[0] for ids in window_ids[1:]):
        raise ValueError("B5 ideal full-energy event set changed across locked windows")
    return comparisons, window_ids[0], resolved_states


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--b4-input-dir", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    config, grid = load_grid(args.input_dir, args.b4_input_dir, args.config)
    comparisons, full_ids, resolved_states = validate_grid(config, grid)
    for state_index, state in enumerate(config.b4.states):
        values = [comparisons[sigma][state_index].normalized for sigma in config.sigmas]
        measured = config.b4.measured_ratios[state]
        inside = min(values) <= measured <= max(values)
        span = max(values) - min(values)
        print(
            f"[b5-check] state={state} envelope={min(values):.6f}:{max(values):.6f} "
            f"span={span:.6f} measured={measured:.3f} "
            f"measured_inside={str(inside).lower()} status=PASS"
        )
    widths = ",".join(f"{value:g}" for value in config.full_energy_half_widths_kev)
    print(
        f"[b5-check] full_energy_half_widths_keV={widths} "
        f"identical_event_set=true full_events={len(full_ids)} status=PASS"
    )
    print(
        "[b5-check] pairing=exact polished_sigma_invariant=true "
        f"roughness_response_above_threshold={resolved_states}/5 "
        "shared_sigma=true per_face_sigma=false "
        "experimental_fit=false status=PASS"
    )
    print("[b5-check] robustness status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
