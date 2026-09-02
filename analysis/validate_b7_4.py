#!/usr/bin/env python3
"""Validate and rank the B7.4 shared-sigma coarse scan."""

from __future__ import annotations

import argparse
from pathlib import Path

from b7_4_common import (
    DEFAULT_CONFIG_PATH, best_positive_score, best_score,
    load_config, load_scan, point_path,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    config = load_config(args.config)
    expected = {
        point_path(args.input_dir, state, sigma, config.reference_sigma).resolve()
        for sigma in config.sigmas for state in config.states
    }
    actual = {path.resolve() for path in args.input_dir.glob("*.csv")}
    actual.update(path.resolve() for path in args.input_dir.glob("sigma_*/*.csv"))
    if actual != expected:
        raise ValueError(
            f"B7.4 CSV set mismatch: missing={len(expected-actual)}, unexpected={len(actual-expected)}"
        )
    summaries, rows, scores = load_scan(args.input_dir, config)
    full_counts = {len(summary.full_energy_events) for summary in summaries.values()}
    if len(full_counts) != 1:
        raise ValueError(f"B7.4 full-energy event counts are not paired: {sorted(full_counts)}")
    spans = {}
    for state in config.states[1:]:
        values = [row.normalized for row in rows if row.state == state]
        spans[state] = max(values) - min(values)
    if max(spans.values()) <= 0.01:
        raise ValueError("B7.4 shared sigma did not produce a resolved response")

    for score in scores:
        print(
            f"[b7.4-score] sigma_rad={score.sigma:g} rmse={score.rmse:.8f} "
            f"mae={score.mae:.8f} pair_order_fraction={score.pair_order_fraction:.6f}"
        )
    best = best_score(scores)
    best_positive = best_positive_score(scores)
    best_rows = [row for row in rows if row.sigma == best.sigma]
    for row in best_rows:
        print(
            f"[b7.4-best] state={row.state} normalized={row.normalized:.6f} "
            f"ci95={row.ci_low:.6f}:{row.ci_high:.6f} measured={row.measured:.3f} "
            f"residual={row.residual:+.6f}"
        )
    boundary = best.sigma in (config.sigmas[0], config.sigmas[-1])
    print(
        f"[b7.4-check] events_per_point={config.response.events} "
        f"full_events={next(iter(full_counts))} points={1 + len(config.sigmas)*(len(config.states)-1)} "
        f"best_shared_sigma_rad={best.sigma:g} best_rmse={best.rmse:.8f} "
        f"best_at_grid_boundary={str(boundary).lower()} "
        f"best_positive_sigma_rad={best_positive.sigma:g} "
        f"best_positive_rmse={best_positive.rmse:.8f} "
        f"best_positive_at_grid_boundary={str(best_positive.sigma == config.sigmas[-1]).lower()}"
    )
    print(
        "[b7.4-check] pairing=exact accounting=closed shared_sigma=true "
        "per_face_fit=false agreement_pass_gate=false status=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
