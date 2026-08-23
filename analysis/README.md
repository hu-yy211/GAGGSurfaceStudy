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
