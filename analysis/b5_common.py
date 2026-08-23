#!/usr/bin/env python3
"""Locked B5 shared-roughness robustness configuration and file naming."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from b4_common import B4Config, load_config as load_b4_config


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "b5_robustness.json"


@dataclass(frozen=True)
class B5Config:
    path: Path
    b4: B4Config
    sigmas: tuple[float, ...]
    reuse_sigma: float
    full_energy_half_widths_kev: tuple[float, ...]
    max_parallel_processes: int
    minimum_full_energy_events: int
    response_reporting_threshold: float
    minimum_resolved_rough_states: int
    require_polished_invariance: bool
    require_history_pairing: bool

    @property
    def run_sigmas(self) -> tuple[float, ...]:
        return tuple(value for value in self.sigmas if value != self.reuse_sigma)


def sigma_tag(value: float) -> str:
    return f"{round(value * 100):03d}"


def point_filename(state: str, sigma: float) -> str:
    return f"gamma_511kev_{state}_sigma{sigma_tag(sigma)}.csv"


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> B5Config:
    path = path.resolve()
    with path.open(encoding="utf-8") as stream:
        raw = json.load(stream)
    if raw.get("stage") != "B5":
        raise ValueError("B5 configuration must declare stage=B5")
    b4 = load_b4_config(path.parent / str(raw["b4_config"]))
    sigmas = tuple(float(value) for value in raw["shared_sigma_alpha_rad"])
    if len(sigmas) < 3 or list(sigmas) != sorted(set(sigmas)):
        raise ValueError("B5 requires at least three unique increasing sigma values")
    reuse = float(raw["reuse_b4_sigma_alpha_rad"])
    if reuse not in sigmas or abs(reuse - b4.shared_sigma_alpha_rad) > 1.0e-12:
        raise ValueError("B5 reuse sigma must identify the B4 comparison point")
    widths = tuple(float(value) for value in raw["full_energy_half_width_keV"])
    if len(widths) < 3 or list(widths) != sorted(set(widths)) or min(widths) <= 0.0:
        raise ValueError("B5 full-energy windows must be unique, positive and increasing")
    validation = raw["validation"]
    if bool(validation["experimental_values_are_fit_target"]):
        raise ValueError("B5 experimental values must not be a fit target")
    if bool(validation["allow_per_face_sigma"]):
        raise ValueError("B5 must not allow per-face roughness parameters")
    max_parallel = int(raw["max_parallel_processes"])
    if max_parallel <= 0:
        raise ValueError("B5 max_parallel_processes must be positive")
    return B5Config(
        path=path,
        b4=b4,
        sigmas=sigmas,
        reuse_sigma=reuse,
        full_energy_half_widths_kev=widths,
        max_parallel_processes=max_parallel,
        minimum_full_energy_events=int(validation["minimum_full_energy_events"]),
        response_reporting_threshold=float(validation["roughness_response_reporting_threshold"]),
        minimum_resolved_rough_states=int(validation["minimum_rough_states_above_reporting_threshold"]),
        require_polished_invariance=bool(validation["require_all_polished_sigma_invariance"]),
        require_history_pairing=bool(validation["require_exact_gamma_history_pairing"]),
    )
