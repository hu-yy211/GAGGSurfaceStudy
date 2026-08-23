#!/usr/bin/env python3
"""Validate paired A7 full-energy events and the Fig. 4 LUT ordering."""

import argparse
import csv
import math
import statistics
from dataclasses import dataclass
from pathlib import Path

from validate_a6 import (
    COUNT_COLUMNS,
    EXPECTED_COLUMNS,
    EXPECTED_YIELD_PER_KEV,
    FULL_ENERGY_HALF_WIDTH_KEV,
    GAMMA_ENERGY_KEV,
)


SURFACES = (
    "polishedvm2000air",
    "polishedtioair",
    "groundvm2000air",
    "groundtioair",
)
FIG4_ORDER = (
    "groundtioair",
    "polishedtioair",
    "polishedvm2000air",
    "groundvm2000air",
)
Z95 = 1.959963984540054


@dataclass(frozen=True)
class FullEnergyEvent:
    event_id: int
    source_x_mm: float
    source_y_mm: float
    source_z_mm: float
    edep_kev: float
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
    def paired_signature(self) -> tuple[float, float, float, float, int]:
        return (
            self.source_x_mm,
            self.source_y_mm,
            self.source_z_mm,
            self.edep_kev,
            self.generated,
        )


@dataclass(frozen=True)
class SurfaceSummary:
    surface: str
    events: int
    zero_edep_events: int
    partial_energy_events: int
    full_events: tuple[FullEnergyEvent, ...]

    @property
    def efficiencies(self) -> tuple[float, ...]:
        return tuple(event.efficiency for event in self.full_events)

    @property
    def mean_efficiency(self) -> float:
        return statistics.fmean(self.efficiencies)

    @property
    def standard_error(self) -> float:
        return statistics.stdev(self.efficiencies) / math.sqrt(
            len(self.full_events)
        )

    @property
    def ci95(self) -> tuple[float, float]:
        half_width = Z95 * self.standard_error
        return (
            self.mean_efficiency - half_width,
            self.mean_efficiency + half_width,
        )

    @property
    def mean_output(self) -> float:
        return statistics.fmean(event.output for event in self.full_events)

    @property
    def total_generated(self) -> int:
        return sum(event.generated for event in self.full_events)

    @property
    def total_output(self) -> int:
        return sum(event.output for event in self.full_events)


def _validate_accounting(values: dict[str, int], path: Path) -> None:
    if values["scintillation"] != values["generated"]:
        raise ValueError(f"non-scintillation optical photon in {path}")
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
    if classified + values["unclassified"] != values["generated"]:
        raise ValueError(f"photon accounting failed in {path}")
    if values["unclassified"] != 0:
        raise ValueError(f"unclassified photon in {path}")


def load_surface(
    path: Path, expected_surface: str, expected_events: int = 100
) -> SurfaceSummary:
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
    full_events: list[FullEnergyEvent] = []
    for expected_event_id, row in enumerate(rows):
        if int(row["event_id"]) != expected_event_id:
            raise ValueError(f"event IDs are not contiguous in {path}")
        if row["stage_a_surface"] != expected_surface:
            raise ValueError(f"surface mismatch in {path}")
        if row["source_particle"] != "gamma":
            raise ValueError(f"unexpected source particle in {path}")
        if abs(float(row["source_energy_keV"]) - GAMMA_ENERGY_KEV) > 1.0e-9:
            raise ValueError(f"unexpected source energy in {path}")
        source_x = float(row["source_x_mm"])
        source_y = float(row["source_y_mm"])
        source_z = float(row["source_z_mm"])
        if math.hypot(source_x, source_y) > 12.7 + 1.0e-9:
            raise ValueError(f"gamma source is outside beam disk in {path}")
        if abs(source_z - 14.7) > 1.0e-9:
            raise ValueError(f"unexpected source z in {path}")

        edep_kev = float(row["edep_keV"])
        if edep_kev < 0.0 or edep_kev > GAMMA_ENERGY_KEV + 1.0e-6:
            raise ValueError(f"unphysical energy deposit in {path}")
        values = {key: int(row[key]) for key in COUNT_COLUMNS}
        _validate_accounting(values, path)
        if abs(values["generated"] - edep_kev * EXPECTED_YIELD_PER_KEV) > 4.0:
            raise ValueError(f"incorrect scintillation yield in {path}")

        if edep_kev == 0.0:
            zero_edep_events += 1
            if any(values[key] != 0 for key in COUNT_COLUMNS):
                raise ValueError(f"zero-Edep event produced light in {path}")
        elif abs(edep_kev - GAMMA_ENERGY_KEV) <= FULL_ENERGY_HALF_WIDTH_KEV:
            full_events.append(
                FullEnergyEvent(
                    event_id=expected_event_id,
                    source_x_mm=source_x,
                    source_y_mm=source_y,
                    source_z_mm=source_z,
                    edep_kev=edep_kev,
                    generated=values["generated"],
                    output=values["output"],
                    crystal_absorption=values["crystal_absorption"],
                    reflector_absorption=values["reflector_absorption"],
                    surface_absorption=values["surface_absorption"],
                    other_absorption=values["other_absorption"],
                    other_world_exit=values["other_world_exit"],
                    lut_interactions=values["lut_interactions"],
                )
            )
        else:
            partial_energy_events += 1

    if zero_edep_events == 0 or partial_energy_events == 0:
        raise ValueError(f"missing gamma control class in {path}")
    if len(full_events) < 10:
        raise ValueError(f"too few full-energy events in {path}: {len(full_events)}")
    if sum(event.lut_interactions for event in full_events) <= 0:
        raise ValueError(f"LUT boundary not exercised in {path}")
    return SurfaceSummary(
        surface=expected_surface,
        events=len(rows),
        zero_edep_events=zero_edep_events,
        partial_energy_events=partial_energy_events,
        full_events=tuple(full_events),
    )


def load_comparison(
    input_dir: Path, expected_events: int = 100
) -> dict[str, SurfaceSummary]:
    summaries = {
        surface: load_surface(
            input_dir / f"{surface}.csv", surface, expected_events
        )
        for surface in SURFACES
    }
    reference = summaries[SURFACES[0]].full_events
    reference_ids = tuple(event.event_id for event in reference)
    reference_signatures = tuple(event.paired_signature for event in reference)
    for surface in SURFACES[1:]:
        candidate = summaries[surface].full_events
        if tuple(event.event_id for event in candidate) != reference_ids:
            raise ValueError(f"full-energy event IDs are not paired for {surface}")
        if tuple(event.paired_signature for event in candidate) != reference_signatures:
            raise ValueError(f"event source/Edep/generated mismatch for {surface}")
    return summaries


def ordering_matches(summaries: dict[str, SurfaceSummary]) -> bool:
    values = [summaries[surface].mean_efficiency for surface in FIG4_ORDER]
    return all(left > right for left, right in zip(values, values[1:]))


def paired_difference(
    left: SurfaceSummary, right: SurfaceSummary
) -> tuple[float, float, float]:
    differences = [
        left_event.efficiency - right_event.efficiency
        for left_event, right_event in zip(left.full_events, right.full_events)
    ]
    mean_difference = statistics.fmean(differences)
    standard_error = statistics.stdev(differences) / math.sqrt(len(differences))
    half_width = Z95 * standard_error
    return mean_difference, mean_difference - half_width, mean_difference + half_width


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--expect-events", type=int, default=100)
    args = parser.parse_args()

    summaries = load_comparison(args.input_dir, args.expect_events)
    for surface in SURFACES:
        summary = summaries[surface]
        ci_low, ci_high = summary.ci95
        print(
            f"[a7-check] surface={surface} full_events="
            f"{len(summary.full_events)} mean_efficiency="
            f"{summary.mean_efficiency:.8f} ci95="
            f"[{ci_low:.8f},{ci_high:.8f}] mean_output="
            f"{summary.mean_output:.3f} accounting=closed status=PASS"
        )
    print("[a7-check] paired_source_edep_generated=true status=PASS")
    for left_name, right_name in zip(FIG4_ORDER, FIG4_ORDER[1:]):
        difference, ci_low, ci_high = paired_difference(
            summaries[left_name], summaries[right_name]
        )
        print(
            f"[a7-check] expected_pair={left_name}>{right_name} "
            f"mean_difference={difference:.8f} ci95="
            f"[{ci_low:.8f},{ci_high:.8f}]"
        )
    if not ordering_matches(summaries):
        print(
            "[a7-check] expected_order=" + ">".join(FIG4_ORDER)
            + " status=FAIL"
        )
        return 1
    print("[a7-check] fig4_order status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
