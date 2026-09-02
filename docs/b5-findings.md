# B5 robustness findings and model boundary

## What the current simulation establishes

The six 511 keV samples are event-paired: source position, gamma energy
deposit, scintillation count and full-energy event IDs are identical for every
surface state and shared-roughness value. Optical terminal accounting closes
exactly. The preliminary experimental ratios are never supplied to Geant4.

Across the predeclared shared `sigma_alpha = 0.10, 0.20, 0.30 rad` grid, the
five non-reference measured ratios all remain outside their corresponding
simulation envelopes:

| State | Simulation envelope | Experiment | Inside envelope |
|---|---:|---:|---:|
| bottom rough | 2.148--2.286 | 1.60 | no |
| top rough | 2.808--2.860 | 1.54 | no |
| side rough | 0.834--1.007 | 0.39 | no |
| bottom polished, others rough | 0.817--1.014 | 0.39 | no |
| top polished, others rough | 0.663--0.975 | 0.32 | no |

All five rough states exceed the 0.01 response-reporting threshold. Larger
roughness reduces bottom-rough enhancement and increases loss for the
side/multiple-rough states, but no state reaches its measured value within the
scanned range. The ideal 511 keV sample selects the same 32 events
with full-energy half-widths of 0.25, 0.5 and 1.0 keV.

Therefore the B4 discrepancy is not explained by finite Monte Carlo
uncertainty, the tested full-energy window, or choosing another single shared
roughness value in this range. This does not prove that the experiment is
wrong, and it does not justify separate face-by-face roughness fits.

## Model assumptions that can plausibly matter

These are hypotheses, not conclusions from B5:

- The PMT is currently a refractive receiver window behind a 0.1 mm bottom
  air-gap placeholder. Photocathode quantum efficiency and angular response
  are absent; optical grease/couplant is intentionally not present in this
  revised geometry.
- The top ESR is behind a 0.1 mm air-gap placeholder and uses
  wavelength-independent 0.98 reflectivity with a pure UNIFIED specular-lobe
  branch. Actual spacing, wrapping and ESR angular/spectral response are not
  measured inputs.
- All three air-gap dimensions, ESR thickness, PMT-window thickness and
  black-housing thickness are B0 placeholders. The black structure is an
  ideal absorber.
- A single `sigma_alpha` represents all surfaces made by the same roughening
  process. No profilometry or calibrated mapping from the real finish to
  UNIFIED microfacet width is yet available.
- The optical spectrum is a narrow 545/550/555 nm representation; material and
  interface properties are effectively wavelength independent over it.
- The source is a centered 511 keV pencil beam, not the full 22Na capsule,
  surrounding apparatus and experimental trigger/peak-estimation chain.

## Measurements needed before model refinement

The highest-value next inputs are measured top/bottom/side gap sizes, the
actual bottom coupling stack, the
actual ESR placement/product data, black-structure dimensions/reflectance,
surface profilometry for the shared roughening process, and the PMT spectral
and angular detection response. Once recorded, each should enter as a measured
parameter or documented literature parameter. Only remaining unidentified
quantities should be scanned as free parameters, and the same-process rough
faces must continue to share one roughness parameter.
