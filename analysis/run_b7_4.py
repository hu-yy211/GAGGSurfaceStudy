#!/usr/bin/env python3
"""Run the B7.4 coarse shared-sigma scan in isolated Geant4 processes."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import subprocess

from b7_4_common import DEFAULT_CONFIG_PATH, B74Config, load_config, point_path, sigma_tag


def geant_path(path: Path) -> str:
    value = str(path.resolve())
    if any(character.isspace() for character in value):
        raise ValueError("Geant4 B7.4 paths must not contain whitespace")
    return value


def write_macro(config: B74Config, output_dir: Path, state: str, sigma: float) -> tuple[Path, Path, str, float]:
    output_path = point_path(output_dir, state, sigma, config.reference_sigma)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    macro_dir = output_dir / "macros"
    macro_dir.mkdir(parents=True, exist_ok=True)
    response = config.response
    source = response.source
    geometry = response.geometry
    x, y, z = source["position_mm"]
    seed1, seed2 = source["run_seeds"]
    lines = [
        "# B7.4 generated shared-sigma scan point; no per-face fitting.",
        "/control/verbose 0", "/run/verbose 0", "/event/verbose 0", "/tracking/verbose 0",
        "/gagg/geometry/mode experiment", "/gagg/stageA/surface none",
        f"/gagg/stageB/sideAirGap {geometry['side_air_gap_mm']} mm",
        f"/gagg/stageB/topAirGap {geometry['top_air_gap_mm']} mm",
        f"/gagg/stageB/bottomAirGap {geometry['bottom_air_gap_mm']} mm",
        f"/gagg/stageB/blackHousingThickness {geometry['black_housing_thickness_mm']} mm",
        f"/gagg/stageB/esrThickness {geometry['esr_thickness_mm']} mm",
        f"/gagg/stageB/pmtWindowThickness {geometry['pmt_window_thickness_mm']} mm",
        f"/gagg/stageB/surfaceState {state}", f"/gagg/stageB/sigmaAlpha {sigma} rad",
        "/gagg/optics/gaggBulkAbsorption true", "/gagg/optics/scintillationTimeConstant 62.53 ns",
        "/gagg/optics/deferScintillationPhotons true", "/gagg/scoring/outputMode transmitted",
        "/gagg/source/particle annihilationPair", "/gagg/source/mode isotropic",
        f"/gagg/source/position {x} {y} {z} mm", f"/gagg/source/faceSize {source['face_size_mm']} mm",
        f"/gagg/source/beamRadius {source['beam_radius_mm']} mm",
        f"/gagg/source/eventSeedBase {source['event_seed_base']}", "/gagg/output/eventPrintModulo 0",
        "/run/initialize", "/gagg/geometry/validate", "/gagg/stageB/validate",
        "/gagg/optics/validateScintillation", f"/random/setSeeds {seed1} {seed2}",
        f"/gagg/output/csv {geant_path(output_path)}", f"/run/beamOn {response.events}", "",
    ]
    name = "all_polished" if state == "all_polished" else f"sigma{sigma_tag(sigma)}_{state}"
    macro_path = macro_dir / f"{name}.mac"
    macro_path.write_text("\n".join(lines), encoding="utf-8")
    return macro_path, output_path, state, sigma


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--generate-only", action="store_true")
    parser.add_argument("--jobs", type=int)
    args = parser.parse_args()
    config = load_config(args.config)
    jobs = [write_macro(config, args.output_dir, "all_polished", config.reference_sigma)]
    jobs.extend(
        write_macro(config, args.output_dir, state, sigma)
        for sigma in config.sigmas for state in config.states[1:]
    )
    workers = config.max_parallel_processes if args.jobs is None else args.jobs
    if not 1 <= workers <= len(jobs):
        raise ValueError("B7.4 --jobs lies outside the valid range")
    if args.generate_only:
        print(f"[b7.4-runner] points={len(jobs)} sigmas={len(config.sigmas)} jobs={workers} generate_only=true status=PASS")
        return 0
    executable = args.executable.resolve()

    def execute(index_and_job):
        index, (macro_path, output_path, state, sigma) = index_and_job
        completed = subprocess.run([str(executable), str(macro_path.resolve())], text=True, capture_output=True, check=False)
        output = completed.stdout + completed.stderr
        failures = [marker for marker in ("status=FAIL", "G4Exception", "Fatal Exception") if marker in output]
        if re.search(r"unclassified=[1-9][0-9]*", output):
            failures.append("nonzero unclassified optical photons")
        marker = f"[output] csv={output_path.resolve()} rows={config.response.events}"
        if completed.returncode != 0 or failures or marker not in completed.stdout:
            raise RuntimeError(
                f"B7.4 point failed: state={state}, sigma={sigma}, code={completed.returncode}, failures={failures}, fresh={marker in completed.stdout}"
            )
        log_path = output_path.with_suffix(".log")
        log_path.write_text(output, encoding="utf-8")
        print(f"[b7.4-progress] point={index}/{len(jobs)} state={state} sigma={sigma:g} status=PASS", flush=True)
        return completed.stdout.count("[b1] surface_validation")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        validations = sum(executor.map(execute, enumerate(jobs, start=1)))
    if validations != len(jobs):
        raise RuntimeError(f"B7.4 surface validations={validations}, expected={len(jobs)}")
    print(
        f"[b7.4-runner] points={len(jobs)} sigmas={len(config.sigmas)} states={len(config.states)} "
        f"events_per_point={config.response.events} jobs={workers} all_polished_runs=1 "
        "shared_sigma=true per_face_sigma=false process_isolation=true status=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
