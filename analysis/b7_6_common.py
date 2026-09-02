#!/usr/bin/env python3
"""Shared configuration and reduction for the B7.6 photon-fate audit."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, replace
from pathlib import Path

from b7_3_common import B73Config, B73Summary, load_config as load_b73_config, load_sample
from validate_a0_csv import COUNT_COLUMNS, EXPECTED_COLUMNS


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "b7_6_photon_fate_audit.json"
STATES = (
    "all_polished",
    "bottom_rough",
    "top_rough",
    "top_bottom_rough",
    "side_rough",
)
AUDIT_COLUMNS = [
    "event_id",
    "generated",
    "output",
    "total_optical_path_mm",
    "output_optical_path_mm",
    "output_face_interactions",
    "output_top_interactions",
    "output_bottom_interactions",
    "output_side_interactions",
    "output_incidence_angle_deg_sum",
]
SURFACE_LOCATIONS = (
    "top_surface_absorption",
    "bottom_surface_absorption",
    "side_surface_absorption",
    "black_surface_absorption",
    "other_surface_absorption",
)
FACE_INTERACTIONS = (
    "top_surface_interactions",
    "bottom_surface_interactions",
    "side_surface_interactions",
)


@dataclass(frozen=True)
class B76Config:
    path: Path
    response: B73Config
    states: tuple[str, ...]
    sigma: float
    max_parallel_processes: int
    terminal_channels: tuple[str, ...]


@dataclass(frozen=True)
class StateAudit:
    state: str
    summary: B73Summary
    counts: dict[str, int]
    total_optical_path_mm: float
    output_optical_path_mm: float
    output_face_interactions: int
    output_top_interactions: int
    output_bottom_interactions: int
    output_side_interactions: int
    output_incidence_angle_deg: float

    @property
    def generated(self) -> int:
        return self.summary.full_generated

    @property
    def output(self) -> int:
        return self.summary.full_output

    def fraction(self, channel: str) -> float:
        return self.counts[channel] / self.generated

    @property
    def path_per_generated_mm(self) -> float:
        return self.total_optical_path_mm / self.generated

    @property
    def output_path_per_photon_mm(self) -> float:
        return self.output_optical_path_mm / self.output

    @property
    def output_face_interactions_per_photon(self) -> float:
        return self.output_face_interactions / self.output

    @property
    def output_incidence_angle_deg_mean(self) -> float:
        return self.output_incidence_angle_deg / self.output


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> B76Config:
    path = path.resolve()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("stage") != "B7.6":
        raise ValueError("B7.6 configuration must declare stage=B7.6")
    states = tuple(str(value) for value in raw["states"])
    if states != STATES:
        raise ValueError("B7.6 state order is not the locked audit order")
    sigma = float(raw["shared_sigma_alpha_rad"])
    if sigma != 0.70:
        raise ValueError("B7.6 is locked to sigma_alpha=0.70 rad")
    validation = raw["validation"]
    if not all(bool(value) for value in validation.values()):
        raise ValueError("B7.6 structural validation gates must all be enabled")
    terminal_channels = tuple(str(value) for value in raw["terminal_channels"])
    expected_terminal = {
        "output", "crystal_absorption", "reflector_absorption",
        "other_absorption", *SURFACE_LOCATIONS, "other_world_exit",
    }
    if set(terminal_channels) != expected_terminal:
        raise ValueError("B7.6 terminal channel list is incomplete")
    base = load_b73_config(path.parent / str(raw["b7_3_config"]))
    response = replace(
        base,
        events=int(raw["events"]),
        minimum_full_energy_events=int(validation["minimum_full_energy_events"]),
    )
    if response.events != 100000:
        raise ValueError("B7.6 requires 100000 events per state")
    return B76Config(
        path=path,
        response=response,
        states=states,
        sigma=sigma,
        max_parallel_processes=int(raw["max_parallel_processes"]),
        terminal_channels=terminal_channels,
    )


def event_history(summary: B73Summary) -> tuple[tuple, ...]:
    return tuple(
        (event.event_id, event.source_position_mm, event.edep_kev, event.generated)
        for event in summary.events
    )


def load_state(input_dir: Path, config: B76Config, state: str) -> StateAudit:
    event_path = input_dir / f"{state}.csv"
    audit_path = input_dir / f"{state}_photon_audit.csv"
    summary = load_sample(
        event_path,
        config.response,
        expected_state=state,
        expected_sigma=config.sigma,
    )
    selected = {event.event_id for event in summary.full_energy_events}
    counts = {key: 0 for key in COUNT_COLUMNS}
    with event_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(f"unexpected B7.6 event columns in {event_path}")
        for row in reader:
            if int(row["event_id"]) in selected:
                for key in COUNT_COLUMNS:
                    counts[key] += int(row[key])

    audit_totals = {
        "total_optical_path_mm": 0.0,
        "output_optical_path_mm": 0.0,
        "output_face_interactions": 0,
        "output_top_interactions": 0,
        "output_bottom_interactions": 0,
        "output_side_interactions": 0,
        "output_incidence_angle_deg_sum": 0.0,
    }
    rows = 0
    with audit_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != AUDIT_COLUMNS:
            raise ValueError(f"unexpected B7.6 audit columns in {audit_path}")
        for expected_id, row in enumerate(reader):
            event_id = int(row["event_id"])
            if event_id != expected_id:
                raise ValueError(f"non-contiguous B7.6 audit IDs in {audit_path}")
            generated = int(row["generated"])
            output = int(row["output"])
            event = summary.events[event_id]
            if generated != event.generated or output != event.output:
                raise ValueError(f"B7.6 main/audit count mismatch in {state}/{event_id}")
            total_path = float(row["total_optical_path_mm"])
            output_path = float(row["output_optical_path_mm"])
            face = int(row["output_face_interactions"])
            top = int(row["output_top_interactions"])
            bottom = int(row["output_bottom_interactions"])
            side = int(row["output_side_interactions"])
            angle = float(row["output_incidence_angle_deg_sum"])
            if min(total_path, output_path, face, top, bottom, side, angle) < 0.0:
                raise ValueError(f"negative B7.6 audit value in {state}/{event_id}")
            if output_path > total_path + 1.0e-8 or face != top + bottom + side:
                raise ValueError(f"B7.6 path or face subtotal failed in {state}/{event_id}")
            if angle > 90.0 * output + 1.0e-7:
                raise ValueError(f"B7.6 PMT angle bound failed in {state}/{event_id}")
            if output == 0 and (output_path != 0.0 or face != 0 or angle != 0.0):
                raise ValueError(f"B7.6 zero-output audit failed in {state}/{event_id}")
            if event_id in selected:
                audit_totals["total_optical_path_mm"] += total_path
                audit_totals["output_optical_path_mm"] += output_path
                audit_totals["output_face_interactions"] += face
                audit_totals["output_top_interactions"] += top
                audit_totals["output_bottom_interactions"] += bottom
                audit_totals["output_side_interactions"] += side
                audit_totals["output_incidence_angle_deg_sum"] += angle
            rows += 1
    if rows != config.response.events:
        raise ValueError(f"B7.6 expected {config.response.events} audit rows, found {rows}")

    surface_subtotal = sum(counts[channel] for channel in SURFACE_LOCATIONS)
    terminal_total = sum(counts[channel] for channel in config.terminal_channels)
    if surface_subtotal != counts["surface_absorption"]:
        raise ValueError(f"B7.6 surface subtotal failed for {state}")
    if terminal_total != summary.full_generated:
        raise ValueError(f"B7.6 terminal balance failed for {state}")
    if counts["output"] != summary.full_output:
        raise ValueError(f"B7.6 selected output mismatch for {state}")
    return StateAudit(
        state=state,
        summary=summary,
        counts=counts,
        total_optical_path_mm=float(audit_totals["total_optical_path_mm"]),
        output_optical_path_mm=float(audit_totals["output_optical_path_mm"]),
        output_face_interactions=int(audit_totals["output_face_interactions"]),
        output_top_interactions=int(audit_totals["output_top_interactions"]),
        output_bottom_interactions=int(audit_totals["output_bottom_interactions"]),
        output_side_interactions=int(audit_totals["output_side_interactions"]),
        output_incidence_angle_deg=float(audit_totals["output_incidence_angle_deg_sum"]),
    )


def load_audits(input_dir: Path, config: B76Config) -> dict[str, StateAudit]:
    audits: dict[str, StateAudit] = {}
    reference_history = None
    for state in config.states:
        audit = load_state(input_dir, config, state)
        history = event_history(audit.summary)
        if reference_history is None:
            reference_history = history
        elif history != reference_history:
            raise ValueError(f"B7.6 event history mismatch for {state}")
        audits[state] = audit
    return audits
