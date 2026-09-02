#!/usr/bin/env python3
"""Validate the small independent photon-audit CSV plumbing test."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from b7_6_common import AUDIT_COLUMNS


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--expect-events", type=int, default=20)
    args = parser.parse_args()
    with args.events.open(newline="", encoding="utf-8") as stream:
        events = list(csv.DictReader(stream))
    with args.audit.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != AUDIT_COLUMNS:
            raise ValueError("B7.6 plumbing audit schema mismatch")
        audits = list(reader)
    if len(events) != args.expect_events or len(audits) != args.expect_events:
        raise ValueError("B7.6 plumbing row count mismatch")
    total_output = total_path = output_path = 0.0
    for event_id, (event, audit) in enumerate(zip(events, audits)):
        if int(event["event_id"]) != event_id or int(audit["event_id"]) != event_id:
            raise ValueError("B7.6 plumbing event IDs are not aligned")
        if int(audit["generated"]) != int(event["generated"]):
            raise ValueError("B7.6 plumbing generated mismatch")
        if int(audit["output"]) != int(event["output"]):
            raise ValueError("B7.6 plumbing output mismatch")
        face = int(audit["output_face_interactions"])
        subtotal = sum(int(audit[key]) for key in (
            "output_top_interactions", "output_bottom_interactions",
            "output_side_interactions",
        ))
        if face != subtotal:
            raise ValueError("B7.6 plumbing output-face subtotal mismatch")
        total_output += int(audit["output"])
        total_path += float(audit["total_optical_path_mm"])
        output_path += float(audit["output_optical_path_mm"])
    if total_output <= 0 or total_path <= 0.0 or output_path <= 0.0:
        raise ValueError("B7.6 plumbing did not exercise transport diagnostics")
    print(
        f"[b7.6-plumbing] rows={len(audits)} output={int(total_output)} "
        "counts=matched paths=positive face_subtotals=closed status=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
