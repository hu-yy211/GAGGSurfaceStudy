#!/usr/bin/env python3
"""Validate A4 LUT switching, photon accounting and reproducibility."""

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path


SURFACES = (
    "polishedvm2000air",
    "polishedtioair",
    "groundvm2000air",
    "groundtioair",
)

EXPECTED_COLUMNS = [
    "event_id",
    "source_x_mm",
    "source_y_mm",
    "source_z_mm",
    "stage_a_surface",
    "generated",
    "output",
    "crystal_absorption",
    "reflector_absorption",
    "other_absorption",
    "surface_absorption",
    "other_world_exit",
    "world_exit",
    "bulk_absorption",
    "lut_interactions",
    "unclassified",
]

COUNT_COLUMNS = EXPECTED_COLUMNS[5:]


@dataclass(frozen=True)
class Summary:
    surface: str
    rows: tuple[tuple[str, ...], ...]
    events: int
    generated: int
    output: int
    crystal_absorption: int
    reflector_absorption: int
    other_absorption: int
    surface_absorption: int
    other_world_exit: int
    lut_interactions: int

    @property
    def efficiency(self) -> float:
        return self.output / self.generated

    @property
    def standard_error(self) -> float:
        probability = self.efficiency
        return math.sqrt(probability * (1.0 - probability) / self.generated)


def load_summary(
    path: Path, expected_surface: str, expected_events: int = 50
) -> Summary:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(f"unexpected columns in {path}: {reader.fieldnames}")
        raw_rows = list(reader)

    if len(raw_rows) != expected_events:
        raise ValueError(
            f"expected {expected_events} events in {path}, found {len(raw_rows)}"
        )

    totals = {key: 0 for key in COUNT_COLUMNS}
    canonical_rows: list[tuple[str, ...]] = []
    for expected_event_id, row in enumerate(raw_rows):
        if int(row["event_id"]) != expected_event_id:
            raise ValueError(f"event IDs are not contiguous in {path}")
        source = tuple(
            float(row[key])
            for key in ("source_x_mm", "source_y_mm", "source_z_mm")
        )
        if source != (0.0, 0.0, 0.0):
            raise ValueError(f"unexpected source in {path}: {source}")
        if row["stage_a_surface"] != expected_surface:
            raise ValueError(
                f"surface mismatch in {path}: {row['stage_a_surface']}"
            )

        values = {key: int(row[key]) for key in COUNT_COLUMNS}
        if values["generated"] != 200:
            raise ValueError(f"unexpected photons/event in {path}: {values}")
        if values["world_exit"] != (
            values["output"] + values["other_world_exit"]
        ):
            raise ValueError(f"world-exit subtotal failed in {path}: {values}")
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
        if classified + values["unclassified"] != values["generated"]:
            raise ValueError(f"photon accounting failed in {path}: {values}")
        if values["unclassified"] != 0:
            raise ValueError(f"unclassified photon in {path}: {values}")

        for key, value in values.items():
            totals[key] += value
        canonical_rows.append(tuple(row[key] for key in EXPECTED_COLUMNS))

    if totals["lut_interactions"] <= 0:
        raise ValueError(f"LUT boundary was never invoked in {path}")

    return Summary(
        surface=expected_surface,
        rows=tuple(canonical_rows),
        events=len(raw_rows),
        generated=totals["generated"],
        output=totals["output"],
        crystal_absorption=totals["crystal_absorption"],
        reflector_absorption=totals["reflector_absorption"],
        other_absorption=totals["other_absorption"],
        surface_absorption=totals["surface_absorption"],
        other_world_exit=totals["other_world_exit"],
        lut_interactions=totals["lut_interactions"],
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    args = parser.parse_args()

    summaries = {
        surface: load_summary(args.input_dir / f"{surface}.csv", surface)
        for surface in SURFACES
    }
    repeat = load_summary(
        args.input_dir / "polishedvm2000air_repeat.csv",
        "polishedvm2000air",
    )
    reproducible = summaries["polishedvm2000air"].rows == repeat.rows
    if not reproducible:
        raise ValueError("surface switch-back did not reproduce the first run")

    for surface in SURFACES:
        summary = summaries[surface]
        print(
            f"[a4-check] surface={surface} generated={summary.generated} "
            f"efficiency={summary.efficiency:.6f} "
            f"surface_absorption={summary.surface_absorption} "
            f"lut_interactions={summary.lut_interactions} status=PASS"
        )
    print("[a4-check] switch_back_exact_match=true status=PASS")
    print("[a4-check] ordering_criterion=DEFERRED_TO_A7")
    print("[a4-check] lut_switching status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
