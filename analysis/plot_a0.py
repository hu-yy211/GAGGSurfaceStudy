#!/usr/bin/env python3
"""Create A0 validation plots from the event-level CSV."""

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_rows(path: Path) -> list[dict[str, int]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        required = {
            "event_id",
            "generated",
            "world_exit",
            "bulk_absorption",
            "unclassified",
        }
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"unexpected CSV columns: {reader.fieldnames}")
        return [
            {key: int(row[key]) for key in required}
            for row in reader
        ]


def plot_terminal_outcomes(rows: list[dict[str, int]], output: Path) -> None:
    labels = ["World exit", "Bulk absorption", "Unclassified"]
    values = [
        sum(row["world_exit"] for row in rows),
        sum(row["bulk_absorption"] for row in rows),
        sum(row["unclassified"] for row in rows),
    ]
    colors = ["#2878B5", "#D95F02", "#777777"]
    total = sum(row["generated"] for row in rows)

    fig, axis = plt.subplots(figsize=(8.2, 5.2))
    bars = axis.bar(labels, values, color=colors, width=0.62)
    axis.set_ylabel("Optical photons")
    axis.set_title("A0 terminal outcomes")
    axis.grid(axis="y", alpha=0.25)
    axis.set_axisbelow(True)
    for bar, value in zip(bars, values):
        fraction = 100.0 * value / total if total else 0.0
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value}\n({fraction:.1f}%)",
            ha="center",
            va="bottom",
        )
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def plot_accounting(rows: list[dict[str, int]], output: Path) -> None:
    event_ids: list[int] = []
    generated: list[int] = []
    classified: list[int] = []
    unclassified: list[int] = []
    generated_total = classified_total = unclassified_total = 0

    for row in rows:
        generated_total += row["generated"]
        classified_total += row["world_exit"] + row["bulk_absorption"]
        unclassified_total += row["unclassified"]
        event_ids.append(row["event_id"] + 1)
        generated.append(generated_total)
        classified.append(classified_total)
        unclassified.append(unclassified_total)

    fig, axis = plt.subplots(figsize=(8.2, 5.2))
    axis.plot(event_ids, generated, label="Generated", linewidth=2.6)
    axis.plot(
        event_ids,
        classified,
        label="Classified terminal outcomes",
        linewidth=1.8,
        linestyle="--",
    )
    axis.plot(event_ids, unclassified, label="Unclassified", linewidth=1.8)
    axis.set_xlabel("Events processed")
    axis.set_ylabel("Cumulative optical photons")
    axis.set_title("A0 photon-accounting closure")
    axis.grid(alpha=0.25)
    axis.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=180)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    rows = load_rows(args.input)
    if not rows:
        raise ValueError("CSV contains no event rows")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outcomes = args.output_dir / "a0_terminal_outcomes.png"
    accounting = args.output_dir / "a0_photon_accounting.png"
    plot_terminal_outcomes(rows, outcomes)
    plot_accounting(rows, accounting)

    print(f"[plot] wrote={outcomes}")
    print(f"[plot] wrote={accounting}")
    print("[plot] status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
