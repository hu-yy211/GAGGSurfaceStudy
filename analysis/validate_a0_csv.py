#!/usr/bin/env python3
"""Validate the A0 event-level CSV schema and photon accounting."""

import argparse
import csv
from pathlib import Path


EXPECTED_COLUMNS = [
    "event_id",
    "source_x_mm",
    "source_y_mm",
    "source_z_mm",
    "source_particle",
    "source_energy_keV",
    "stage_a_surface",
    "edep_keV",
    "scintillation",
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

COUNT_COLUMNS = EXPECTED_COLUMNS[8:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--expect-events", required=True, type=int)
    args = parser.parse_args()

    with args.input.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(
                f"unexpected columns: {reader.fieldnames}; "
                f"expected {EXPECTED_COLUMNS}"
            )
        rows = list(reader)

    if len(rows) != args.expect_events:
        raise ValueError(
            f"expected {args.expect_events} rows, found {len(rows)}"
        )

    for expected_id, row in enumerate(rows):
        event_id = int(row["event_id"])
        values = {key: int(row[key]) for key in COUNT_COLUMNS}
        if event_id != expected_id:
            raise ValueError(
                f"event id mismatch: expected {expected_id}, "
                f"found {event_id}"
            )
        source = tuple(float(row[key]) for key in EXPECTED_COLUMNS[1:4])
        if source != (0.0, 0.0, 0.0):
            raise ValueError(f"unexpected A0 source position: {source}")
        if row["stage_a_surface"] != "none":
            raise ValueError(f"unexpected A0 surface: {row['stage_a_surface']}")
        if row["source_particle"] != "optical":
            raise ValueError(f"unexpected A0 source: {row['source_particle']}")
        if not 0.0 < float(row["source_energy_keV"]) < 0.01:
            raise ValueError(f"unexpected A0 source energy: {row}")
        if float(row["edep_keV"]) != 0.0 or values["scintillation"] != 0:
            raise ValueError(f"A0 unexpectedly produced scintillation: {row}")
        if values["world_exit"] != (
            values["output"] + values["other_world_exit"]
        ):
            raise ValueError(f"world-exit subtotal failed: {values}")
        if values["bulk_absorption"] != (
            values["crystal_absorption"]
            + values["reflector_absorption"]
            + values["other_absorption"]
        ):
            raise ValueError(f"bulk-absorption subtotal failed: {values}")
        classified = (
            values["world_exit"]
            + values["bulk_absorption"]
            + values["surface_absorption"]
        )
        if values["generated"] != 1 or classified != 1:
            raise ValueError(f"photon accounting failed: {values}")
        if values["surface_absorption"] != 0 or values["lut_interactions"] != 0:
            raise ValueError(f"A0 unexpectedly invoked LUT transport: {values}")
        if values["unclassified"] != 0:
            raise ValueError(f"unclassified photon: {values}")

    print(f"[csv-check] rows={len(rows)} accounting=closed status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
