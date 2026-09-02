#!/usr/bin/env python3
"""Configuration and event-level checks for the B7.3 response sample."""

from __future__ import annotations

import csv
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path

from validate_a0_csv import (
    COUNT_COLUMNS,
    EXPECTED_COLUMNS,
    validate_surface_absorption_subtotal,
)


DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "b7_3_full_energy_response.json"
)


@dataclass(frozen=True)
class B73Config:
    path: Path
    events: int
    source: dict
    geometry: dict[str, float]
    state: str
    sigma_alpha_rad: float
    gate_center_kev: float
    gate_half_width_kev: float
    minimum_full_energy_events: int
    expected_yield_per_mev: float
    max_yield_relative_error: float


@dataclass(frozen=True)
class B73Event:
    event_id: int
    source_position_mm: tuple[float, float, float]
    edep_kev: float
    generated: int
    output: int


@dataclass(frozen=True)
class B73Summary:
    events: tuple[B73Event, ...]
    zero_events: int
    partial_events: int
    full_energy_events: tuple[B73Event, ...]
    total_edep_kev: float
    total_generated: int
    full_edep_kev: float
    full_generated: int
    full_output: int

    @property
    def full_collection_efficiency(self) -> float:
        return self.full_output / self.full_generated

    @property
    def mean_full_output(self) -> float:
        return self.full_output / len(self.full_energy_events)

    @property
    def mean_full_generated(self) -> float:
        return self.full_generated / len(self.full_energy_events)

    @property
    def full_output_standard_error(self) -> float:
        values = [event.output for event in self.full_energy_events]
        return statistics.stdev(values) / math.sqrt(len(values))

    @property
    def full_efficiency_standard_error(self) -> float:
        values = [event.output / event.generated for event in self.full_energy_events]
        return statistics.stdev(values) / math.sqrt(len(values))

    @property
    def full_yield_per_mev(self) -> float:
        return self.full_generated / (self.full_edep_kev / 1000.0)


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> B73Config:
    path = path.resolve()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("stage") != "B7.3":
        raise ValueError("B7.3 configuration must declare stage=B7.3")
    source = raw["source"]
    if source.get("particle") != "annihilationPair":
        raise ValueError("B7.3 requires the validated annihilationPair source")
    if source.get("direction_mode") != "isotropic":
        raise ValueError("B7.3 pair axis must be isotropic")
    if float(source["gamma_energy_keV"]) != 511.0:
        raise ValueError("B7.3 requires two 511 keV source gammas")
    if float(source["face_size_mm"]) != 2.5 or float(source["beam_radius_mm"]) != 0.0:
        raise ValueError("B7.3 requires the validated 2.5 mm square source face")
    position = tuple(float(value) for value in source["position_mm"])
    seeds = tuple(int(value) for value in source["run_seeds"])
    if position != (0.0, 0.0, 30.0) or len(seeds) != 2 or min(seeds) <= 0:
        raise ValueError("B7.3 source position or seeds are invalid")
    geometry = {key: float(value) for key, value in raw["geometry"].items()}
    expected_geometry = {
        "side_air_gap_mm", "top_air_gap_mm", "bottom_air_gap_mm",
        "black_housing_thickness_mm", "esr_thickness_mm",
        "pmt_window_thickness_mm",
    }
    if set(geometry) != expected_geometry or min(geometry.values()) <= 0.0:
        raise ValueError("B7.3 nominal geometry is incomplete")
    validation = raw["validation"]
    surface = raw["surface"]
    return B73Config(
        path=path,
        events=int(raw["events"]),
        source=source,
        geometry=geometry,
        state=str(surface["state"]),
        sigma_alpha_rad=float(surface["shared_sigma_alpha_rad"]),
        gate_center_kev=float(validation["full_energy_center_keV"]),
        gate_half_width_kev=float(validation["full_energy_half_width_keV"]),
        minimum_full_energy_events=int(validation["minimum_full_energy_events"]),
        expected_yield_per_mev=float(validation["expected_yield_photons_per_MeV"]),
        max_yield_relative_error=float(validation["max_yield_relative_error"]),
    )


def load_sample(
    path: Path,
    config: B73Config,
    expected_state: str | None = None,
    expected_sigma: float | None = None,
) -> B73Summary:
    state = config.state if expected_state is None else expected_state
    sigma = config.sigma_alpha_rad if expected_sigma is None else expected_sigma
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(f"unexpected B7.3 columns in {path}")
        rows = list(reader)
    if len(rows) != config.events:
        raise ValueError(f"expected {config.events} events, found {len(rows)}")

    source = config.source
    center_x, center_y, center_z = (float(value) for value in source["position_mm"])
    half_face = 0.5 * float(source["face_size_mm"])
    zero = partial = 0
    events: list[B73Event] = []
    full: list[B73Event] = []
    total_edep = full_edep = 0.0
    total_generated = full_generated = full_output = 0
    for event_id, row in enumerate(rows):
        if int(row["event_id"]) != event_id:
            raise ValueError("B7.3 event IDs are not contiguous")
        if row["source_particle"] != "annihilationPair":
            raise ValueError("B7.3 event does not use annihilationPair")
        if abs(float(row["source_energy_keV"]) - 511.0) > 1.0e-9:
            raise ValueError("B7.3 source-energy metadata is not 511 keV")
        x, y, z = (float(row[key]) for key in EXPECTED_COLUMNS[1:4])
        if not (center_x - half_face <= x <= center_x + half_face):
            raise ValueError("B7.3 source x lies outside the square face")
        if not (center_y - half_face <= y <= center_y + half_face) or z != center_z:
            raise ValueError("B7.3 source position lies outside the source plane")
        if row["stage_a_surface"] != "none" or row["stage_b_surface_state"] != state:
            raise ValueError("B7.3 surface metadata mismatch")
        if abs(float(row["stage_b_sigma_alpha_rad"]) - sigma) > 1.0e-12:
            raise ValueError("B7.3 shared sigma metadata mismatch")

        edep = float(row["edep_keV"])
        if edep < 0.0 or edep > 511.0 + 1.0e-6:
            raise ValueError(f"B7.3 event has invalid GAGG Edep: {edep}")
        counts = {key: int(row[key]) for key in COUNT_COLUMNS}
        if counts["scintillation"] != counts["generated"]:
            raise ValueError("B7.3 contains non-scintillation optical photons")
        expected_generated = edep * config.expected_yield_per_mev / 1000.0
        # Geant4 emits an integer scintillation count for each energy-loss
        # step. Summing many independently rounded step yields can differ by
        # a few photons from applying the yield once to event-total Edep.
        # The aggregate full-energy yield below remains the strict physics
        # check; this bound only catches event-accounting failures.
        if abs(counts["generated"] - expected_generated) > 8.0:
            raise ValueError(f"B7.3 yield mismatch in event {event_id}")
        if counts["world_exit"] != counts["output"] + counts["other_world_exit"]:
            raise ValueError("B7.3 world-exit subtotal failed")
        if counts["bulk_absorption"] != (
            counts["crystal_absorption"] + counts["reflector_absorption"]
            + counts["other_absorption"]
        ):
            raise ValueError("B7.3 bulk-absorption subtotal failed")
        validate_surface_absorption_subtotal(counts, path)
        classified = counts["world_exit"] + counts["bulk_absorption"] + counts["surface_absorption"]
        if classified + counts["unclassified"] != counts["generated"]:
            raise ValueError("B7.3 optical-photon accounting failed")
        if counts["unclassified"] != 0 or counts["output"] > counts["generated"]:
            raise ValueError("B7.3 has invalid terminal optical counts")

        event = B73Event(event_id, (x, y, z), edep, counts["generated"], counts["output"])
        events.append(event)
        total_edep += edep
        total_generated += counts["generated"]
        if edep == 0.0:
            zero += 1
            if any(counts[key] != 0 for key in COUNT_COLUMNS):
                raise ValueError("zero-Edep B7.3 event transported optical light")
        elif abs(edep - config.gate_center_kev) <= config.gate_half_width_kev:
            full.append(event)
            full_edep += edep
            full_generated += counts["generated"]
            full_output += counts["output"]
        else:
            partial += 1

    if min(zero, partial) == 0 or len(full) < config.minimum_full_energy_events:
        raise ValueError(
            f"B7.3 insufficient event classes: zero={zero}, partial={partial}, full={len(full)}"
        )
    summary = B73Summary(
        tuple(events), zero, partial, tuple(full), total_edep, total_generated,
        full_edep, full_generated, full_output,
    )
    relative_error = abs(summary.full_yield_per_mev - config.expected_yield_per_mev) / config.expected_yield_per_mev
    if relative_error > config.max_yield_relative_error:
        raise ValueError(f"B7.3 full-energy light yield mismatch: {relative_error}")
    return summary
