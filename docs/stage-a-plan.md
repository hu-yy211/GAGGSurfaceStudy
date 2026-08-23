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

### A2 - Paper geometry - PASSED

Add a 1 mm side sleeve and top cap, leaving the output face open. Start with
direct crystal/reflector adjacency because the paper gives no finite air-gap
thickness even though the finish names contain "air".

Pass: no overlaps, analytic volumes agree, visualization shows an open output
face.

Status: passed on 2026-08-23. The `bare` and `paper` modes are selectable by
macro. Navigator probes identify the crystal, side reflector, top reflector
and open output region correctly. No LUT optical surface exists yet.

### A3 - Optical transport before scintillation - PASSED

Use a fixed-count isotropic 550 nm source at controlled positions.

Pass: event-by-event photon accounting closes; fixed seeds reproduce results;
disabling bulk absorption cannot lower collection; position scans are smooth.

Status: passed on 2026-08-23. The center run reproduced exactly row by row,
all 20,000-photon direction samples passed first/second-moment isotropy checks,
and all events closed with zero unclassified photons. Disabling GAGG
self-absorption changed `N_output/N_generated` from 0.17065 to 0.17800. The
five-point axial scan had no upward reversal larger than 3 sigma.

### A4 - LUT switching by messenger - PASSED

Implement "/gagg/stageA/surface" with polishedvm2000air,
polishedtioair, groundvm2000air and groundtioair. Apply changes by geometry
reinitialization, never recompilation.

Pass: one macro switches all four finishes in one executable, every run header
reports the selected finish, and installed G4REALSURFACEDATA is loaded.

Status: passed on 2026-08-23. Two directional GAGG-to-reflector border
surfaces share the selected LBNL LUT. Switching at Idle requests full geometry
reinitialization; the comparison macro initializes and validates the rebuilt
border table before every run. All four runs had nonzero LUT interactions,
closed photon accounting and zero unclassified photons. Switching back to
`polishedvm2000air` reproduced all 50 event rows exactly. The A4 output order
is recorded but is not a pass criterion before A7.

### A5 - Scintillation validation - PASSED

Add only a narrow 550 nm component and 54000 photons/MeV.

Pass: N_generated is linear in Edep with the correct slope; photon accounting
closes; integrated counts do not depend on time constants.

Status: passed on 2026-08-23. A controlled 10/20/40 keV electron source
deposited its full energy in GAGG and generated 540/1080/2160 photons per
event. The fitted slope was exactly 54000 photons/MeV, all terminal accounting
closed, and every generated secondary was created by `Scintillation`.
Changing the single-component constant from 62.53 ns to 190.89 ns changed the
integrated yield by 4.63e-5 relative; output efficiencies differed by only
0.150 sigma. Cerenkov production is disabled. No gamma source exists yet.

### A6 - 662 keV gamma - PASSED

Add the minimum electromagnetic physics and a normally incident gamma beam.

Pass: full-energy events appear at 662 keV; N_generated/Edep matches the
validated yield; zero-Edep events create no scintillation.

Status: passed on 2026-08-23. A fixed-seed 100-event normally incident gamma
sample contained 42 events in the 661.5-662.5 keV full-energy gate, 30
partial-energy events and 28 zero-deposit events. The full-energy subset gave
53999.784 photons/MeV, every zero-deposit event generated zero photons and all
optical terminal accounting closed. The source is a monoenergetic particle
gun; radioactive decay and detector energy resolution remain out of scope.

### A7 - Fig. 4 - IN PROGRESS, ORDERING GATE FAILED

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

Current status: not passed on 2026-08-23. A paired 100-primary comparison had
33 identical full-energy events per finish. Source position, Edep and
N_generated matched event by event and all optical accounting closed, but the
observed mean order was `groundvm2000air > polishedvm2000air > groundtioair >
polishedtioair`. The paper's target failed with confidence intervals entirely
in the wrong direction for two adjacent pairs. The audit added the paper's
0.98/0.95 reflector lower bounds because the legacy LUT otherwise defaults to
unit reflectivity. Uniform-face irradiation, random-stream isolation, a LUT
default-reflectivity control and a ten-times-shorter absorption-length unit
diagnostic did not recover the target. No parameter was fitted and no `a7`
milestone tag may be created yet.

A bounded follow-up separated direct versus explicit 0.1 mm air connection
and first-arrival versus true boundary-transmission scoring. All four
50-primary paired models passed geometry, pairing and accounting validation;
none passed the Fig. 4 order. True transmission was identified by
`G4OpBoundaryProcess` status rather than post-volume name, which can still
name the candidate next volume on a reflected boundary step. It reduced the
direct-model full-energy mean counts to 6564, 9948, 14698 and 10367 for
polished VM2000, polished TiO, ground VM2000 and ground TiO. This recovered
`ground TiO > polished TiO > polished VM` and improved the absolute scale,
but ground VM2000 remained highest rather than lowest. The explicit air
volume changed efficiencies only by a few (10^{-3}), so no thickness scan
or fit was performed. Stage B may proceed independently, but A7 remains open
and untagged.

## Explicit ambiguities

- The paper specifies a reflector material/index but no air-gap thickness.
- Fig. 4 provides distributions, not a numerical table.
- LUT real-surface data are not GAGG-specific: use them for Stage A only.
- The paper's 2% intrinsic resolution is disabled until its role is defined.
