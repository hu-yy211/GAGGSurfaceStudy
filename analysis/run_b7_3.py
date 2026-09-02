#!/usr/bin/env python3
"""Run the locked 100k-event B7.3 all-polished response sample."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from b7_3_common import DEFAULT_CONFIG_PATH, load_config


def geant_path(path: Path) -> str:
    value = str(path.resolve())
    if any(character.isspace() for character in value):
        raise ValueError("Geant4 B7.3 paths must not contain whitespace")
    return value


def write_macro(config_path: Path, output_dir: Path) -> tuple[Path, Path, int]:
    config = load_config(config_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    macro_dir = output_dir / "macros"
    macro_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "annihilation_pair_all_polished.csv"
    source = config.source
    geometry = config.geometry
    x, y, z = source["position_mm"]
    seed1, seed2 = source["run_seeds"]
    lines = [
        "# Generated from config/b7_3_full_energy_response.json.",
        "# B7.3 validates event-level 511 keV selection; it does not scan sigma_alpha.",
        "/control/verbose 0", "/run/verbose 0", "/event/verbose 0", "/tracking/verbose 0",
        "/gagg/geometry/mode experiment", "/gagg/stageA/surface none",
        f"/gagg/stageB/sideAirGap {geometry['side_air_gap_mm']} mm",
        f"/gagg/stageB/topAirGap {geometry['top_air_gap_mm']} mm",
        f"/gagg/stageB/bottomAirGap {geometry['bottom_air_gap_mm']} mm",
        f"/gagg/stageB/blackHousingThickness {geometry['black_housing_thickness_mm']} mm",
        f"/gagg/stageB/esrThickness {geometry['esr_thickness_mm']} mm",
        f"/gagg/stageB/pmtWindowThickness {geometry['pmt_window_thickness_mm']} mm",
        f"/gagg/stageB/surfaceState {config.state}",
        f"/gagg/stageB/sigmaAlpha {config.sigma_alpha_rad} rad",
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
        f"/gagg/output/csv {geant_path(output_path)}",
        f"/run/beamOn {config.events}", "",
    ]
    macro_path = macro_dir / "b7_3_full_energy_response.mac"
    macro_path.write_text("\n".join(lines), encoding="utf-8")
    return macro_path, output_path, config.events


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--generate-only", action="store_true")
    args = parser.parse_args()
    macro_path, output_path, events = write_macro(args.config, args.output_dir)
    if args.generate_only:
        print(f"[b7.3-runner] macro={macro_path} generate_only=true status=PASS")
        return 0
    completed = subprocess.run(
        [str(args.executable.resolve()), str(macro_path.resolve())],
        text=True, capture_output=True, check=False,
    )
    process_output = completed.stdout + completed.stderr
    (args.output_dir / "b7_3_run.log").write_text(process_output, encoding="utf-8")
    failures = [marker for marker in ("status=FAIL", "G4Exception", "Fatal Exception") if marker in process_output]
    marker = f"[output] csv={output_path.resolve()} rows={events}"
    if completed.returncode != 0 or failures or marker not in completed.stdout:
        print(process_output[-12000:])
        raise RuntimeError(
            f"B7.3 run failed: code={completed.returncode}, markers={failures}, fresh_output={marker in completed.stdout}"
        )
    print(
        f"[b7.3-runner] output={output_path} events={events} "
        "source=annihilationPair process_isolation=true status=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
