#!/usr/bin/env python3
"""Run the six B4 surface states in isolated Geant4 processes."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from b4_common import DEFAULT_CONFIG_PATH, B4Config, load_config, state_filename


def geant_path(path: Path) -> str:
    value = str(path.resolve())
    if any(character.isspace() for character in value):
        raise ValueError("Geant4 B4 paths must not contain whitespace")
    return value


def write_macro(config: B4Config, output_dir: Path, state: str) -> tuple[Path, Path]:
    macro_dir = output_dir / "macros"
    macro_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / state_filename(state)
    b3 = config.b3
    geometry = b3.geometry
    x, y, z = b3.source_position_mm
    lines = [
        "# Generated from config/b4_comparison.json by analysis/run_b4.py.",
        "# One shared roughness value is used; experimental ratios are not inputs.",
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
        f"/gagg/stageB/sigmaAlpha {config.shared_sigma_alpha_rad} rad",
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
    macro_path = macro_dir / f"b4_{state}.mac"
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
    jobs = [write_macro(config, args.output_dir, state) for state in config.states]
    if args.generate_only:
        print(f"[b4-runner] macros={len(jobs)} generate_only=true status=PASS")
        return 0
    executable = args.executable.resolve()
    logs: list[str] = []
    validations = 0
    for index, (macro_path, output_path) in enumerate(jobs, start=1):
        completed = subprocess.run(
            [str(executable), str(macro_path.resolve())],
            text=True,
            capture_output=True,
            check=False,
        )
        process_output = completed.stdout + completed.stderr
        logs.extend([f"===== B4 isolated job {index}/{len(jobs)}: {macro_path.name} =====", process_output])
        failures = [marker for marker in ("status=FAIL", "G4Exception", "Fatal Exception") if marker in process_output]
        marker = f"[output] csv={output_path.resolve()} rows={config.b3.events}"
        if completed.returncode != 0 or failures or marker not in completed.stdout:
            print(process_output[-12000:])
            raise RuntimeError(
                f"B4 job failed: macro={macro_path}, code={completed.returncode}, "
                f"markers={failures}, fresh_output={marker in completed.stdout}"
            )
        validations += completed.stdout.count("[b1] surface_validation")
    log_path = args.output_dir / "b4_run.log"
    log_path.write_text("\n".join(logs), encoding="utf-8")
    if validations != len(jobs):
        raise RuntimeError(f"B4 surface validations={validations}, expected={len(jobs)}")
    print(
        f"[b4-runner] states={len(jobs)} events_per_state={config.b3.events} "
        f"processes={len(jobs)} surface_validations={validations} "
        "process_isolation=true shared_sigma=true status=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
