#!/usr/bin/env python3
"""Generate and run isolated B2 Geant4 macros from the locked JSON grid."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from b2_common import (
    DEFAULT_CONFIG_PATH,
    B2Config,
    PositionPoint,
    SigmaPoint,
    load_config,
    point_filename,
    repeat_filename,
)


def geant_path(path: Path) -> str:
    value = str(path.resolve())
    if any(character.isspace() for character in value):
        raise ValueError("Geant4 B2 paths must not contain whitespace")
    return value


def common_lines(config: B2Config) -> list[str]:
    geometry = config.geometry
    return [
        "# Generated from config/b2_scan.json by analysis/run_b2_scan.py.",
        "# B2 is optical-only and does not select or fit sigma_alpha.",
        "/control/verbose 0",
        "/run/verbose 0",
        "/event/verbose 0",
        "/tracking/verbose 0",
        "/gagg/geometry/mode experiment",
        "/gagg/stageA/surface none",
        f"/gagg/stageB/sideAirGap {geometry['side_air_gap_mm']} mm",
        "/gagg/stageB/blackHousingThickness "
        f"{geometry['black_housing_thickness_mm']} mm",
        f"/gagg/stageB/esrThickness {geometry['esr_thickness_mm']} mm",
        "/gagg/stageB/pmtWindowThickness "
        f"{geometry['pmt_window_thickness_mm']} mm",
        "/gagg/optics/gaggBulkAbsorption true",
        "/gagg/scoring/outputMode transmitted",
        "/gagg/source/particle optical",
        "/gagg/source/mode isotropic",
        f"/gagg/source/photonsPerEvent {config.photons_per_event}",
        f"/gagg/source/eventSeedBase {config.event_seed_base}",
        "/gagg/output/eventPrintModulo 0",
    ]


def write_point_macro(
    config: B2Config,
    macro_dir: Path,
    output_path: Path,
    state: str,
    position: PositionPoint,
    sigma: SigmaPoint,
) -> Path:
    x, y, z = position.xyz_mm
    lines = common_lines(config)
    lines.extend(
        [
            f"/gagg/source/position {x} {y} {z} mm",
            f"/gagg/stageB/surfaceState {state}",
            f"/gagg/stageB/sigmaAlpha {sigma.value_rad} rad",
            "/run/initialize",
            "/gagg/stageB/validate",
            "/geometry/navigator/reset",
            f"/random/setSeeds {config.run_seeds[0]} {config.run_seeds[1]}",
            f"/gagg/output/csv {geant_path(output_path)}",
            f"/run/beamOn {config.events_per_point}",
            "",
        ]
    )
    macro_path = macro_dir / f"{output_path.stem}.mac"
    macro_path.write_text("\n".join(lines), encoding="utf-8")
    return macro_path


def build_macros(
    config_path: Path, output_dir: Path
) -> tuple[B2Config, list[tuple[Path, Path]]]:
    config = load_config(config_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    macro_dir = output_dir / "macros"
    macro_dir.mkdir(parents=True, exist_ok=True)
    jobs: list[tuple[Path, Path]] = []
    for state in config.states:
        for sigma in config.sigmas:
            for position in config.positions:
                output_path = output_dir / point_filename(
                    state, position.tag, sigma.tag
                )
                jobs.append(
                    (
                        write_point_macro(
                            config,
                            macro_dir,
                            output_path,
                            state,
                            position,
                            sigma,
                        ),
                        output_path,
                    )
                )

    repeat = config.repeat
    repeat_output = output_dir / repeat_filename(config)
    jobs.append(
        (
            write_point_macro(
                config,
                macro_dir,
                repeat_output,
                repeat.state,
                config.position(repeat.position_tag),
                config.sigma(repeat.sigma_tag),
            ),
            repeat_output,
        )
    )
    return config, jobs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--generate-only", action="store_true")
    args = parser.parse_args()

    config, jobs = build_macros(args.config, args.output_dir)
    macro_dir = args.output_dir / "macros"
    if args.generate_only:
        print(
            f"[b2-runner] macro_dir={macro_dir} points={config.point_count} "
            "repeat=1 process_isolation=true generate_only=true status=PASS"
        )
        return 0

    executable = args.executable.resolve()
    if not executable.is_file():
        raise FileNotFoundError(f"Geant4 executable not found: {executable}")

    full_log: list[str] = []
    surface_validations = 0
    failure_markers = ("status=FAIL", "G4Exception", "Fatal Exception")
    for index, (macro_path, output_path) in enumerate(jobs, start=1):
        completed = subprocess.run(
            [str(executable), str(macro_path.resolve())],
            text=True,
            capture_output=True,
            check=False,
        )
        process_output = completed.stdout + completed.stderr
        full_log.extend(
            [
                f"===== B2 isolated job {index}/{len(jobs)}: {macro_path.name} =====",
                process_output,
            ]
        )
        failures = [
            marker for marker in failure_markers if marker in process_output
        ]
        output_marker = (
            f"[output] csv={output_path.resolve()} "
            f"rows={config.events_per_point}"
        )
        output_fresh = output_marker in completed.stdout
        if (
            completed.returncode != 0
            or failures
            or not output_path.is_file()
            or not output_fresh
        ):
            print(process_output[-12000:])
            raise RuntimeError(
                f"B2 job failed: macro={macro_path}, code={completed.returncode}, "
                f"markers={failures}, output_exists={output_path.is_file()}, "
                f"output_fresh={output_fresh}"
            )
        surface_validations += completed.stdout.count(
            "[b1] surface_validation"
        )

    log_path = args.output_dir / "b2_run.log"
    log_path.write_text("\n".join(full_log), encoding="utf-8")
    if surface_validations != len(jobs):
        raise RuntimeError(
            "B2 isolated jobs did not each validate their surface: "
            f"{surface_validations}/{len(jobs)}"
        )
    print(
        f"[b2-runner] macro_dir={macro_dir} log={log_path} "
        f"points={config.point_count} repeat=1 processes={len(jobs)} "
        f"surface_validations={surface_validations} process_isolation=true "
        "optical_only=true selected_sigma=false status=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
