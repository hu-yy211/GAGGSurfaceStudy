# Stage A implementation plan

## Conventions

- Cylinder axis: z.
- Gamma enters at +z and travels toward -z.
- Crystal output face: -z.
- Count a photon once on its first GAGG-to-output crossing, then kill it.
- Event output will contain Edep, N_generated, N_output and loss locations.

## Validation gates

### A0 - Build, optical smoke test and diagnostics - PASSED

Paper-sized GAGG plus one 550 nm photon per event.

Pass: configure, compile, run ten events, zero unclassified terminal outcomes,
pass CTest, open the Qt/OpenGL scene, export an event-level CSV, independently
check photon accounting and generate both diagnostic plots.

Status: passed on 2026-08-23.

### A1 - Materials and units - PASSED

Pass: 550 nm is about 2.254 eV; 0.0155 cm^-1 is 64.516 cm; the future
100 cm^-1 reflector coefficient is 0.1 mm; all optical grids are increasing
and cover the emission energy.

Status: passed on 2026-08-23. The reflector values are validation-only
constants; no reflector solid or optical surface exists yet.

### A2 - Paper geometry - NOT STARTED

Add a 1 mm side sleeve and top cap, leaving the output face open. Start with
direct crystal/reflector adjacency because the paper gives no finite air-gap
thickness even though the finish names contain "air".

Pass: no overlaps, analytic volumes agree, visualization shows an open output
face.

### A3 - Optical transport before scintillation

Use a fixed-count isotropic 550 nm source at controlled positions.

Pass: event-by-event photon accounting closes; fixed seeds reproduce results;
disabling bulk absorption cannot lower collection; position scans are smooth.

### A4 - LUT switching by messenger

Implement "/gagg/stageA/surface" with polishedvm2000air,
polishedtioair, groundvm2000air and groundtioair. Apply changes by geometry
reinitialization, never recompilation.

Pass: four macros use one executable, the run header reports the selected
finish, and installed G4REALSURFACEDATA is loaded.

### A5 - Scintillation validation

Add only a narrow 550 nm component and 54000 photons/MeV.

Pass: N_generated is linear in Edep with the correct slope; photon accounting
closes; integrated counts do not depend on time constants.

### A6 - 662 keV gamma

Add the minimum electromagnetic physics and a normally incident gamma beam.

Pass: full-energy events appear at 662 keV; N_generated/Edep matches the
validated yield; zero-Edep events create no scintillation.

### A7 - Fig. 4

Run identical statistics and fixed seeds for the four LUT finishes.

Pass:

~~~text
groundtioair
  > polishedtioair
  > polishedvm2000air
  > groundvm2000air
~~~

Report confidence intervals. If the order fails, diagnose geometry, surface
assignment, LUT data, counting and event selection before changing parameters.

## Explicit ambiguities

- The paper specifies a reflector material/index but no air-gap thickness.
- Fig. 4 provides distributions, not a numerical table.
- LUT real-surface data are not GAGG-specific: use them for Stage A only.
- The paper's 2% intrinsic resolution is disabled until its role is defined.
