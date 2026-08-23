#!/usr/bin/env python3
"""Validate A5 scintillation yield, accounting and timing independence."""

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
EXPECTED_YIELD_PER_KEV = 54.0


@dataclass(frozen=True)
class Summary:
    path: Path
    energy_kev: float
    events: int
    edep_kev: float
    scintillation: int
    generated: int
    output: int
    lut_interactions: int

    @property
    def yield_per_mev(self) -> float:
        return self.scintillation / (self.edep_kev / 1000.0)

    @property
    def output_efficiency(self) -> float:
        return self.output / self.generated


def load_summary(
    path: Path, expected_energy_kev: float, expected_events: int = 20
) -> Summary:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(f"unexpected columns in {path}: {reader.fieldnames}")
        rows = list(reader)

    if len(rows) != expected_events:
        raise ValueError(
            f"expected {expected_events} events in {path}, found {len(rows)}"
        )

    totals = {key: 0 for key in COUNT_COLUMNS}
    total_edep = 0.0
    for expected_event_id, row in enumerate(rows):
        if int(row["event_id"]) != expected_event_id:
            raise ValueError(f"event IDs are not contiguous in {path}")
        source = tuple(
            float(row[key])
            for key in ("source_x_mm", "source_y_mm", "source_z_mm")
        )
        if source != (0.0, 0.0, 0.0):
            raise ValueError(f"unexpected source position in {path}: {source}")
        if row["source_particle"] != "electron":
            raise ValueError(f"unexpected source particle in {path}")
        if abs(float(row["source_energy_keV"]) - expected_energy_kev) > 1.0e-9:
            raise ValueError(f"unexpected source energy in {path}")
        if row["stage_a_surface"] != "polishedvm2000air":
            raise ValueError(f"unexpected LUT finish in {path}")

        edep = float(row["edep_keV"])
        if abs(edep - expected_energy_kev) > 1.0e-6:
            raise ValueError(f"incomplete controlled energy deposit in {path}: {edep}")
        total_edep += edep

        values = {key: int(row[key]) for key in COUNT_COLUMNS}
        if values["scintillation"] != values["generated"]:
            raise ValueError(f"non-scintillation optical photon in {path}: {values}")
        expected_generated = round(edep * EXPECTED_YIELD_PER_KEV)
        if abs(values["generated"] - expected_generated) > 1:
            raise ValueError(f"incorrect event light yield in {path}: {values}")
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

    if totals["lut_interactions"] <= 0:
        raise ValueError(f"A5 did not exercise the LUT boundary in {path}")

    return Summary(
        path=path,
        energy_kev=expected_energy_kev,
        events=len(rows),
        edep_kev=total_edep,
        scintillation=totals["scintillation"],
        generated=totals["generated"],
        output=totals["output"],
        lut_interactions=totals["lut_interactions"],
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    args = parser.parse_args()

    linear = [
        load_summary(args.input_dir / f"energy_{energy}kev.csv", float(energy))
        for energy in (10, 20, 40)
    ]
    slow = load_summary(args.input_dir / "energy_20kev_slow.csv", 20.0)
    fast = linear[1]

    numerator = sum(item.edep_kev * item.generated for item in linear)
    denominator = sum(item.edep_kev**2 for item in linear)
    slope_per_kev = numerator / denominator
    slope_relative_error = abs(slope_per_kev - EXPECTED_YIELD_PER_KEV) / 54.0
    if slope_relative_error > 1.0e-6:
        raise ValueError(f"incorrect light-yield slope: {slope_per_kev}")

    timing_relative_difference = abs(
        slow.yield_per_mev - fast.yield_per_mev
    ) / 54000.0
    if timing_relative_difference > 1.0e-4:
        raise ValueError(
            "integrated light yield depends on time constant: "
            f"relative difference={timing_relative_difference}"
        )
    output_combined_error = math.hypot(
        math.sqrt(
            fast.output_efficiency
            * (1.0 - fast.output_efficiency)
            / fast.generated
        ),
        math.sqrt(
            slow.output_efficiency
            * (1.0 - slow.output_efficiency)
            / slow.generated
        ),
    )
    output_difference_sigma = abs(
        fast.output_efficiency - slow.output_efficiency
    ) / output_combined_error
    if output_difference_sigma > 3.0:
        raise ValueError(
            "collected fraction depends significantly on time constant: "
            f"difference={output_difference_sigma} sigma"
        )

    for summary in linear:
        print(
            f"[a5-check] energy_keV={summary.energy_kev:g} "
            f"edep_keV={summary.edep_kev:g} generated={summary.generated} "
            f"yield_photons_per_MeV={summary.yield_per_mev:.6f} "
            f"accounting=closed status=PASS"
        )
    print(
        f"[a5-check] linear_slope_photons_per_MeV="
        f"{slope_per_kev * 1000.0:.6f} relative_error="
        f"{slope_relative_error:.3e} status=PASS"
    )
    print(
        f"[a5-check] time_fast_ns=62.53 yield={fast.yield_per_mev:.6f} "
        f"time_slow_ns=190.89 yield={slow.yield_per_mev:.6f} "
        f"relative_difference={timing_relative_difference:.3e} "
        f"output_difference_sigma={output_difference_sigma:.3f} status=PASS"
    )
    print("[a5-check] scintillation status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
