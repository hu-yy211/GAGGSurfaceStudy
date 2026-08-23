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
