#!/usr/bin/env python3
"""Shared locked configuration and event checks for B3/B4 gamma samples."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from validate_a0_csv import (
    COUNT_COLUMNS,
    EXPECTED_COLUMNS,
    validate_surface_absorption_subtotal,
)


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "b3_gamma.json"


@dataclass(frozen=True)
class B3Config:
    path: Path
    events: int
    gamma_energy_kev: float
    source_position_mm: tuple[float, float, float]
    beam_radius_mm: float
    event_seed_base: int
    run_seeds: tuple[int, int]
    surface_state: str
    sigma_alpha_rad: float
    geometry: dict[str, float]
    full_energy_half_width_kev: float
    expected_yield_per_mev: float
    max_yield_relative_error: float
    require_all_classes: bool


@dataclass(frozen=True)
class GammaEvent:
    event_id: int
    source_position_mm: tuple[float, float, float]
    edep_kev: float
    generated: int
    output: int
    counts: tuple[int, ...]

    @property
    def collection_efficiency(self) -> float:
        return 0.0 if self.generated == 0 else self.output / self.generated


@dataclass(frozen=True)
class GammaSummary:
    path: Path
    events: tuple[GammaEvent, ...]
    zero_edep_events: int
    partial_energy_events: int
    full_energy_events: int
    total_edep_kev: float
    total_generated: int
    full_edep_kev: float
    full_generated: int
    full_output: int

    @property
    def total_yield_per_mev(self) -> float:
        return self.total_generated / (self.total_edep_kev / 1000.0)

    @property
    def full_energy_yield_per_mev(self) -> float:
        return self.full_generated / (self.full_edep_kev / 1000.0)

    @property
    def full_energy_collection_efficiency(self) -> float:
        return self.full_output / self.full_generated


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> B3Config:
    path = path.resolve()
    with path.open(encoding="utf-8") as stream:
        raw = json.load(stream)
    if raw.get("stage") != "B3":
        raise ValueError("B3 configuration must declare stage=B3")
    events = int(raw["events"])
    energy = float(raw["gamma_energy_keV"])
    position = tuple(float(value) for value in raw["source_position_mm"])
    run_seeds = tuple(int(value) for value in raw["run_seeds"])
    if events <= 0 or energy <= 0.0 or len(position) != 3:
        raise ValueError("B3 event count, energy or source position is invalid")
    if len(run_seeds) != 2 or min(run_seeds) <= 0:
        raise ValueError("B3 requires two positive run seeds")
    if int(raw["event_seed_base"]) <= 0:
        raise ValueError("B3 event_seed_base must be positive")
    geometry = {key: float(value) for key, value in raw["geometry"].items()}
    expected_geometry = {
        "side_air_gap_mm",
        "black_housing_thickness_mm",
        "esr_thickness_mm",
        "pmt_window_thickness_mm",
    }
    if set(geometry) != expected_geometry or min(geometry.values()) <= 0.0:
        raise ValueError("B3 geometry placeholders are incomplete or invalid")
    validation = raw["validation"]
    return B3Config(
        path=path,
        events=events,
        gamma_energy_kev=energy,
        source_position_mm=(position[0], position[1], position[2]),
        beam_radius_mm=float(raw["beam_radius_mm"]),
        event_seed_base=int(raw["event_seed_base"]),
        run_seeds=(run_seeds[0], run_seeds[1]),
        surface_state=str(raw["surface_state"]),
        sigma_alpha_rad=float(raw["sigma_alpha_rad"]),
        geometry=geometry,
        full_energy_half_width_kev=float(validation["full_energy_half_width_keV"]),
        expected_yield_per_mev=float(validation["expected_yield_photons_per_MeV"]),
        max_yield_relative_error=float(validation["max_yield_relative_error"]),
        require_all_classes=bool(validation["require_zero_partial_full_classes"]),
    )


def load_gamma_sample(
    path: Path,
    config: B3Config,
    expected_state: str | None = None,
    expected_sigma: float | None = None,
) -> GammaSummary:
    state = config.surface_state if expected_state is None else expected_state
    sigma = config.sigma_alpha_rad if expected_sigma is None else expected_sigma
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(f"unexpected columns in {path}: {reader.fieldnames}")
        rows = list(reader)
    if len(rows) != config.events:
        raise ValueError(f"expected {config.events} events in {path}, found {len(rows)}")

    events: list[GammaEvent] = []
    zero_count = partial_count = full_count = 0
    total_edep = full_edep = 0.0
    total_generated = full_generated = full_output = 0
    for event_id, row in enumerate(rows):
        if int(row["event_id"]) != event_id:
            raise ValueError(f"event IDs are not contiguous in {path}")
        position = tuple(
            float(row[key])
            for key in ("source_x_mm", "source_y_mm", "source_z_mm")
        )
        if position != config.source_position_mm:
            raise ValueError(f"unexpected source position in {path}: {position}")
        if row["source_particle"] != "gamma":
            raise ValueError(f"unexpected particle in {path}")
        if abs(float(row["source_energy_keV"]) - config.gamma_energy_kev) > 1.0e-9:
            raise ValueError(f"unexpected gamma energy in {path}")
        if row["stage_a_surface"] != "none":
            raise ValueError(f"Stage A surface is active in {path}")
        if row["stage_b_surface_state"] != state:
            raise ValueError(f"Stage B state mismatch in {path}")
        if abs(float(row["stage_b_sigma_alpha_rad"]) - sigma) > 1.0e-12:
            raise ValueError(f"sigma_alpha mismatch in {path}")

        edep = float(row["edep_keV"])
        if edep < 0.0 or edep > config.gamma_energy_kev + 1.0e-6:
            raise ValueError(f"unphysical energy deposit in {path}: {edep}")
        values = {key: int(row[key]) for key in COUNT_COLUMNS}
        if values["scintillation"] != values["generated"]:
            raise ValueError(f"non-scintillation optical photon in {path}")
        expected_generated = edep * config.expected_yield_per_mev / 1000.0
        if abs(values["generated"] - expected_generated) > 4.0:
            raise ValueError(f"light yield/energy mismatch in {path}, event {event_id}")
        if values["world_exit"] != values["output"] + values["other_world_exit"]:
            raise ValueError(f"world-exit subtotal failed in {path}")
        if values["bulk_absorption"] != (
            values["crystal_absorption"]
            + values["reflector_absorption"]
            + values["other_absorption"]
        ):
            raise ValueError(f"bulk-absorption subtotal failed in {path}")
        validate_surface_absorption_subtotal(values, path)
        classified = (
            values["world_exit"]
            + values["bulk_absorption"]
            + values["surface_absorption"]
        )
        if classified + values["unclassified"] != values["generated"]:
            raise ValueError(f"photon accounting failed in {path}")
        if values["unclassified"] != 0 or values["output"] > values["generated"]:
            raise ValueError(f"invalid terminal count in {path}")

        event = GammaEvent(
            event_id=event_id,
            source_position_mm=(position[0], position[1], position[2]),
            edep_kev=edep,
            generated=values["generated"],
            output=values["output"],
            counts=tuple(values[key] for key in COUNT_COLUMNS),
        )
        events.append(event)
        total_edep += edep
        total_generated += values["generated"]
        if edep == 0.0:
            zero_count += 1
            if any(values[key] != 0 for key in COUNT_COLUMNS):
                raise ValueError(f"zero-Edep event transported light in {path}")
        elif abs(edep - config.gamma_energy_kev) <= config.full_energy_half_width_kev:
            full_count += 1
            full_edep += edep
            full_generated += values["generated"]
            full_output += values["output"]
        else:
            partial_count += 1

    if config.require_all_classes and min(zero_count, partial_count, full_count) == 0:
        raise ValueError(
            f"B3 requires zero/partial/full classes, got {zero_count}/{partial_count}/{full_count}"
        )
    summary = GammaSummary(
        path=path,
        events=tuple(events),
        zero_edep_events=zero_count,
        partial_energy_events=partial_count,
        full_energy_events=full_count,
        total_edep_kev=total_edep,
        total_generated=total_generated,
        full_edep_kev=full_edep,
        full_generated=full_generated,
        full_output=full_output,
    )
    for label, measured in (
        ("all-depositing", summary.total_yield_per_mev),
        ("full-energy", summary.full_energy_yield_per_mev),
    ):
        relative_error = abs(measured - config.expected_yield_per_mev) / config.expected_yield_per_mev
        if relative_error > config.max_yield_relative_error:
            raise ValueError(f"{label} yield mismatch in {path}: {relative_error}")
    return summary
