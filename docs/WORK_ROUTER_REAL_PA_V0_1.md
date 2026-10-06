# Work Router v0.1 — Real PA Qualification

This campaign applies the certified work-router mechanics to measured physical
I/Q data in the OpenDPD CSV format.  For each nonzero input sample it derives
the measured complex transfer `r = y/x` and exposes only:

- `log(|r|)` for gain-threshold work;
- `arg(r)` for phase-excursion work;
- successive coordinate differences for operator-motion work.

The qualification cross-checks routed threshold answers against direct complex
arithmetic on the same input/output measurements.  Gain and phase queries must
not traverse the waveform-materialization edge.  Explicit output-I/Q work may.

The public source used for the first physical campaign is OpenDPD's
`datasets/DPA_200MHz/test_input.csv` and `test_output.csv`.  Source data are
not vendored into MAPEOGEO.

This is an engineering qualification of routing behavior, not evidence that
AM/AM or AM/PM analysis is novel; those are standard RF representations.
