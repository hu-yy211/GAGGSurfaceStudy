#!/usr/bin/env python3
"""Generate and execute the controlled B3 511 keV gamma run."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from b3_common import DEFAULT_CONFIG_PATH, B3Config, load_config


def geant_path(path: Path) -> str:
    value = str(path.resolve())
    if any(character.isspace() for character in value):
        raise ValueError("Geant4 B3 paths must not contain whitespace")
    return value


def write_macro(config: B3Config, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    macro_dir = output_dir / "macros"
    macro_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "gamma_511kev_all_polished.csv"
    geometry = config.geometry
    x, y, z = config.source_position_mm
    lines = [
        "# Generated from config/b3_gamma.json by analysis/run_b3.py.",
        "# B3 validates gamma/scintillation before comparing surface states.",
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
        f"/gagg/stageB/surfaceState {config.surface_state}",
        f"/gagg/stageB/sigmaAlpha {config.sigma_alpha_rad} rad",
        "/gagg/optics/gaggBulkAbsorption true",
        "/gagg/optics/scintillationTimeConstant 62.53 ns",
        "/gagg/optics/deferScintillationPhotons true",
        "/gagg/scoring/outputMode transmitted",
        "/gagg/source/particle gamma",
        "/gagg/source/mode fixed",
        f"/gagg/source/position {x} {y} {z} mm",
        f"/gagg/source/kineticEnergy {config.gamma_energy_kev} keV",
        f"/gagg/source/beamRadius {config.beam_radius_mm} mm",
        f"/gagg/source/eventSeedBase {config.event_seed_base}",
        "/gagg/output/eventPrintModulo 0",
        "/run/initialize",
        "/gagg/geometry/validate",
        "/gagg/stageB/validate",
        "/gagg/optics/validateScintillation",
        f"/random/setSeeds {config.run_seeds[0]} {config.run_seeds[1]}",
        f"/gagg/output/csv {geant_path(output_path)}",
        f"/run/beamOn {config.events}",
        "",
    ]
    macro_path = macro_dir / "b3_gamma_511.mac"
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
    macro_path, output_path = write_macro(config, args.output_dir)
    if args.generate_only:
        print(f"[b3-runner] macro={macro_path} generate_only=true status=PASS")
        return 0
    completed = subprocess.run(
        [str(args.executable.resolve()), str(macro_path.resolve())],
        text=True,
        capture_output=True,
        check=False,
    )
    process_output = completed.stdout + completed.stderr
    (args.output_dir / "b3_run.log").write_text(process_output, encoding="utf-8")
    failures = [
        marker
        for marker in ("status=FAIL", "G4Exception", "Fatal Exception")
        if marker in process_output
    ]
    expected_marker = f"[output] csv={output_path.resolve()} rows={config.events}"
    if completed.returncode != 0 or failures or expected_marker not in completed.stdout:
        print(process_output[-12000:])
        raise RuntimeError(
            f"B3 run failed: code={completed.returncode}, markers={failures}, "
            f"fresh_output={expected_marker in completed.stdout}"
        )
    print(
        f"[b3-runner] output={output_path} events={config.events} "
        "gamma_keV=511 deferred_scintillation=true status=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
