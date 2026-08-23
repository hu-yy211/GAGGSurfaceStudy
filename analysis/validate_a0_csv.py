#!/usr/bin/env python3
"""Validate the A0 event-level CSV schema and photon accounting."""

import argparse
import csv
from pathlib import Path


EXPECTED_COLUMNS = [
    "event_id",
    "generated",
    "world_exit",
    "bulk_absorption",
    "unclassified",
]


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
        values = {key: int(row[key]) for key in EXPECTED_COLUMNS}
        if values["event_id"] != expected_id:
            raise ValueError(
                f"event id mismatch: expected {expected_id}, "
                f"found {values['event_id']}"
            )
        classified = values["world_exit"] + values["bulk_absorption"]
        if values["generated"] != 1 or classified != 1:
            raise ValueError(f"photon accounting failed: {values}")
        if values["unclassified"] != 0:
            raise ValueError(f"unclassified photon: {values}")

    print(f"[csv-check] rows={len(rows)} accounting=closed status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
