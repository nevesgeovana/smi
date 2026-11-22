# Method

The method decomposes the propeller-airframe interaction of an aircraft from isolated-component and combined
solver runs, builds the aircraft totals component by component and derives stability, trim and sizing
quantities from them. It is implemented in the package `smi_framework` and explained step by step in
`method_deck.pdf`.

Reference: Neves et al., Journal of Aircraft, 2026, doi 10.2514/1.C038629.

## The package

Install from the root of the repository (Python 3.11 or later):

    python -m pip install .

The kriging response surface also needs `smt`: `python -m pip install ".[response-surface]"`.

| Module | What it does |
|---|---|
| `array` | A labelled n-dimensional table (`PolarArray`) and the readers of solver polars (`read_table`, `from_files`). Columns that start with `LEGACY_` are read with that prefix removed. |
| `methods` | Generic steps repeated across the analysis: thrust loading, static margin, neutral point, moment reference shift, propeller equivalent angle, smoothing. Every number comes in as an argument. |
| `decomposition` | Breakdown of the aeropropulsive contributions: surface polars from wing-off runs, downwash and dynamic pressure ratio at the tail, slipstream angle and ratio at the pylon (nonlinear sequential method, with the equivalent and crossing methods for missing runs), and the in-plane gradient of the propeller. |
| `build_up` | Build-up of the aircraft totals at the moment reference point, the extrapolated database and its writer and reader. The transposition to any center of gravity comes afterward. |
| `response_surface` | Response surface of the build-up by kriging, and the trim and sizing lines solved on it. Requires `smt`. The band it gives is the surrogate's own error, not a physical or solver uncertainty. |
| `monte_carlo` | Monte Carlo propagation of uncertain scales through a cheap response, with a correlated sampler. Generic: numpy and scipy only, no plotting. |
| `plotting` | One frame for every plot page, in the format of the article's figures. |

## The method steps

1. Polars of each configuration, with the propeller on and off, are read. They stay at the moment reference
   point until the sizing.
2. Surface polars of the tail and the pylon are differences of wing-off runs.
3. Downwash and dynamic pressure ratio at the tail, and slipstream angle and ratio at the pylon, are found
   by the nonlinear sequential method (`decomposition`).
4. The installed propeller angle follows from the isolated in-plane gradient.
5. The aircraft totals are built up component by component (`build_up`).
6. Stability, trim and sizing quantities are derived; the moment is moved to each center of gravity only
   here. The scissor plot comes from a kriging surface of the build-up (`response_surface`).
7. The setup biases are propagated to the sizing, and a Monte Carlo of their scales gives an interval of
   the tail area factor (`monte_carlo`).

## The method deck

<!-- --8<-- [start:deck] -->
`method_deck.pdf` presents each step with its equations, a worked example on the SMI-L2 geometry, the
function of the package that implements it, and the premises and limits of the step. Another aircraft needs
a new aircraft input file and a new case input file in the format of the files in
`../publications/2027-ja-smi-l2/inputs/`.
<!-- --8<-- [end:deck] -->
