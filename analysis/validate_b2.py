#!/usr/bin/env python3
"""Validate the predeclared B2 optical-only position/roughness grid."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from b2_common import (
    DEFAULT_CONFIG_PATH,
    B2Config,
    load_config,
    point_filename,
    repeat_filename,
)
from validate_a0_csv import COUNT_COLUMNS, EXPECTED_COLUMNS


@dataclass(frozen=True)
class PointSummary:
    state: str
    position_tag: str
    sigma_tag: str
    sigma_alpha_rad: float
    generated: int
    output: int
    top_interactions: int
    bottom_interactions: int
    side_interactions: int
    rows: tuple[tuple[str, ...], ...]
    transport_rows: tuple[tuple[str, ...], ...]

    @property
    def efficiency(self) -> float:
        return self.output / self.generated


def load_point(
    path: Path,
    config: B2Config,
    state: str,
    position_tag: str,
    sigma_tag: str,
) -> PointSummary:
    position = config.position(position_tag)
    sigma = config.sigma(sigma_tag)
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(f"unexpected B2 columns in {path}")
        rows = list(reader)
    if len(rows) != config.events_per_point:
        raise ValueError(
            f"expected {config.events_per_point} events in {path}, found {len(rows)}"
        )

    totals = {key: 0 for key in COUNT_COLUMNS}
    canonical_rows: list[tuple[str, ...]] = []
    transport_rows: list[tuple[str, ...]] = []
    transport_columns = [
        key for key in EXPECTED_COLUMNS if key != "stage_b_sigma_alpha_rad"
    ]
    for event_id, row in enumerate(rows):
        if int(row["event_id"]) != event_id:
            raise ValueError(f"non-contiguous event IDs in {path}")
        actual_position = tuple(
            float(row[key])
            for key in ("source_x_mm", "source_y_mm", "source_z_mm")
        )
        if actual_position != position.xyz_mm:
            raise ValueError(f"source-position mismatch in {path}")
        if row["source_particle"] != "optical" or row["stage_a_surface"] != "none":
            raise ValueError(f"non-B2 source or Stage A surface in {path}")
        if row["stage_b_surface_state"] != state:
            raise ValueError(f"Stage B state mismatch in {path}")
        if abs(float(row["stage_b_sigma_alpha_rad"]) - sigma.value_rad) > 1.0e-12:
            raise ValueError(f"sigma_alpha mismatch in {path}")
        if float(row["edep_keV"]) != 0.0 or int(row["scintillation"]) != 0:
            raise ValueError(f"B2 optical primaries deposited energy in {path}")

        values = {key: int(row[key]) for key in COUNT_COLUMNS}
        if values["generated"] != config.photons_per_event:
            raise ValueError(f"incorrect generated count in {path}")
        if values["world_exit"] != values["output"] + values["other_world_exit"]:
            raise ValueError(f"world-exit subtotal failed in {path}")
        if values["bulk_absorption"] != (
            values["crystal_absorption"]
            + values["reflector_absorption"]
            + values["other_absorption"]
        ):
            raise ValueError(f"bulk-absorption subtotal failed in {path}")
        classified = (
            values["world_exit"]
            + values["bulk_absorption"]
            + values["surface_absorption"]
        )
        if classified != values["generated"] or values["unclassified"] != 0:
            raise ValueError(f"B2 photon accounting failed in {path}")
        face_interactions = (
            values["top_surface_interactions"]
            + values["bottom_surface_interactions"]
            + values["side_surface_interactions"]
        )
        if values["lut_interactions"] < face_interactions:
            raise ValueError(f"B2 face counters exceed all borders in {path}")
        if values["output"] > values["bottom_surface_interactions"]:
            raise ValueError(f"B2 PMT count exceeds bottom interactions in {path}")
        for key, value in values.items():
            totals[key] += value
        canonical_rows.append(tuple(row[key] for key in EXPECTED_COLUMNS))
        transport_rows.append(tuple(row[key] for key in transport_columns))

    for face in (
        "top_surface_interactions",
        "bottom_surface_interactions",
        "side_surface_interactions",
    ):
        if totals[face] <= 0:
            raise ValueError(f"{face} was not exercised in {path}")
    if totals["output"] <= 0:
        raise ValueError(f"B2 delivered no light to the PMT in {path}")

    return PointSummary(
        state=state,
        position_tag=position_tag,
        sigma_tag=sigma_tag,
        sigma_alpha_rad=sigma.value_rad,
        generated=totals["generated"],
        output=totals["output"],
        top_interactions=totals["top_surface_interactions"],
        bottom_interactions=totals["bottom_surface_interactions"],
        side_interactions=totals["side_surface_interactions"],
        rows=tuple(canonical_rows),
        transport_rows=tuple(transport_rows),
    )


def load_grid(
    input_dir: Path, config_path: Path = DEFAULT_CONFIG_PATH
) -> tuple[B2Config, dict[tuple[str, str, str], PointSummary]]:
    config = load_config(config_path)
    expected_names = {
        point_filename(state, position.tag, sigma.tag)
        for state in config.states
        for sigma in config.sigmas
        for position in config.positions
    }
    expected_names.add(repeat_filename(config))
    actual_names = {path.name for path in input_dir.glob("*.csv")}
    if actual_names != expected_names:
        raise ValueError(
            f"B2 CSV set mismatch: missing={sorted(expected_names - actual_names)}, "
            f"unexpected={sorted(actual_names - expected_names)}"
        )

    summaries = {
        (state, position.tag, sigma.tag): load_point(
            input_dir / point_filename(state, position.tag, sigma.tag),
            config,
            state,
            position.tag,
            sigma.tag,
        )
        for state in config.states
        for sigma in config.sigmas
        for position in config.positions
    }
    repeat = config.repeat
    repeated = load_point(
        input_dir / repeat_filename(config),
        config,
        repeat.state,
        repeat.position_tag,
        repeat.sigma_tag,
    )
    original = summaries[(repeat.state, repeat.position_tag, repeat.sigma_tag)]
    if original.rows != repeated.rows:
        raise ValueError("B2 repeat point is not exactly reproducible")

    for position in config.positions:
        reference = summaries[("all_polished", position.tag, config.sigmas[0].tag)]
        for sigma in config.sigmas[1:]:
            candidate = summaries[("all_polished", position.tag, sigma.tag)]
            if candidate.transport_rows != reference.transport_rows:
                raise ValueError(
                    "all-polished transport changed with unused sigma_alpha at "
                    f"{position.tag}"
                )

    for state in config.states[1:]:
        response_spans = []
        for position in config.positions:
            efficiencies = [
                summaries[(state, position.tag, sigma.tag)].efficiency
                for sigma in config.sigmas
            ]
            jumps = [
                abs(right - left)
                for left, right in zip(efficiencies, efficiencies[1:])
            ]
            if max(jumps) > config.max_adjacent_efficiency_jump:
                raise ValueError(
                    f"B2 response jump exceeded the predeclared limit for "
                    f"{state} at {position.tag}: {max(jumps):.6f}"
                )
            response_spans.append(max(efficiencies) - min(efficiencies))
        if max(response_spans) < config.min_rough_response_span:
            raise ValueError(
                f"B2 roughness response was not resolved at any position for {state}"
            )
    return config, summaries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()

    config, summaries = load_grid(args.input_dir, args.config)
    for state in config.states:
        for position in config.positions:
            efficiencies = [
                summaries[(state, position.tag, sigma.tag)].efficiency
                for sigma in config.sigmas
            ]
            jumps = [
                abs(right - left)
                for left, right in zip(efficiencies, efficiencies[1:])
            ]
            print(
                f"[b2-check] state={state} position={position.tag} "
                f"min_efficiency={min(efficiencies):.8f} "
                f"max_efficiency={max(efficiencies):.8f} "
                f"response_span={max(efficiencies) - min(efficiencies):.8f} "
                f"max_adjacent_jump={max(jumps):.8f} status=PASS"
            )
    print(
        f"[b2-check] points={config.point_count} accounting=closed "
        "repeat_exact=true all_polished_sigma_invariant=true "
        "smooth_response=true optical_only=true experimental_order_tested=false "
        "selected_sigma=false status=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
