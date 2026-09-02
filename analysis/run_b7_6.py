#!/usr/bin/env python3
"""Run the B7.6 full-energy photon-fate audit in isolated processes."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import subprocess

from b7_6_common import B76Config, DEFAULT_CONFIG_PATH, STATES, load_config


FINISHES = {
    "all_polished": ("polished", "polished", "polished"),
    "bottom_rough": ("polished", "rough", "polished"),
    "top_rough": ("rough", "polished", "polished"),
    "top_bottom_rough": ("rough", "rough", "polished"),
    "side_rough": ("polished", "polished", "rough"),
}


def geant_path(path: Path) -> str:
    value = str(path.resolve())
    if any(character.isspace() for character in value):
        raise ValueError("Geant4 B7.6 paths must not contain whitespace")
    return value


def write_macro(config: B76Config, output_dir: Path, state: str) -> tuple[Path, Path, Path, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    macro_dir = output_dir / "macros"
    macro_dir.mkdir(parents=True, exist_ok=True)
    event_path = output_dir / f"{state}.csv"
    audit_path = output_dir / f"{state}_photon_audit.csv"
    source = config.response.source
    geometry = config.response.geometry
    x, y, z = source["position_mm"]
    seed1, seed2 = source["run_seeds"]
    lines = [
        "# B7.6 photon-fate audit; transport parameters are unchanged.",
        "/control/verbose 0", "/run/verbose 0", "/event/verbose 0", "/tracking/verbose 0",
        "/gagg/geometry/mode experiment", "/gagg/stageA/surface none",
        f"/gagg/stageB/sideAirGap {geometry['side_air_gap_mm']} mm",
        f"/gagg/stageB/topAirGap {geometry['top_air_gap_mm']} mm",
        f"/gagg/stageB/bottomAirGap {geometry['bottom_air_gap_mm']} mm",
        f"/gagg/stageB/blackHousingThickness {geometry['black_housing_thickness_mm']} mm",
        f"/gagg/stageB/esrThickness {geometry['esr_thickness_mm']} mm",
        f"/gagg/stageB/pmtWindowThickness {geometry['pmt_window_thickness_mm']} mm",
        f"/gagg/stageB/surfaceState {state}",
        f"/gagg/stageB/sigmaAlpha {config.sigma} rad",
        "/gagg/optics/gaggBulkAbsorption true",
        "/gagg/optics/scintillationTimeConstant 62.53 ns",
        "/gagg/optics/deferScintillationPhotons true",
        "/gagg/scoring/outputMode transmitted",
        "/gagg/source/particle annihilationPair", "/gagg/source/mode isotropic",
        f"/gagg/source/position {x} {y} {z} mm",
        f"/gagg/source/faceSize {source['face_size_mm']} mm",
        f"/gagg/source/beamRadius {source['beam_radius_mm']} mm",
        f"/gagg/source/eventSeedBase {source['event_seed_base']}",
        "/gagg/output/eventPrintModulo 0", "/run/initialize",
        "/gagg/geometry/validate", "/gagg/stageB/validate",
        "/gagg/optics/validateScintillation",
        f"/random/setSeeds {seed1} {seed2}",
        f"/gagg/output/csv {geant_path(event_path)}",
        f"/gagg/output/photonAuditCsv {geant_path(audit_path)}",
        f"/run/beamOn {config.response.events}", "",
    ]
    macro_path = macro_dir / f"{state}.mac"
    macro_path.write_text("\n".join(lines), encoding="utf-8")
    return macro_path, event_path, audit_path, state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--jobs", type=int)
    parser.add_argument("--state", action="append", choices=STATES)
    parser.add_argument("--generate-only", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    states = config.states if args.state is None else tuple(args.state)
    if len(set(states)) != len(states):
        raise ValueError("B7.6 states must not be repeated")
    jobs = [write_macro(config, args.output_dir, state) for state in states]
    workers = min(config.max_parallel_processes, len(jobs)) if args.jobs is None else args.jobs
    if not 1 <= workers <= len(jobs):
        raise ValueError("B7.6 --jobs lies outside the valid range")
    if args.generate_only:
        print(f"[b7.6-runner] points={len(jobs)} generate_only=true status=PASS")
        return 0
    executable = args.executable.resolve()

    def execute(job: tuple[Path, Path, Path, str]) -> None:
        macro_path, event_path, audit_path, state = job
        completed = subprocess.run(
            [str(executable), str(macro_path.resolve())],
            text=True,
            capture_output=True,
            check=False,
        )
        output = completed.stdout + completed.stderr
        failures = [marker for marker in ("status=FAIL", "G4Exception", "Fatal Exception") if marker in output]
        if re.search(r"unclassified=[1-9][0-9]*", output):
            failures.append("nonzero unclassified optical photons")
        top, bottom, side = FINISHES[state]
        surface_pattern = (
            rf"\[b1\] surface_validation state={state} top={top} "
            rf"bottom={bottom} side={side} .*status=PASS"
        )
        event_marker = f"[output] csv={event_path.resolve()} rows={config.response.events}"
        audit_marker = f"[output] photon_audit_csv={audit_path.resolve()} rows={config.response.events}"
        if re.search(surface_pattern, output) is None:
            failures.append("incorrect face treatment")
        if completed.returncode != 0 or failures or event_marker not in completed.stdout or audit_marker not in completed.stdout:
            raise RuntimeError(
                f"B7.6 failed: state={state}, code={completed.returncode}, "
                f"failures={failures}, event_fresh={event_marker in completed.stdout}, "
                f"audit_fresh={audit_marker in completed.stdout}"
            )
        event_path.with_suffix(".log").write_text(output, encoding="utf-8")
        print(f"[b7.6-progress] state={state} sigma_rad={config.sigma:g} status=PASS", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        tuple(executor.map(execute, jobs))
    print(
        f"[b7.6-runner] points={len(jobs)} events_per_point={config.response.events} "
        f"sigma_rad={config.sigma:g} separate_audit_csv=true process_isolation=true status=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
