#!/usr/bin/env python3
"""Summarize structurally valid A7 diagnostic model comparisons."""

import argparse
import csv
from pathlib import Path

from validate_a7 import FIG4_ORDER, SURFACES, load_comparison, ordering_matches


MODELS = (
    "direct_transmitted",
    "direct_first_arrival",
    "airgap_transmitted",
    "airgap_first_arrival",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--expect-events", type=int, default=50)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rows: list[dict[str, object]] = []
    reproduced = []
    for model in MODELS:
        summaries = load_comparison(
            args.input_dir / model, args.expect_events
        )
        observed = sorted(
            SURFACES,
            key=lambda surface: summaries[surface].mean_efficiency,
            reverse=True,
        )
        match = ordering_matches(summaries)
        if match:
            reproduced.append(model)
        print(
            f"[a7-model] model={model} full_events="
            f"{len(summaries[SURFACES[0]].full_events)} "
            f"observed_order={'>'.join(observed)} "
            f"expected_order={'>'.join(FIG4_ORDER)} "
            f"fig4_order={'PASS' if match else 'FAIL'}"
        )
        for surface in SURFACES:
            summary = summaries[surface]
            ci_low, ci_high = summary.ci95
            rows.append(
                {
                    "model": model,
                    "surface": surface,
                    "full_events": len(summary.full_events),
                    "mean_efficiency": f"{summary.mean_efficiency:.10f}",
                    "ci95_low": f"{ci_low:.10f}",
                    "ci95_high": f"{ci_high:.10f}",
                    "mean_output": f"{summary.mean_output:.3f}",
                    "fig4_order": "PASS" if match else "FAIL",
                }
            )
            print(
                f"[a7-model] model={model} surface={surface} "
                f"mean_efficiency={summary.mean_efficiency:.8f} "
                f"ci95=[{ci_low:.8f},{ci_high:.8f}] "
                f"mean_output={summary.mean_output:.3f}"
            )

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"[a7-model] summary_csv={args.output}")

    print(
        "[a7-model] structural_validation=PASS reproduced_models="
        + (",".join(reproduced) if reproduced else "none")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
