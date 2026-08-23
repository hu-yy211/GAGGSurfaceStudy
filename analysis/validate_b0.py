#!/usr/bin/env python3
"""Validate B0 all-polished optical transport and photon accounting."""

import argparse
import csv
from pathlib import Path

from validate_a0_csv import COUNT_COLUMNS, EXPECTED_COLUMNS


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--expect-events", type=int, default=50)
    parser.add_argument("--photons-per-event", type=int, default=100)
    args = parser.parse_args()

    with args.input.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(f"unexpected B0 columns: {reader.fieldnames}")
        rows = list(reader)
    if len(rows) != args.expect_events:
        raise ValueError(
            f"expected {args.expect_events} B0 events, found {len(rows)}"
        )

    totals = {key: 0 for key in COUNT_COLUMNS}
    for event_id, row in enumerate(rows):
        if int(row["event_id"]) != event_id:
            raise ValueError("B0 event IDs are not contiguous")
        if row["source_particle"] != "optical":
            raise ValueError("B0 transport must use optical primaries")
        if row["stage_a_surface"] != "none":
            raise ValueError("B0 must not use a Stage A LUT")
        if tuple(float(row[key]) for key in EXPECTED_COLUMNS[1:4]) != (
            0.0,
            0.0,
            0.0,
        ):
            raise ValueError("B0 source is not at the crystal center")
        if float(row["edep_keV"]) != 0.0 or int(row["scintillation"]) != 0:
            raise ValueError("B0 optical primaries produced energy deposit")
        values = {key: int(row[key]) for key in COUNT_COLUMNS}
        if values["generated"] != args.photons_per_event:
            raise ValueError("incorrect B0 generated-photon count")
        if values["world_exit"] != (
            values["output"] + values["other_world_exit"]
        ):
            raise ValueError("B0 world-exit subtotal failed")
        if values["bulk_absorption"] != (
            values["crystal_absorption"]
            + values["reflector_absorption"]
            + values["other_absorption"]
        ):
            raise ValueError("B0 bulk-absorption subtotal failed")
        classified = (
            values["world_exit"]
            + values["bulk_absorption"]
            + values["surface_absorption"]
        )
        if classified != values["generated"] or values["unclassified"] != 0:
            raise ValueError("B0 photon accounting failed")
        for key, value in values.items():
            totals[key] += value

    generated = totals["generated"]
    efficiency = totals["output"] / generated
    if totals["output"] <= 0:
        raise ValueError("B0 did not deliver photons to the PMT window")
    if totals["surface_absorption"] <= 0:
        raise ValueError("B0 did not exercise ESR/black optical surfaces")
    if totals["lut_interactions"] <= 0:
        raise ValueError("B0 did not exercise configured border surfaces")
    if totals["reflector_absorption"] != 0:
        raise ValueError("B0 unexpectedly used Stage A reflector volumes")

    print(
        f"[b0-check] events={len(rows)} generated={generated} "
        f"n_pmt={totals['output']} efficiency={efficiency:.8f} "
        f"surface_absorption={totals['surface_absorption']} "
        f"border_interactions={totals['lut_interactions']} "
        "accounting=closed status=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
