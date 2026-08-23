#!/usr/bin/env python3
"""Shared configuration and file naming for the predeclared B2 scan."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "b2_scan.json"
)

EXPECTED_STATES = (
    "all_polished",
    "bottom_rough",
    "top_rough",
    "side_rough",
    "bottom_polished_others_rough",
    "top_polished_others_rough",
)


@dataclass(frozen=True)
class SigmaPoint:
    tag: str
    value_rad: float


@dataclass(frozen=True)
class PositionPoint:
    tag: str
    xyz_mm: tuple[float, float, float]


@dataclass(frozen=True)
class RepeatPoint:
    state: str
    position_tag: str
    sigma_tag: str


@dataclass(frozen=True)
class B2Config:
    path: Path
    events_per_point: int
    photons_per_event: int
    event_seed_base: int
    run_seeds: tuple[int, int]
    geometry: dict[str, float]
    sigmas: tuple[SigmaPoint, ...]
    positions: tuple[PositionPoint, ...]
    states: tuple[str, ...]
    repeat: RepeatPoint
    max_adjacent_efficiency_jump: float
    min_rough_response_span: float

    def sigma(self, tag: str) -> SigmaPoint:
        return next(point for point in self.sigmas if point.tag == tag)

    def position(self, tag: str) -> PositionPoint:
        return next(point for point in self.positions if point.tag == tag)

    @property
    def point_count(self) -> int:
        return len(self.states) * len(self.sigmas) * len(self.positions)


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> B2Config:
    path = path.resolve()
    with path.open(encoding="utf-8") as stream:
        raw = json.load(stream)

    if raw.get("stage") != "B2":
        raise ValueError("B2 configuration must declare stage=B2")
    events = int(raw["events_per_point"])
    photons = int(raw["photons_per_event"])
    seed_base = int(raw["event_seed_base"])
    run_seeds = tuple(int(value) for value in raw["run_seeds"])
    if events <= 0 or photons <= 0 or seed_base <= 0:
        raise ValueError("B2 event, photon and seed values must be positive")
    if len(run_seeds) != 2 or min(run_seeds) <= 0:
        raise ValueError("B2 requires two positive run seeds")

    sigmas = tuple(
        SigmaPoint(str(point["tag"]), float(point["value_rad"]))
        for point in raw["sigma_alpha"]
    )
    if len(sigmas) < 3:
        raise ValueError("B2 requires at least three sigma_alpha points")
    if len({point.tag for point in sigmas}) != len(sigmas):
        raise ValueError("B2 sigma tags must be unique")
    sigma_values = [point.value_rad for point in sigmas]
    if sigma_values != sorted(sigma_values) or len(set(sigma_values)) != len(sigmas):
        raise ValueError("B2 sigma values must be unique and increasing")
    if min(sigma_values) < 0.0 or max(sigma_values) >= math.pi / 2.0:
        raise ValueError("B2 sigma values must satisfy 0 <= sigma < pi/2")

    positions = tuple(
        PositionPoint(
            str(point["tag"]),
            tuple(float(value) for value in point["xyz_mm"]),
        )
        for point in raw["positions"]
    )
    if len(positions) < 3 or len({point.tag for point in positions}) != len(positions):
        raise ValueError("B2 requires at least three uniquely tagged positions")
    for point in positions:
        if len(point.xyz_mm) != 3:
            raise ValueError("B2 positions must contain x, y and z")
        if point.xyz_mm[0] != 0.0 or point.xyz_mm[1] != 0.0:
            raise ValueError("B2 validation positions must lie on the crystal axis")
        if abs(point.xyz_mm[2]) >= 10.0:
            raise ValueError("B2 validation positions must be inside the 20 mm crystal")

    states = tuple(str(value) for value in raw["states"])
    if states != EXPECTED_STATES:
        raise ValueError("B2 states must match the six validated B1 states")
    repeat = RepeatPoint(**raw["repeat"])
    if repeat.state not in states:
        raise ValueError("B2 repeat state is not in the scan")
    if repeat.position_tag not in {point.tag for point in positions}:
        raise ValueError("B2 repeat position is not in the scan")
    if repeat.sigma_tag not in {point.tag for point in sigmas}:
        raise ValueError("B2 repeat sigma is not in the scan")

    geometry = {key: float(value) for key, value in raw["geometry"].items()}
    expected_geometry = {
        "side_air_gap_mm",
        "black_housing_thickness_mm",
        "esr_thickness_mm",
        "pmt_window_thickness_mm",
    }
    if set(geometry) != expected_geometry or min(geometry.values()) <= 0.0:
        raise ValueError("B2 geometry placeholders are incomplete or invalid")

    validation = raw["validation"]
    max_jump = float(validation["max_adjacent_efficiency_jump"])
    min_span = float(validation["min_state_response_span_at_any_position"])
    if not 0.0 < max_jump < 1.0 or not 0.0 < min_span < max_jump:
        raise ValueError("B2 response thresholds are invalid")

    return B2Config(
        path=path,
        events_per_point=events,
        photons_per_event=photons,
        event_seed_base=seed_base,
        run_seeds=(run_seeds[0], run_seeds[1]),
        geometry=geometry,
        sigmas=sigmas,
        positions=positions,
        states=states,
        repeat=repeat,
        max_adjacent_efficiency_jump=max_jump,
        min_rough_response_span=min_span,
    )


def point_filename(state: str, position_tag: str, sigma_tag: str) -> str:
    return f"{state}_{position_tag}_sigma{sigma_tag}.csv"


def repeat_filename(config: B2Config) -> str:
    repeat = config.repeat
    return (
        f"{repeat.state}_{repeat.position_tag}_sigma{repeat.sigma_tag}"
        "_repeat.csv"
    )
