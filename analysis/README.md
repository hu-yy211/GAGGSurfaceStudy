# Analysis

Each validated stage keeps its independent CSV checker and, where useful, a
plotting script. A6 uses:

~~~sh
python analysis/validate_a6.py \
  --input results/a6/gamma_662kev.csv --expect-events 100
MPLCONFIGDIR=results/.mplconfig python analysis/plot_a6.py \
  --input results/a6/gamma_662kev.csv \
  --output-dir results/a6/figures
~~~

The validator requires exact optical terminal accounting, at least one zero,
partial and full-energy gamma event, zero light for every zero-deposit event,
and a generated-light yield within 1e-4 relative of 54000 photons/MeV. The
plotter writes a compact summary CSV, an energy-deposition histogram and a
generated-light linearity plot.

A7 uses `validate_a7.py` and `plot_a7.py`. The validator requires the four
surfaces to share identical event source positions, Edep, N_generated and
full-energy IDs before comparing event-level mean collection efficiencies. It
reports 95% confidence intervals and paired adjacent-order differences. The
current data deliberately return a nonzero validator exit because the Fig. 4
ordering is not reproduced; the plotter still writes reviewed diagnostic
figures and a summary CSV.

`summarize_a7_models.py` checks the four bounded combinations of direct or
explicit-air LUT connection and first-arrival or true boundary-transmission
scoring. Structural validation passes even when every model reports the
predefined Fig. 4 order as FAIL.

B0 uses `validate_b0.py`. It requires 50 center-source optical events with
100 photons each, exact terminal accounting, no Stage A LUT, nonzero PMT
transmission and nonzero ESR/black boundary activity.

B1 uses `validate_b1.py` and `plot_b1.py`. The validator requires all six
runtime surface states, one shared `sigma_alpha`, exact photon accounting,
nonzero independent top/bottom/side counters and an exact all-polished repeat.
It verifies that at least one rough state changes `N_PMT`, but deliberately
does not test the experimental ordering. The plotter writes `b1_summary.csv`,
a normalized collection-efficiency chart and a face-interaction diagnostic.

B2 centralizes the full grid in `config/b2_scan.json`. `run_b2_scan.py`
generates one Geant4 macro per point and runs each in a fresh process;
`validate_b2.py` requires the exact 90-file grid, event-level repeatability,
all-polished invariance, full accounting, face-counter activity and the locked
smoothness bounds. `plot_b2.py` writes the long-form summary, smoothness table,
absolute-efficiency scan and position-normalized scan. No script selects a
sigma value or tests the experimental order.

B3 centralizes its 511 keV pencil-beam inputs and full-energy gate in
`config/b3_gamma.json`. `run_b3.py` generates an inspectable macro,
`validate_b3.py` requires zero/partial/full energy classes, exact optical
accounting and the literature light yield, and `plot_b3.py` writes the energy
spectrum, scintillation-yield line and summary CSV. B3 uses all-polished
surfaces and does not compare the six experimental states.

B4 uses `config/b4_comparison.json`, `run_b4.py`, `validate_b4.py` and
`plot_b4.py`. The runner isolates all six surface states in separate Geant4
processes. The validator requires exact event-level source/Edep/generated
pairing, an exact all-polished B3 repeat, shared roughness and full accounting.
It reports 5000-resample paired-bootstrap intervals and simulation-minus-
measurement residuals. Experimental agreement is not a pass gate. The
plotter writes a long-form comparison table, grouped bar chart and residual
chart.

B5 uses `config/b5_robustness.json`, `run_b5.py`, `validate_b5.py` and
`plot_b5.py`. It reuses the six B4 samples at 0.20 rad and runs twelve new
isolated points at 0.10 and 0.30 rad, with four Geant4 subprocesses allowed in
parallel. The validator requires exact gamma-history pairing, all-polished
invariance, full accounting and an active shared-roughness response. The 0.01
threshold reports whether each state resolves a response; a physically weak
state is not treated as an invalid scan. The plotter writes the shared-sigma
table and six-panel sensitivity figure. No best-fit sigma is calculated.

B6 uses `config/b6_diagnostics.json`, `validate_b6.py` and `plot_b6.py`.
The event schema now resolves surface absorption at the top ESR, bottom PMT
interface, side-air interface, outer black structure and other surfaces. The
validator requires those locations to sum to aggregate surface absorption and
all terminal fractions to sum to generated light. It also requires exact
state-minus-all-polished differential closure. The plotter writes the
18-point loss table, a stacked terminal budget, a differential loss chart and
a logarithmic face-interaction chart. B6 introduces no fit parameter.

B7.3 uses `b7_3_common.py`, `run_b7_3.py`, `validate_b7_3.py` and
`plot_b7_3.py`. The locked 100k-event all-polished sample uses the B7.2
annihilation-pair source and selects events by event-total GAGG energy deposit
in 510.5--511.5 keV. The validator reports both `sum(N_PMT)/sum(N_generated)`
and mean `N_PMT` with standard errors; it never interprets the approximately
2.25 eV PMT optical photons as 511 keV particles.

B7.4 uses `b7_4_common.py`, `run_b7_4.py`, `validate_b7_4.py` and
`plot_b7_4.py`. It launches isolated processes for a locked shared-sigma grid,
reuses one sigma-inactive all-polished reference and requires exact event
history pairing. The predeclared score is RMSE over the five non-reference
normalized responses. Agreement is reported but is not a structural pass
gate; the code forbids per-face sigma values.

B7.5 uses `b7_5_common.py`, `run_b7_5.py` and `validate_b7_5.py` to compare
bottom rough, top rough and the added `top_bottom_rough` state at
sigma=0.70 rad with 100000 paired events. It reuses the B7.3 all-polished
reference and writes
`b7_5_endface_summary.csv` plus `b7_5_endface_comparison.csv`. There is no
B7.5 plotting program by design.
