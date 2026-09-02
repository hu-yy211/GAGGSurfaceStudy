#!/usr/bin/env python3
"""Configuration and paired reduction for the B7.5 end-face comparison."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

from b7_3_common import B73Config, B73Summary, load_config as load_b73_config, load_sample


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "b7_5_endface_sigma070.json"
EXPECTED_STATES = ("bottom_rough", "top_rough")


@dataclass(frozen=True)
class B75Config:
    path: Path
    response: B73Config
    states: tuple[str, ...]
    sigma: float
    max_parallel_processes: int
    measured_ratios: dict[str, float]
    bootstrap_samples: int
    bootstrap_seed: int
    confidence_level: float


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> B75Config:
    path = path.resolve()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("stage") != "B7.5":
        raise ValueError("B7.5 configuration must declare stage=B7.5")
    states = tuple(str(value) for value in raw["states"])
    if states != EXPECTED_STATES:
        raise ValueError("B7.5 must contain only bottom_rough and top_rough")
    sigma = float(raw["shared_sigma_alpha_rad"])
    if sigma != 0.70:
        raise ValueError("B7.5 is locked to shared sigma_alpha=0.70 rad")
    validation = raw["validation"]
    if not bool(validation["require_exact_event_history_pairing"]):
        raise ValueError("B7.5 requires exact paired histories")
    base = load_b73_config(path.parent / str(raw["b7_3_config"]))
    response = replace(
        base,
        events=int(raw["events"]),
        minimum_full_energy_events=int(validation["minimum_full_energy_events"]),
    )
    if response.events != 100000:
        raise ValueError("B7.5 is locked to 100000 events per rough state")
    measured = {
        str(key): float(value)
        for key, value in raw["measured_normalized_light_output"].items()
    }
    if set(measured) != {"all_polished", *states} or measured["all_polished"] != 1.0:
        raise ValueError("B7.5 measured ratios are incomplete")
    return B75Config(
        path=path,
        response=response,
        states=states,
        sigma=sigma,
        max_parallel_processes=int(raw["max_parallel_processes"]),
        measured_ratios=measured,
        bootstrap_samples=int(validation["bootstrap_samples"]),
        bootstrap_seed=int(validation["bootstrap_seed"]),
        confidence_level=float(validation["confidence_level"]),
    )


def event_history(summary: B73Summary) -> tuple[tuple, ...]:
    return tuple(
        (event.event_id, event.source_position_mm, event.edep_kev, event.generated)
        for event in summary.events
    )


def load_paired_samples(
    input_dir: Path,
    reference_path: Path,
    config: B75Config,
) -> dict[str, B73Summary]:
    reference = load_sample(
        reference_path,
        config.response,
        expected_state="all_polished",
        expected_sigma=config.response.sigma_alpha_rad,
    )
    summaries = {"all_polished": reference}
    history = event_history(reference)
    for state in config.states:
        summary = load_sample(
            input_dir / f"{state}.csv",
            config.response,
            expected_state=state,
            expected_sigma=config.sigma,
        )
        if event_history(summary) != history:
            raise ValueError(f"B7.5 event history mismatch for {state}")
        summaries[state] = summary
    return summaries
