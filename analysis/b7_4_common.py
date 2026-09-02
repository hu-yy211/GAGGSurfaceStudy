#!/usr/bin/env python3
"""Shared configuration and reduction for the B7.4 shared-sigma scan."""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, replace
from pathlib import Path

from b4_common import EXPECTED_STATES, quantile
from b7_3_common import B73Config, B73Summary, load_config as load_b73_config, load_sample


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "b7_4_sigma_scan.json"


@dataclass(frozen=True)
class B74Config:
    path: Path
    response: B73Config
    states: tuple[str, ...]
    sigmas: tuple[float, ...]
    reference_sigma: float
    max_parallel_processes: int
    measured_ratios: dict[str, float]
    selection_objective: str
    bootstrap_samples: int
    bootstrap_seed: int
    confidence_level: float
    require_exact_pairing: bool


@dataclass(frozen=True)
class ScanRow:
    sigma: float
    state: str
    full_events: int
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


@dataclass(frozen=True)
class SigmaScore:
    sigma: float
    rmse: float
    mae: float
    pair_order_fraction: float


def sigma_tag(sigma: float) -> str:
    return f"{round(sigma * 1000):03d}"


def point_path(input_dir: Path, state: str, sigma: float, reference_sigma: float) -> Path:
    if state == "all_polished":
        return input_dir / "all_polished.csv"
    return input_dir / f"sigma_{sigma_tag(sigma)}" / f"{state}.csv"


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> B74Config:
    path = path.resolve()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("stage") != "B7.4":
        raise ValueError("B7.4 configuration must declare stage=B7.4")
    states = tuple(str(value) for value in raw["states"])
    if states != EXPECTED_STATES:
        raise ValueError("B7.4 states must match the six locked Stage-B states")
    sigmas = tuple(float(value) for value in raw["shared_sigma_alpha_rad"])
    if not sigmas or sigmas != tuple(sorted(set(sigmas))) or min(sigmas) < 0.0 or max(sigmas) >= math.pi / 2.0:
        raise ValueError("B7.4 shared-sigma grid is invalid")
    if not bool(raw["reuse_all_polished_across_sigma"]):
        raise ValueError("B7.4 must reuse the sigma-inactive all-polished reference")
    validation = raw["validation"]
    if bool(validation["allow_per_face_sigma"]):
        raise ValueError("B7.4 forbids per-face sigma values")
    if bool(validation["experimental_agreement_is_pass_gate"]):
        raise ValueError("B7.4 agreement cannot be a structural pass gate")
    if not bool(validation["require_exact_event_history_pairing"]):
        raise ValueError("B7.4 requires exact paired gamma histories")
    measured = {str(key): float(value) for key, value in raw["measured_normalized_light_output"].items()}
    if set(measured) != set(states) or measured["all_polished"] != 1.0:
        raise ValueError("B7.4 measurements must cover and normalize all six states")
    base = load_b73_config(path.parent / str(raw["b7_3_config"]))
    events = int(raw["events_per_point"])
    minimum = int(validation["minimum_full_energy_events"])
    if events <= 0 or minimum <= 0:
        raise ValueError("B7.4 event-count controls are invalid")
    response = replace(base, events=events, minimum_full_energy_events=minimum)
    reference_sigma = float(raw["all_polished_reference_sigma_rad"])
    if reference_sigma not in sigmas:
        raise ValueError("B7.4 reference sigma must lie on the scan grid")
    objective = str(raw["selection_objective"])
    if objective != "rmse_non_reference_states":
        raise ValueError("B7.4 has an unsupported selection objective")
    return B74Config(
        path=path, response=response, states=states, sigmas=sigmas,
        reference_sigma=reference_sigma,
        max_parallel_processes=int(raw["max_parallel_processes"]),
        measured_ratios=measured, selection_objective=objective,
        bootstrap_samples=int(validation["bootstrap_samples"]),
        bootstrap_seed=int(validation["bootstrap_seed"]),
        confidence_level=float(validation["confidence_level"]),
        require_exact_pairing=True,
    )


def event_history(summary: B73Summary) -> tuple[tuple, ...]:
    return tuple(
        (event.event_id, event.source_position_mm, event.edep_kev, event.generated)
        for event in summary.events
    )


def load_scan(input_dir: Path, config: B74Config) -> tuple[dict[tuple[float, str], B73Summary], tuple[ScanRow, ...], tuple[SigmaScore, ...]]:
    reference = load_sample(
        point_path(input_dir, "all_polished", config.reference_sigma, config.reference_sigma),
        config.response, expected_state="all_polished", expected_sigma=config.reference_sigma,
    )
    reference_history = event_history(reference)
    summaries: dict[tuple[float, str], B73Summary] = {}
    for sigma in config.sigmas:
        summaries[(sigma, "all_polished")] = reference
        for state in config.states[1:]:
            summary = load_sample(
                point_path(input_dir, state, sigma, config.reference_sigma),
                config.response, expected_state=state, expected_sigma=sigma,
            )
            if config.require_exact_pairing and event_history(summary) != reference_history:
                raise ValueError(f"B7.4 event history mismatch at sigma={sigma}, state={state}")
            summaries[(sigma, state)] = summary

    reference_full = reference.full_energy_events
    reference_efficiency = reference.full_collection_efficiency
    alpha = (1.0 - config.confidence_level) / 2.0
    rows: list[ScanRow] = []
    for sigma_index, sigma in enumerate(config.sigmas):
        bootstrap = {state: [] for state in config.states}
        generator = random.Random(config.bootstrap_seed + sigma_index)
        for _ in range(config.bootstrap_samples):
            indices = [generator.randrange(len(reference_full)) for _ in reference_full]
            ref_out = sum(reference_full[index].output for index in indices)
            ref_gen = sum(reference_full[index].generated for index in indices)
            ref_eff = ref_out / ref_gen
            for state in config.states:
                selected = summaries[(sigma, state)].full_energy_events
                out = sum(selected[index].output for index in indices)
                gen = sum(selected[index].generated for index in indices)
                bootstrap[state].append((out / gen) / ref_eff)
        for state in config.states:
            summary = summaries[(sigma, state)]
            normalized = summary.full_collection_efficiency / reference_efficiency
            rows.append(ScanRow(
                sigma=sigma, state=state,
                full_events=len(summary.full_energy_events),
                generated=summary.full_generated, output=summary.full_output,
                efficiency=summary.full_collection_efficiency,
                normalized=normalized,
                ci_low=quantile(bootstrap[state], alpha),
                ci_high=quantile(bootstrap[state], 1.0 - alpha),
                measured=config.measured_ratios[state],
            ))

    scores: list[SigmaScore] = []
    for sigma in config.sigmas:
        sigma_rows = {row.state: row for row in rows if row.sigma == sigma}
        residuals = [sigma_rows[state].residual for state in config.states[1:]]
        rmse = math.sqrt(sum(value * value for value in residuals) / len(residuals))
        mae = sum(abs(value) for value in residuals) / len(residuals)
        comparable = correct = 0
        for index, first in enumerate(config.states):
            for second in config.states[index + 1:]:
                measured_delta = config.measured_ratios[first] - config.measured_ratios[second]
                if abs(measured_delta) <= 1.0e-12:
                    continue
                simulated_delta = sigma_rows[first].normalized - sigma_rows[second].normalized
                comparable += 1
                correct += simulated_delta * measured_delta > 0.0
        scores.append(SigmaScore(sigma, rmse, mae, correct / comparable))
    return summaries, tuple(rows), tuple(scores)


def best_score(scores: tuple[SigmaScore, ...]) -> SigmaScore:
    return min(scores, key=lambda score: (score.rmse, score.sigma))


def best_positive_score(scores: tuple[SigmaScore, ...]) -> SigmaScore:
    positive = tuple(score for score in scores if score.sigma > 0.0)
    if not positive:
        raise ValueError("B7.4 has no positive roughness candidate")
    return best_score(positive)
