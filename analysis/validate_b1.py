#!/usr/bin/env python3
"""Validate B1 runtime surface switching and independent face counters."""

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from validate_a0_csv import (
    COUNT_COLUMNS,
    EXPECTED_COLUMNS,
    validate_surface_absorption_subtotal,
)


STATES = (
    "all_polished",
    "bottom_rough",
    "top_rough",
    "side_rough",
    "bottom_polished_others_rough",
    "top_polished_others_rough",
)

ROUGH_FACES = {
    "all_polished": (),
    "bottom_rough": ("bottom",),
    "top_rough": ("top",),
    "side_rough": ("side",),
    "bottom_polished_others_rough": ("top", "side"),
    "top_polished_others_rough": ("bottom", "side"),
}


@dataclass(frozen=True)
class StateSummary:
    state: str
    rows: tuple[tuple[str, ...], ...]
    generated: int
    output: int
    top_interactions: int
    bottom_interactions: int
    side_interactions: int
    border_interactions: int

    @property
    def efficiency(self) -> float:
        return self.output / self.generated


def load_state(
    path: Path,
    expected_state: str,
    expected_events: int,
    photons_per_event: int,
    sigma_alpha: float,
) -> StateSummary:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(f"unexpected B1 columns in {path}")
        rows = list(reader)
    if len(rows) != expected_events:
        raise ValueError(
            f"expected {expected_events} events in {path}, found {len(rows)}"
        )

    totals = {key: 0 for key in COUNT_COLUMNS}
    canonical_rows: list[tuple[str, ...]] = []
    for event_id, row in enumerate(rows):
        if int(row["event_id"]) != event_id:
            raise ValueError(f"non-contiguous B1 event IDs in {path}")
        if row["source_particle"] != "optical":
            raise ValueError(f"non-optical B1 source in {path}")
        if row["stage_a_surface"] != "none":
            raise ValueError(f"Stage A LUT active in {path}")
        if row["stage_b_surface_state"] != expected_state:
            raise ValueError(f"Stage B state mismatch in {path}")
        if abs(float(row["stage_b_sigma_alpha_rad"]) - sigma_alpha) > 1.0e-12:
            raise ValueError(f"shared sigma_alpha mismatch in {path}")
        if tuple(float(row[key]) for key in EXPECTED_COLUMNS[1:4]) != (
            0.0,
            0.0,
            0.0,
        ):
            raise ValueError(f"B1 source is not at the crystal center in {path}")
        if float(row["edep_keV"]) != 0.0 or int(row["scintillation"]) != 0:
            raise ValueError(f"B1 optical primaries deposited energy in {path}")

        values = {key: int(row[key]) for key in COUNT_COLUMNS}
        if values["generated"] != photons_per_event:
            raise ValueError(f"incorrect generated count in {path}")
        if values["world_exit"] != (
            values["output"] + values["other_world_exit"]
        ):
            raise ValueError(f"world-exit subtotal failed in {path}")
        if values["bulk_absorption"] != (
            values["crystal_absorption"]
            + values["reflector_absorption"]
            + values["other_absorption"]
        ):
            raise ValueError(f"bulk-absorption subtotal failed in {path}")
        validate_surface_absorption_subtotal(values, path)
        classified = (
            values["world_exit"]
            + values["bulk_absorption"]
            + values["surface_absorption"]
        )
        if classified != values["generated"] or values["unclassified"] != 0:
            raise ValueError(f"B1 photon accounting failed in {path}")
        face_interactions = (
            values["top_surface_interactions"]
            + values["bottom_surface_interactions"]
            + values["side_surface_interactions"]
        )
        if values["lut_interactions"] < face_interactions:
            raise ValueError(f"B1 face counters exceed all borders in {path}")
        if values["output"] > values["bottom_surface_interactions"]:
            raise ValueError(f"B1 PMT count exceeds bottom interactions in {path}")
        for key, value in values.items():
            totals[key] += value
        canonical_rows.append(tuple(row[key] for key in EXPECTED_COLUMNS))

    for face in (
        "top_surface_interactions",
        "bottom_surface_interactions",
        "side_surface_interactions",
    ):
        if totals[face] <= 0:
            raise ValueError(f"{face} was not exercised in {path}")
    if totals["output"] <= 0:
        raise ValueError(f"B1 did not deliver light to PMT in {path}")

    return StateSummary(
        state=expected_state,
        rows=tuple(canonical_rows),
        generated=totals["generated"],
        output=totals["output"],
        top_interactions=totals["top_surface_interactions"],
        bottom_interactions=totals["bottom_surface_interactions"],
        side_interactions=totals["side_surface_interactions"],
        border_interactions=totals["lut_interactions"],
    )


def load_comparison(
    input_dir: Path,
    expected_events: int = 50,
    photons_per_event: int = 100,
    sigma_alpha: float = 0.20,
) -> dict[str, StateSummary]:
    summaries = {
        state: load_state(
            input_dir / f"{state}.csv",
            state,
            expected_events,
            photons_per_event,
            sigma_alpha,
        )
        for state in STATES
    }
    repeat = load_state(
        input_dir / "all_polished_repeat.csv",
        "all_polished",
        expected_events,
        photons_per_event,
        sigma_alpha,
    )
    if summaries["all_polished"].rows != repeat.rows:
        raise ValueError("all-polished B1 repeat is not exactly reproducible")
    if len({summary.output for summary in summaries.values()}) < 2:
        raise ValueError("B1 surface switching did not change optical output")
    return summaries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--expect-events", type=int, default=50)
    parser.add_argument("--photons-per-event", type=int, default=100)
    parser.add_argument("--sigma-alpha", type=float, default=0.20)
    args = parser.parse_args()

    summaries = load_comparison(
        args.input_dir,
        args.expect_events,
        args.photons_per_event,
        args.sigma_alpha,
    )
    reference = summaries["all_polished"].efficiency
    for state in STATES:
        summary = summaries[state]
        rough = ROUGH_FACES[state]
        print(
            f"[b1-check] state={state} rough_faces="
            f"{'+'.join(rough) if rough else 'none'} "
            f"sigma_alpha_rad={args.sigma_alpha:.6f} "
            f"n_pmt={summary.output} efficiency={summary.efficiency:.8f} "
            f"normalized={summary.efficiency / reference:.8f} "
            f"top_interactions={summary.top_interactions} "
            f"bottom_interactions={summary.bottom_interactions} "
            f"side_interactions={summary.side_interactions} "
            "accounting=closed status=PASS"
        )
    print(
        "[b1-check] six_state_switching=true shared_sigma_alpha=true "
        "all_polished_reproducible=true experimental_order_tested=false "
        "status=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
