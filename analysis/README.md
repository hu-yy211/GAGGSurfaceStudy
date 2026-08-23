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
