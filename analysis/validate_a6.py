#!/usr/bin/env python3
"""Validate the A6 normally incident 662 keV gamma sample."""

import argparse
import csv
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
GAMMA_ENERGY_KEV = 662.0
EXPECTED_YIELD_PER_KEV = 54.0
FULL_ENERGY_HALF_WIDTH_KEV = 0.5


@dataclass(frozen=True)
class GammaSummary:
    path: Path
    events: int
    zero_edep_events: int
    partial_energy_events: int
    full_energy_events: int
    total_edep_kev: float
    total_generated: int
    full_edep_kev: float
    full_generated: int

    @property
    def total_yield_per_mev(self) -> float:
        return self.total_generated / (self.total_edep_kev / 1000.0)

    @property
    def full_energy_yield_per_mev(self) -> float:
        return self.full_generated / (self.full_edep_kev / 1000.0)


def load_gamma_sample(path: Path, expected_events: int = 100) -> GammaSummary:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(f"unexpected columns in {path}: {reader.fieldnames}")
        rows = list(reader)

    if len(rows) != expected_events:
        raise ValueError(
            f"expected {expected_events} events in {path}, found {len(rows)}"
        )

    zero_edep_events = 0
    partial_energy_events = 0
    full_energy_events = 0
    total_edep_kev = 0.0
    total_generated = 0
    full_edep_kev = 0.0
    full_generated = 0

    for expected_event_id, row in enumerate(rows):
        if int(row["event_id"]) != expected_event_id:
            raise ValueError(f"event IDs are not contiguous in {path}")
        source = tuple(
            float(row[key])
            for key in ("source_x_mm", "source_y_mm", "source_z_mm")
        )
        if source != (0.0, 0.0, 14.7):
            raise ValueError(f"unexpected gamma source position: {source}")
        if row["source_particle"] != "gamma":
            raise ValueError(f"unexpected source particle in {path}")
        if abs(float(row["source_energy_keV"]) - GAMMA_ENERGY_KEV) > 1.0e-9:
            raise ValueError(f"unexpected source energy in {path}")
        if row["stage_a_surface"] != "polishedvm2000air":
            raise ValueError(f"unexpected LUT finish in {path}")

        edep_kev = float(row["edep_keV"])
        if edep_kev < 0.0 or edep_kev > GAMMA_ENERGY_KEV + 1.0e-6:
            raise ValueError(f"unphysical gamma energy deposit: {edep_kev}")
        values = {key: int(row[key]) for key in COUNT_COLUMNS}
        if values["scintillation"] != values["generated"]:
            raise ValueError(f"non-scintillation optical photon: {values}")
        expected_generated = edep_kev * EXPECTED_YIELD_PER_KEV
        if abs(values["generated"] - expected_generated) > 4.0:
            raise ValueError(
                "event light yield is inconsistent with stepwise photon "
                f"rounding: edep={edep_kev}, generated={values['generated']}"
            )
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
        if classified + values["unclassified"] != values["generated"]:
            raise ValueError(f"photon accounting failed: {values}")
        if values["unclassified"] != 0:
            raise ValueError(f"unclassified optical photon: {values}")

        total_edep_kev += edep_kev
        total_generated += values["generated"]
        if edep_kev == 0.0:
            zero_edep_events += 1
            if any(values[key] != 0 for key in COUNT_COLUMNS):
                raise ValueError(
                    f"zero-Edep event created or transported light: {values}"
                )
        elif abs(edep_kev - GAMMA_ENERGY_KEV) <= FULL_ENERGY_HALF_WIDTH_KEV:
            full_energy_events += 1
            full_edep_kev += edep_kev
            full_generated += values["generated"]
        else:
            partial_energy_events += 1

    if zero_edep_events == 0:
        raise ValueError("the A6 sample has no zero-Edep event")
    if partial_energy_events == 0:
        raise ValueError("the A6 sample has no partial-energy event")
    if full_energy_events == 0:
        raise ValueError("the A6 sample has no 662 keV full-energy event")

    summary = GammaSummary(
        path=path,
        events=len(rows),
        zero_edep_events=zero_edep_events,
        partial_energy_events=partial_energy_events,
        full_energy_events=full_energy_events,
        total_edep_kev=total_edep_kev,
        total_generated=total_generated,
        full_edep_kev=full_edep_kev,
        full_generated=full_generated,
    )
    for label, measured_yield in (
        ("all depositing", summary.total_yield_per_mev),
        ("full-energy", summary.full_energy_yield_per_mev),
    ):
        relative_error = abs(measured_yield - 54000.0) / 54000.0
        if relative_error > 1.0e-4:
            raise ValueError(
                f"{label} gamma yield mismatch: yield={measured_yield}, "
                f"relative_error={relative_error}"
            )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--expect-events", type=int, default=100)
    args = parser.parse_args()

    summary = load_gamma_sample(args.input, args.expect_events)
    full_relative_error = abs(summary.full_energy_yield_per_mev - 54000.0) / 54000.0
    total_relative_error = abs(summary.total_yield_per_mev - 54000.0) / 54000.0
    print(
        f"[a6-check] events={summary.events} "
        f"zero_edep={summary.zero_edep_events} "
        f"partial_energy={summary.partial_energy_events} "
        f"full_energy={summary.full_energy_events} status=PASS"
    )
    print(
        f"[a6-check] full_energy_gate_keV="
        f"{GAMMA_ENERGY_KEV - FULL_ENERGY_HALF_WIDTH_KEV:g}:"
        f"{GAMMA_ENERGY_KEV + FULL_ENERGY_HALF_WIDTH_KEV:g} "
        f"yield_photons_per_MeV={summary.full_energy_yield_per_mev:.6f} "
        f"relative_error={full_relative_error:.3e} status=PASS"
    )
    print(
        f"[a6-check] all_depositing_yield_photons_per_MeV="
        f"{summary.total_yield_per_mev:.6f} "
        f"relative_error={total_relative_error:.3e} status=PASS"
    )
    print(
        f"[a6-check] zero_edep_events={summary.zero_edep_events} "
        "generated=0 status=PASS"
    )
    print("[a6-check] gamma status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
