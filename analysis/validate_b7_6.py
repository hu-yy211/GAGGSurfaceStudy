#!/usr/bin/env python3
"""Validate B7.6 paired photon-fate audits and write numerical tables."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from b7_6_common import DEFAULT_CONFIG_PATH, FACE_INTERACTIONS, load_audits, load_config


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    config = load_config(args.config)
    audits = load_audits(args.input_dir, config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    reference = audits["all_polished"]
    if len({len(audit.summary.full_energy_events) for audit in audits.values()}) != 1:
        raise ValueError("B7.6 full-energy counts differ across paired states")
    if len({audit.generated for audit in audits.values()}) != 1:
        raise ValueError("B7.6 generated light differs across paired states")

    budget_path = args.output_dir / "b7_6_terminal_budget.csv"
    budget_fields = [
        "state", "full_energy_events", "generated",
        *[f"count_{channel}" for channel in config.terminal_channels],
        *[f"fraction_{channel}" for channel in config.terminal_channels],
    ]
    with budget_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=budget_fields)
        writer.writeheader()
        for state in config.states:
            audit = audits[state]
            row = {
                "state": state,
                "full_energy_events": len(audit.summary.full_energy_events),
                "generated": audit.generated,
            }
            row.update({f"count_{channel}": audit.counts[channel] for channel in config.terminal_channels})
            row.update({f"fraction_{channel}": f"{audit.fraction(channel):.12f}" for channel in config.terminal_channels})
            writer.writerow(row)

    transport_path = args.output_dir / "b7_6_transport_metrics.csv"
    transport_fields = [
        "state", "total_path_per_generated_mm", "output_path_per_photon_mm",
        "output_face_interactions_per_photon",
        "output_top_interactions_per_photon",
        "output_bottom_interactions_per_photon",
        "output_side_interactions_per_photon",
        "output_incidence_angle_deg_mean",
    ]
    with transport_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=transport_fields)
        writer.writeheader()
        for state in config.states:
            audit = audits[state]
            writer.writerow({
                "state": state,
                "total_path_per_generated_mm": f"{audit.path_per_generated_mm:.12f}",
                "output_path_per_photon_mm": f"{audit.output_path_per_photon_mm:.12f}",
                "output_face_interactions_per_photon": f"{audit.output_face_interactions_per_photon:.12f}",
                "output_top_interactions_per_photon": f"{audit.output_top_interactions / audit.output:.12f}",
                "output_bottom_interactions_per_photon": f"{audit.output_bottom_interactions / audit.output:.12f}",
                "output_side_interactions_per_photon": f"{audit.output_side_interactions / audit.output:.12f}",
                "output_incidence_angle_deg_mean": f"{audit.output_incidence_angle_deg_mean:.12f}",
            })

    delta_path = args.output_dir / "b7_6_delta_budget.csv"
    delta_fields = [
        "state", *[f"delta_fraction_{channel}" for channel in config.terminal_channels],
        "dominant_loss_channel", "dominant_loss_delta_fraction",
    ]
    with delta_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=delta_fields)
        writer.writeheader()
        for state in config.states[1:]:
            audit = audits[state]
            deltas = {
                channel: audit.fraction(channel) - reference.fraction(channel)
                for channel in config.terminal_channels
            }
            if abs(sum(deltas.values())) > 2.0e-12:
                raise ValueError(f"B7.6 differential terminal balance failed for {state}")
            loss_channels = tuple(channel for channel in config.terminal_channels if channel != "output")
            dominant = max(loss_channels, key=lambda channel: abs(deltas[channel]))
            row = {"state": state}
            row.update({f"delta_fraction_{channel}": f"{deltas[channel]:.12f}" for channel in config.terminal_channels})
            row["dominant_loss_channel"] = dominant
            row["dominant_loss_delta_fraction"] = f"{deltas[dominant]:.12f}"
            writer.writerow(row)
            print(
                f"[b7.6-delta] state={state} delta_output={deltas['output']:+.8f} "
                f"dominant={dominant} delta_dominant={deltas[dominant]:+.8f} "
                "balance=closed"
            )

    for state in config.states:
        audit = audits[state]
        if audit.output_face_interactions < audit.output:
            raise ValueError(f"B7.6 output photons lack crystal-face crossings for {state}")
        if audit.counts["reflector_absorption"] != 0:
            raise ValueError(f"B7.6 Stage-A reflector absorption appeared for {state}")
        print(
            f"[b7.6-transport] state={state} output_fraction={audit.fraction('output'):.8f} "
            f"path_per_generated_mm={audit.path_per_generated_mm:.6f} "
            f"output_path_mm={audit.output_path_per_photon_mm:.6f} "
            f"output_face_hits={audit.output_face_interactions_per_photon:.6f} "
            f"pmt_angle_deg={audit.output_incidence_angle_deg_mean:.6f}"
        )
    print(f"[b7.6-check] wrote={budget_path}")
    print(f"[b7.6-check] wrote={transport_path}")
    print(f"[b7.6-check] wrote={delta_path}")
    print(
        f"[b7.6-check] states={len(audits)} events_per_state={config.response.events} "
        f"full_events={len(reference.summary.full_energy_events)} pairing=exact "
        "terminal_balance=closed output_audit=matched status=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
