#!/usr/bin/env python3
"""Validate A3 optical transport, reproducibility and position scans."""

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path


EXPECTED_COLUMNS = [
    "event_id",
    "source_x_mm",
    "source_y_mm",
    "source_z_mm",
    "source_particle",
    "source_energy_keV",
    "stage_a_surface",
    "stage_b_surface_state",
    "stage_b_sigma_alpha_rad",
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
    "top_surface_interactions",
    "bottom_surface_interactions",
    "side_surface_interactions",
    "unclassified",
]

COUNT_COLUMNS = EXPECTED_COLUMNS[EXPECTED_COLUMNS.index("scintillation") :]


@dataclass(frozen=True)
class Summary:
    path: Path
    rows: tuple[tuple[str, ...], ...]
    events: int
    generated: int
    output: int
    crystal_absorption: int
    reflector_absorption: int
    surface_absorption: int
    other_absorption: int
    other_world_exit: int
    lut_interactions: int

    @property
    def efficiency(self) -> float:
        return self.output / self.generated

    @property
    def standard_error(self) -> float:
        probability = self.efficiency
        return math.sqrt(probability * (1.0 - probability) / self.generated)


def load_summary(path: Path, expected_z_mm: float) -> Summary:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(f"unexpected columns in {path}: {reader.fieldnames}")
        raw_rows = list(reader)

    if not raw_rows:
        raise ValueError(f"no event rows in {path}")

    totals = {key: 0 for key in COUNT_COLUMNS}
    canonical_rows: list[tuple[str, ...]] = []
    expected_generated = None
    for expected_event_id, row in enumerate(raw_rows):
        event_id = int(row["event_id"])
        if event_id != expected_event_id:
            raise ValueError(
                f"event id mismatch in {path}: {event_id} != {expected_event_id}"
            )
        source = (
            float(row["source_x_mm"]),
            float(row["source_y_mm"]),
            float(row["source_z_mm"]),
        )
        if source != (0.0, 0.0, expected_z_mm):
            raise ValueError(f"unexpected source in {path}: {source}")
        if row["stage_a_surface"] != "none":
            raise ValueError(f"unexpected A3 surface in {path}")
        if row["source_particle"] != "optical":
            raise ValueError(f"unexpected A3 source in {path}")
        if not 0.0 < float(row["source_energy_keV"]) < 0.01:
            raise ValueError(f"unexpected A3 source energy in {path}")
        if float(row["edep_keV"]) != 0.0:
            raise ValueError(f"A3 optical source deposited energy in {path}")

        values = {key: int(row[key]) for key in COUNT_COLUMNS}
        if expected_generated is None:
            expected_generated = values["generated"]
        if values["generated"] != expected_generated:
            raise ValueError(f"generated count changed within {path}")
        if values["world_exit"] != (
            values["output"] + values["other_world_exit"]
        ):
            raise ValueError(f"world-exit subtotal failed in {path}: {values}")
        if values["bulk_absorption"] != (
            values["crystal_absorption"]
            + values["reflector_absorption"]
            + values["other_absorption"]
        ):
            raise ValueError(
                f"bulk-absorption subtotal failed in {path}: {values}"
            )
        classified = (
            values["world_exit"]
            + values["bulk_absorption"]
            + values["surface_absorption"]
        )
        if classified + values["unclassified"] != values["generated"]:
            raise ValueError(f"photon accounting failed in {path}: {values}")
        if values["unclassified"] != 0:
            raise ValueError(f"unclassified photon in {path}: {values}")
        if values["surface_absorption"] != 0 or values["lut_interactions"] != 0:
            raise ValueError(f"A3 unexpectedly invoked LUT transport in {path}")
        if values["scintillation"] != 0:
            raise ValueError(f"A3 unexpectedly produced scintillation in {path}")

        for key, value in values.items():
            totals[key] += value
        canonical_rows.append(tuple(row[key] for key in EXPECTED_COLUMNS))

    return Summary(
        path=path,
        rows=tuple(canonical_rows),
        events=len(raw_rows),
        generated=totals["generated"],
        output=totals["output"],
        crystal_absorption=totals["crystal_absorption"],
        reflector_absorption=totals["reflector_absorption"],
        surface_absorption=totals["surface_absorption"],
        other_absorption=totals["other_absorption"],
        other_world_exit=totals["other_world_exit"],
        lut_interactions=totals["lut_interactions"],
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--center-a", required=True, type=Path)
    parser.add_argument("--center-b", required=True, type=Path)
    parser.add_argument("--no-absorption", required=True, type=Path)
    parser.add_argument("--z-m10", required=True, type=Path)
    parser.add_argument("--z-m5", required=True, type=Path)
    parser.add_argument("--z-p5", required=True, type=Path)
    parser.add_argument("--z-p10", required=True, type=Path)
    args = parser.parse_args()

    center_a = load_summary(args.center_a, 0.0)
    center_b = load_summary(args.center_b, 0.0)
    no_absorption = load_summary(args.no_absorption, 0.0)
    scan = [
        (-10.0, load_summary(args.z_m10, -10.0)),
        (-5.0, load_summary(args.z_m5, -5.0)),
        (0.0, center_a),
        (5.0, load_summary(args.z_p5, 5.0)),
        (10.0, load_summary(args.z_p10, 10.0)),
    ]

    for summary in [center_b, no_absorption, *(item[1] for item in scan)]:
        if summary.events != 100 or summary.generated != 20000:
            raise ValueError(
                f"unexpected fixed source count in {summary.path}: "
                f"events={summary.events}, generated={summary.generated}"
            )

    reproducible = center_a.rows == center_b.rows
    if not reproducible:
        raise ValueError("fixed-seed center runs are not identical")

    if center_a.crystal_absorption <= 0:
        raise ValueError("enabled GAGG absorption produced no crystal losses")
    if no_absorption.crystal_absorption != 0:
        raise ValueError("disabled GAGG absorption still produced crystal losses")
    combined_error = math.hypot(
        center_a.standard_error, no_absorption.standard_error
    )
    absorption_monotonic = (
        no_absorption.efficiency + 3.0 * combined_error
        >= center_a.efficiency
    )
    if not absorption_monotonic:
        raise ValueError("disabling GAGG absorption significantly lowered output")

    reversal_significances = []
    for (_, left), (_, right) in zip(scan, scan[1:]):
        difference_error = math.hypot(
            left.standard_error, right.standard_error
        )
        reversal_significances.append(
            (right.efficiency - left.efficiency) / difference_error
        )
    smooth = (
        max(reversal_significances) < 3.0
        and scan[0][1].efficiency > scan[-1][1].efficiency
    )
    if not smooth:
        raise ValueError(
            "position scan is not smooth: "
            f"reversal significance={reversal_significances}"
        )

    print(
        f"[a3] reproducibility rows={center_a.events} "
        "exact_match=true status=PASS"
    )
    print(
        f"[a3] absorption_on={center_a.efficiency:.6f} "
        f"absorption_off={no_absorption.efficiency:.6f} "
        f"three_sigma={3.0 * combined_error:.6f} status=PASS"
    )
    print(
        "[a3] position_scan "
        + " ".join(
            f"z={position:g}mm:{summary.efficiency:.6f}"
            for position, summary in scan
        )
        + f" max_upward_reversal_sigma={max(reversal_significances):.3f} "
        "status=PASS"
    )
    print("[a3] accounting=closed unclassified=0")
    print("[a3] transport status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
