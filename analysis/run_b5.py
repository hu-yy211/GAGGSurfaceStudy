#!/usr/bin/env python3
"""Run the non-B4 points of the B5 shared-sigma robustness grid."""

from __future__ import annotations

import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from b5_common import DEFAULT_CONFIG_PATH, B5Config, load_config, point_filename, sigma_tag


def geant_path(path: Path) -> str:
    value = str(path.resolve())
    if any(character.isspace() for character in value):
        raise ValueError("Geant4 B5 paths must not contain whitespace")
    return value


def write_macro(config: B5Config, output_dir: Path, state: str, sigma: float) -> tuple[Path, Path]:
    macro_dir = output_dir / "macros"
    macro_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / point_filename(state, sigma)
    b3 = config.b4.b3
    geometry = b3.geometry
    x, y, z = b3.source_position_mm
    lines = [
        "# Generated from config/b5_robustness.json by analysis/run_b5.py.",
        "# Shared-sigma sensitivity point; experimental values are not inputs.",
        "/control/verbose 0",
        "/run/verbose 0",
        "/event/verbose 0",
        "/tracking/verbose 0",
        "/gagg/geometry/mode experiment",
        "/gagg/stageA/surface none",
        f"/gagg/stageB/sideAirGap {geometry['side_air_gap_mm']} mm",
        f"/gagg/stageB/topAirGap {geometry['top_air_gap_mm']} mm",
        f"/gagg/stageB/bottomAirGap {geometry['bottom_air_gap_mm']} mm",
        f"/gagg/stageB/blackHousingThickness {geometry['black_housing_thickness_mm']} mm",
        f"/gagg/stageB/esrThickness {geometry['esr_thickness_mm']} mm",
        f"/gagg/stageB/pmtWindowThickness {geometry['pmt_window_thickness_mm']} mm",
        f"/gagg/stageB/surfaceState {state}",
        f"/gagg/stageB/sigmaAlpha {sigma} rad",
        "/gagg/optics/gaggBulkAbsorption true",
        "/gagg/optics/scintillationTimeConstant 62.53 ns",
        "/gagg/optics/deferScintillationPhotons true",
        "/gagg/scoring/outputMode transmitted",
        "/gagg/source/particle gamma",
        "/gagg/source/mode fixed",
        f"/gagg/source/position {x} {y} {z} mm",
        f"/gagg/source/kineticEnergy {b3.gamma_energy_kev} keV",
        f"/gagg/source/beamRadius {b3.beam_radius_mm} mm",
        f"/gagg/source/eventSeedBase {b3.event_seed_base}",
        "/gagg/output/eventPrintModulo 0",
        "/run/initialize",
        "/gagg/geometry/validate",
        "/gagg/stageB/validate",
        "/gagg/optics/validateScintillation",
        f"/random/setSeeds {b3.run_seeds[0]} {b3.run_seeds[1]}",
        f"/gagg/output/csv {geant_path(output_path)}",
        f"/run/beamOn {b3.events}",
        "",
    ]
    macro_path = macro_dir / f"b5_{state}_sigma{sigma_tag(sigma)}.mac"
    macro_path.write_text("\n".join(lines), encoding="utf-8")
    return macro_path, output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--generate-only", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    jobs = [
        write_macro(config, args.output_dir, state, sigma)
        for sigma in config.run_sigmas
        for state in config.b4.states
    ]
    if args.generate_only:
        print(f"[b5-runner] points={len(jobs)} reused_b4=6 generate_only=true status=PASS")
        return 0
    executable = args.executable.resolve()
    def run_job(index_and_job):
        index, (macro_path, output_path) = index_and_job
        completed = subprocess.run(
            [str(executable), str(macro_path.resolve())],
            text=True,
            capture_output=True,
            check=False,
        )
        process_output = completed.stdout + completed.stderr
        failures = [marker for marker in ("status=FAIL", "G4Exception", "Fatal Exception") if marker in process_output]
        marker = f"[output] csv={output_path.resolve()} rows={config.b4.b3.events}"
        if completed.returncode != 0 or failures or marker not in completed.stdout:
            print(process_output[-12000:])
            raise RuntimeError(
                f"B5 job failed: macro={macro_path}, code={completed.returncode}, "
                f"markers={failures}, fresh_output={marker in completed.stdout}"
            )
        return (
            index,
            f"===== B5 isolated job {index}/{len(jobs)}: {macro_path.name} =====\n{process_output}",
            completed.stdout.count("[b1] surface_validation"),
        )

    with ThreadPoolExecutor(max_workers=config.max_parallel_processes) as executor:
        completed_jobs = list(executor.map(run_job, enumerate(jobs, start=1)))
    completed_jobs.sort(key=lambda item: item[0])
    logs = [item[1] for item in completed_jobs]
    validations = sum(item[2] for item in completed_jobs)
    log_path = args.output_dir / "b5_run.log"
    log_path.write_text("\n".join(logs), encoding="utf-8")
    if validations != len(jobs):
        raise RuntimeError(f"B5 surface validations={validations}, expected={len(jobs)}")
    print(
        f"[b5-runner] points={len(jobs)} reused_b4=6 sigma_points={len(config.sigmas)} "
        f"processes={len(jobs)} max_parallel={config.max_parallel_processes} "
        "shared_sigma=true process_isolation=true status=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
