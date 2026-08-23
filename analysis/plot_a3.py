#!/usr/bin/env python3
"""Create A3 transport-validation plots."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from validate_a3 import load_summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    center = load_summary(args.input_dir / "center_a.csv", 0.0)
    no_absorption = load_summary(
        args.input_dir / "center_no_absorption.csv", 0.0
    )
    scan = [
        (-10.0, load_summary(args.input_dir / "z_m10.csv", -10.0)),
        (-5.0, load_summary(args.input_dir / "z_m5.csv", -5.0)),
        (0.0, center),
        (5.0, load_summary(args.input_dir / "z_p5.csv", 5.0)),
        (10.0, load_summary(args.input_dir / "z_p10.csv", 10.0)),
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    positions = [position for position, _ in scan]
    efficiencies = [summary.efficiency for _, summary in scan]
    errors = [summary.standard_error for _, summary in scan]
    fig, axis = plt.subplots(figsize=(8.2, 5.2))
    axis.errorbar(
        positions,
        efficiencies,
        yerr=errors,
        marker="o",
        linewidth=2.0,
        capsize=4,
        color="#2878B5",
    )
    axis.set_xlabel("Source z position (mm)")
    axis.set_ylabel("N_output / N_generated")
    axis.set_title("A3 axial position scan")
    axis.grid(alpha=0.25)
    fig.tight_layout()
    position_output = args.output_dir / "a3_position_scan.png"
    fig.savefig(position_output, dpi=180)
    plt.close(fig)

    labels = [
        "Output",
        "GAGG absorption",
        "Reflector absorption",
        "Other absorption",
        "Other world exit",
    ]
    values = [
        center.output,
        center.crystal_absorption,
        center.reflector_absorption,
        center.other_absorption,
        center.other_world_exit,
    ]
    fig, axis = plt.subplots(figsize=(10.0, 5.4))
    bars = axis.bar(
        labels,
        values,
        color=["#2878B5", "#D95F02", "#7A5195", "#777777", "#6A994E"],
    )
    axis.set_ylabel("Optical photons")
    axis.set_title("A3 center-source terminal outcomes")
    axis.grid(axis="y", alpha=0.25)
    axis.set_axisbelow(True)
    axis.set_ylim(0.0, max(values) * 1.18)
    plt.setp(axis.get_xticklabels(), rotation=15, ha="right")
    for bar, value in zip(bars, values):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value}\n({100.0 * value / center.generated:.1f}%)",
            ha="center",
            va="bottom",
        )
    fig.tight_layout()
    terminal_output = args.output_dir / "a3_terminal_outcomes.png"
    fig.savefig(terminal_output, dpi=180)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(7.2, 5.0))
    absorption_values = [center.efficiency, no_absorption.efficiency]
    absorption_errors = [center.standard_error, no_absorption.standard_error]
    axis.bar(
        ["Literature absorption", "GAGG absorption disabled"],
        absorption_values,
        yerr=absorption_errors,
        capsize=5,
        color=["#D95F02", "#2878B5"],
    )
    axis.set_ylabel("N_output / N_generated")
    axis.set_title("A3 bulk-absorption control")
    axis.grid(axis="y", alpha=0.25)
    axis.set_axisbelow(True)
    fig.tight_layout()
    absorption_output = args.output_dir / "a3_absorption_control.png"
    fig.savefig(absorption_output, dpi=180)
    plt.close(fig)

    for output in (position_output, terminal_output, absorption_output):
        print(f"[a3-plot] wrote={output}")
    print("[a3-plot] status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
