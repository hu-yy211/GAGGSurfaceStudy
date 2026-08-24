#!/usr/bin/env python3
"""Configuration and loss-budget helpers for B6 diagnostics."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from b3_common import GammaEvent
from b5_common import B5Config, load_config as load_b5_config
from validate_a0_csv import COUNT_COLUMNS


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "b6_diagnostics.json"


@dataclass(frozen=True)
class B6Config:
    path: Path
    b5: B5Config
    comparison_sigma: float
    terminal_channels: tuple[str, ...]
    surface_locations: tuple[str, ...]
    face_interactions: tuple[str, ...]
    minimum_full_energy_events: int
    require_terminal_balance: bool
    require_surface_subtotal: bool
    require_top_black_nonzero: bool
    require_reflector_zero: bool


@dataclass(frozen=True)
class LossBudget:
    sigma_alpha_rad: float
    state: str
    full_energy_events: int
    generated: int
    counts: dict[str, int]

    def fraction(self, channel: str) -> float:
        return self.counts[channel] / self.generated


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> B6Config:
    path = path.resolve()
    with path.open(encoding="utf-8") as stream:
        raw = json.load(stream)
    if raw.get("stage") != "B6":
        raise ValueError("B6 configuration must declare stage=B6")
    b5 = load_b5_config(path.parent / str(raw["b5_config"]))
    comparison_sigma = float(raw["comparison_sigma_alpha_rad"])
    if comparison_sigma not in b5.sigmas:
        raise ValueError("B6 comparison sigma must be present in the B5 grid")
    terminal = tuple(str(value) for value in raw["terminal_channels"])
    surface = tuple(str(value) for value in raw["surface_absorption_locations"])
    interactions = tuple(str(value) for value in raw["face_interaction_channels"])
    if len(set(terminal)) != len(terminal) or "output" not in terminal:
        raise ValueError("B6 terminal channels must be unique and include output")
    if not set(surface).issubset(terminal):
        raise ValueError("B6 surface locations must be terminal channels")
    if not set(terminal + interactions + ("surface_absorption",)).issubset(COUNT_COLUMNS):
        raise ValueError("B6 requested a channel absent from the event CSV schema")
    validation = raw["validation"]
    if bool(validation["experimental_values_are_fit_target"]):
        raise ValueError("B6 is diagnostic and must not fit experimental values")
    return B6Config(
        path=path,
        b5=b5,
        comparison_sigma=comparison_sigma,
        terminal_channels=terminal,
        surface_locations=surface,
        face_interactions=interactions,
        minimum_full_energy_events=int(validation["minimum_full_energy_events"]),
        require_terminal_balance=bool(validation["require_exact_terminal_balance"]),
        require_surface_subtotal=bool(validation["require_exact_surface_absorption_subtotal"]),
        require_top_black_nonzero=bool(validation["require_nonzero_top_and_black_absorption"]),
        require_reflector_zero=bool(validation["require_zero_stage_a_reflector_absorption"]),
    )


def event_counts(event: GammaEvent) -> dict[str, int]:
    return dict(zip(COUNT_COLUMNS, event.counts))


def make_budget(config: B6Config, sigma: float, state: str, events: tuple[GammaEvent, ...]) -> LossBudget:
    full = tuple(
        event
        for event in events
        if abs(event.edep_kev - config.b5.b4.b3.gamma_energy_kev)
        <= config.b5.b4.b3.full_energy_half_width_kev
    )
    if len(full) < config.minimum_full_energy_events:
        raise ValueError(f"B6 has too few full-energy events for {sigma}/{state}")
    totals = {key: 0 for key in COUNT_COLUMNS}
    for event in full:
        values = event_counts(event)
        for key, value in values.items():
            totals[key] += value
    return LossBudget(
        sigma_alpha_rad=sigma,
        state=state,
        full_energy_events=len(full),
        generated=totals["generated"],
        counts=totals,
    )
