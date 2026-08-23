#!/usr/bin/env python3
"""Configuration, paired comparison and uncertainty helpers for B4."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from b3_common import B3Config, GammaEvent, GammaSummary, load_config as load_b3_config


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "b4_comparison.json"
EXPECTED_STATES = (
    "all_polished",
    "bottom_rough",
    "top_rough",
    "side_rough",
    "bottom_polished_others_rough",
    "top_polished_others_rough",
)


@dataclass(frozen=True)
class B4Config:
    path: Path
    b3: B3Config
    states: tuple[str, ...]
    shared_sigma_alpha_rad: float
    sigma_provenance: str
    measured_ratios: dict[str, float]
    minimum_full_energy_events: int
    bootstrap_samples: int
    bootstrap_seed: int
    confidence_level: float
    require_exact_b3_repeat: bool
    experimental_agreement_is_pass_gate: bool


@dataclass(frozen=True)
class ComparisonRow:
    state: str
    full_energy_events: int
    generated: int
    output: int
    efficiency: float
    normalized: float
    ci_low: float
    ci_high: float
    measured: float

    @property
    def residual(self) -> float:
        return self.normalized - self.measured


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> B4Config:
    path = path.resolve()
    with path.open(encoding="utf-8") as stream:
        raw = json.load(stream)
    if raw.get("stage") != "B4":
        raise ValueError("B4 configuration must declare stage=B4")
    states = tuple(str(value) for value in raw["states"])
    if states != EXPECTED_STATES:
        raise ValueError("B4 states must match the six B1 states in fixed order")
    measured = {
        str(key): float(value)
        for key, value in raw["measured_normalized_light_output"].items()
    }
    if set(measured) != set(states) or measured["all_polished"] != 1.0:
        raise ValueError("B4 measured ratios must cover all states and normalize to one")
    b3_path = path.parent / str(raw["b3_config"])
    b3 = load_b3_config(b3_path)
    sigma = float(raw["shared_sigma_alpha_rad"])
    if abs(sigma - b3.sigma_alpha_rad) > 1.0e-12:
        raise ValueError("B4 shared sigma must equal the locked B3 reference value")
    validation = raw["validation"]
    confidence = float(validation["confidence_level"])
    if not 0.0 < confidence < 1.0:
        raise ValueError("B4 confidence level must be between zero and one")
    if bool(validation["experimental_agreement_is_pass_gate"]):
        raise ValueError("B4 must not use experimental agreement as a pass gate")
    return B4Config(
        path=path,
        b3=b3,
        states=states,
        shared_sigma_alpha_rad=sigma,
        sigma_provenance=str(raw["sigma_provenance"]),
        measured_ratios=measured,
        minimum_full_energy_events=int(validation["minimum_full_energy_events"]),
        bootstrap_samples=int(validation["bootstrap_samples"]),
        bootstrap_seed=int(validation["bootstrap_seed"]),
        confidence_level=confidence,
        require_exact_b3_repeat=bool(validation["require_exact_b3_all_polished_repeat"]),
        experimental_agreement_is_pass_gate=False,
    )


def state_filename(state: str) -> str:
    return f"gamma_511kev_{state}.csv"


def full_energy_events(summary: GammaSummary, b3: B3Config) -> tuple[GammaEvent, ...]:
    return tuple(
        event
        for event in summary.events
        if abs(event.edep_kev - b3.gamma_energy_kev) <= b3.full_energy_half_width_kev
    )


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def make_comparison(
    config: B4Config, summaries: dict[str, GammaSummary]
) -> tuple[ComparisonRow, ...]:
    full = {state: full_energy_events(summary, config.b3) for state, summary in summaries.items()}
    event_count = len(full["all_polished"])
    if event_count < config.minimum_full_energy_events:
        raise ValueError(
            f"B4 has {event_count} full-energy events; minimum is {config.minimum_full_energy_events}"
        )
    reference = summaries["all_polished"].full_energy_collection_efficiency
    bootstrap: dict[str, list[float]] = {state: [] for state in config.states}
    generator = random.Random(config.bootstrap_seed)
    for _ in range(config.bootstrap_samples):
        indices = [generator.randrange(event_count) for _ in range(event_count)]
        reference_output = sum(full["all_polished"][index].output for index in indices)
        reference_generated = sum(full["all_polished"][index].generated for index in indices)
        reference_efficiency = reference_output / reference_generated
        for state in config.states:
            output = sum(full[state][index].output for index in indices)
            generated = sum(full[state][index].generated for index in indices)
            bootstrap[state].append((output / generated) / reference_efficiency)
    alpha = (1.0 - config.confidence_level) / 2.0
    rows = []
    for state in config.states:
        summary = summaries[state]
        normalized = summary.full_energy_collection_efficiency / reference
        rows.append(
            ComparisonRow(
                state=state,
                full_energy_events=summary.full_energy_events,
                generated=summary.full_generated,
                output=summary.full_output,
                efficiency=summary.full_energy_collection_efficiency,
                normalized=normalized,
                ci_low=quantile(bootstrap[state], alpha),
                ci_high=quantile(bootstrap[state], 1.0 - alpha),
                measured=config.measured_ratios[state],
            )
        )
    return tuple(rows)
