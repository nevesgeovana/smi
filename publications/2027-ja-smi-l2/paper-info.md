# Paper: Propeller Effects on Stability and Control Sizing of Aircraft with Rear-Mounted Engines

Authors: Geovana Neves, Tiago Barbosa de Araujo, Tomas Sinnige, Roberto Gil Annes da Silva.
Affiliations: Instituto Tecnologico de Aeronautica (ITA), Brazil; Delft University of Technology, The Netherlands.

Journal: Journal of Aircraft. Status: under preparation. DOI: to come.
The paper extends AIAA Paper 2026-4720, doi:10.2514/6.2026-4720.

This folder holds what is needed to inspect and re-derive the numerical results of the paper: the inputs of the
method, the solver polars, and the data behind each plotted figure. Wind-tunnel data are not here; they are in
the Supplemental Data S1 of the paper.

## Geometry version

SMI, 1st-generation, level L2 (rear-mounted tractor), in `../../geometry/1st-generation/`. The runs of this
folder are all on SMI-L2. L1 is wing-mounted and L3 is the pusher. The propeller is the TU Delft XPROP
propeller (blades are not part of this repository).

## Software

| Item | Version |
|---|---|
| Solver | FlightStream 26.100, build 2122026 (February 12, 2026), unsteady panel method |
| Analysis | `smi_framework` 2.0.0 (`../../method/`) |

Solver setup of the decomposition runs (the validation runs of the isolated propeller use the setup of the
second column):

| Parameter | Decomposition | Validation |
|---|---|---|
| Blade mesh | B (42 x 42) | B (42 x 42) |
| Trailing edge | Collapsed | Blunt |
| Viscous coupling | Off | On |
| Rotation increment per step, deg | 10 (36 steps per revolution) | 5 |
| Revolutions, isolated propeller | 1.5 | 1.5 |
| Revolutions, tail off | 3.0 | not applicable |
| Revolutions, tail on | 4.0 | not applicable |
| Boundary layer | Turbulent | Turbulent |

Flight condition of the runs: Mach 0.2. Power-off polars: alpha 0, 2, 4, 8 deg (WB, WBVH, B, BVH, BPN, WBPN,
WBPNVH; the power-off value of every polar is the J and RPM stated in its file). Propeller-on polars:
J = 1.3, 858.798 rpm, blade angles 30, 35, 40 and 45 deg, alpha 0, 4, 8 deg (0 and 4 deg for NX). The
isolated propeller X holds the J sweeps at alpha 0 and 4 deg. The moment reference in the polars is x = 9.152 m.
Columns that start with `LEGACY_` are kept as they are in the polar files; `smi_framework.array.read_table`
removes the prefix when loading them. Run dates are in the file headers of the original exports, which are not
published.

## Component letters

W wing, B body (fuselage), P pylon, N nacelle, V vertical tail, H horizontal tail, X propeller.
`WBPNVHX` is the complete aircraft with propeller; `WBPNVH` is the same with the power off; `B` is the body alone.
Wing-off configurations are B, BVH, BPN, BPNX, NX and X.

## Folder contents

### inputs/

One aircraft file, one case file for the paper and two setup-bias cases, plus the measured biases they use.
The polar path of each case file is `../data`.

| File | What it feeds |
|---|---|
| `smi_l2.toml` | Aircraft: reference values, arms, surfaces of the tail and the pylon, propeller count. |
| `journal_2026.toml` | The case of the paper: which polar is which run, grids, series, correction switches, sizing. Feeds Figs. 12 to 29 and the figures of the sizing. |
| `journal_bias.toml` | The setup-bias cases: the `bias_*` keys scale a measured bias (0 none, 1 the full bias); also the Monte Carlo premises (Fig. 30). |
| `journal_bias_check.toml` | Direct checks of the Monte Carlo surrogate: the bias scales set to intermediate values in [0, 1]. |
| `setup_bias.toml` | The measured setup biases: the in-plane slope ratio and the ratios of the dynamic pressure and of the swirl angle, per blade angle. |

### data/

`data/<CONFIGURATION>/SUPER-<run>-M200AL+sweepBE+000_g01.csv`, one CSV per solver run, in a folder named by the
component letters of the configuration.

| Folder | Configuration | Runs |
|---|---|---|
| B | body | 3247 |
| BVH | body, vertical tail, horizontal tail | 3248, 3249, 3250 |
| BPN | body, pylon, nacelle | 3254, 3281, 3282 |
| BPNX | body, pylon, nacelle, propeller | 3270 to 3273, 3287, 3288, 3297 to 3302 |
| NX | nacelle, propeller | 3317 to 3320 |
| X | propeller alone | 0000_AoA0, 0000_AoA4, 3303 to 3316 |
| WB | wing, body | 3222 |
| WBVH | wing, body, vertical tail, horizontal tail | 3251, 3252, 3253 |
| WBPN | wing, body, pylon, nacelle | 3255, 3285, 3286 |
| WBPNVH | the same with the tails, power off | 3229, 3244, 3245, 3246 |
| WBPNX | wing, body, pylon, nacelle, propeller | 3266 to 3269, 3289 to 3296 |
| WBPNVHX | complete aircraft with propeller | 3241 to 3243, 3257 to 3265 |

The case file names the run of every role (for example `[reduction.tail]` names the wing-off runs 3247 and
3248 that give the tail polar).

### results/

One CSV per figure with plotted data, in long format with the columns `series`, `x`, `y`, `x_label` and
`y_label`. Fig. 3 keeps the columns of its source. Figures that are diagrams or renders have no CSV: Figs. 1, 2,
4, 5, 13 and 18. For the validation figures (6, 7, 8, 9, 10) only the simulated series are given.
Lines of a panel that the paper draws from an earlier state of the same data are not duplicated here.

| Figure | File | Content |
|---|---|---|
| 3 | `Fig03.csv` | Method extension against the mesh-integrated wing and body lift, per thrust loading |
| 6(a) | `Fig06_a.csv` | Propeller efficiency against number of blade mesh faces |
| 6(b) | `Fig06_b.csv` | Thrust coefficient against rotation increment, with the extrapolated reference |
| 7(a) | `Fig07_a.csv` | Thrust coefficient against advance ratio, three solver fidelity settings |
| 7(b) | `Fig07_b.csv` | Dynamic pressure ratio at x = R, y = 0.7R against thrust coefficient |
| 8(a) | `Fig08_a.csv` | Thrust coefficient against advance ratio (simulation) |
| 8(b) | `Fig08_b.csv` | Propeller efficiency against advance ratio (simulation) |
| 9(a) | `Fig09_a.csv` | Induced axial velocity against radius at x/R = 1.0 (simulation) |
| 9(b) | `Fig09_b.csv` | Swirl angle against radius at x/R = 1.0 (simulation) |
| 10 | `Fig10.csv` | In-plane force slope against advance ratio (simulation) |
| 11 | `Fig11.csv` | Selected thrust conditions: isolines in the advance ratio and blade angle map |
| 12(a) | `Fig12_a.csv` | Pitching moment slope increment from the in-plane force, against thrust loading |
| 12(b) | `Fig12_b.csv` | Average dynamic pressure ratio at x = R against thrust loading |
| 12(c) | `Fig12_c.csv` | Average swirl angle at x = R against thrust loading |
| 14 | `Fig14.csv` | Slipstream angle at the pylon against angle of attack, BPNX |
| 15(a) | `Fig15_a.csv` | Slipstream angle at the pylon at alpha 0 against thrust loading |
| 15(b) | `Fig15_b.csv` | Slipstream angle derivative against thrust loading |
| 16 | `Fig16.csv` | Dynamic pressure ratio at the pylon at alpha 0 against thrust loading |
| 17 | `Fig17.csv` | Dynamic pressure ratio at the pylon against angle of attack |
| 19(a) | `Fig19_a.csv` | In-plane force coefficient per propeller against angle of attack |
| 19(b) | `Fig19_b.csv` | Installed propeller inflow angle against angle of attack |
| 20 | `Fig20.csv` | Propeller angle of attack derivative against thrust condition |
| 21 | `Fig21.csv` | Propeller angle of attack at alpha 0 against thrust condition |
| 22 | `Fig22.csv` | Downwash at the horizontal tail against angle of attack |
| 23(a) | `Fig23_a.csv` | Downwash increment at alpha 0 against thrust loading |
| 23(b) | `Fig23_b.csv` | Downwash increment derivative against thrust loading |
| 24(a) | `Fig24_a.csv` | Static margin increment by contribution |
| 24(b) | `Fig24_b.csv` | Pitch damping increment by contribution, percent of total |
| 24(c) | `Fig24_c.csv` | Pitching moment coefficient increment at alpha 0 by contribution |
| 25(a) | `Fig25_a.csv` | Static margin, overall propeller effect and pylon influence |
| 25(b) | `Fig25_b.csv` | Pitch damping, overall propeller effect and pylon influence |
| 26 | `Fig26.csv` | Pitching moment at alpha 0, overall propeller effect and pylon influence |
| 27 | `Fig27.csv` | Installed tail contribution to the pitching moment, simulation and build-up, beta 45 |
| 28 | `Fig28.csv` | Scissor plot: horizontal tail area factor against feasible CG range |
| 29 | `Fig29.csv` | Horizontal tail area factor against feasible CG range, by case |
| 30(a) | `Fig30_a.csv` | Triangular density of a setup-bias scale |
| 30(b) | `Fig30_b.csv` | Samples of the dynamic pressure and swirl scales (rank correlation 0.5) |

## How to re-derive the results

1. Install the package from the root of the repository: `python -m pip install .` (the kriging of the scissor
   plot needs `python -m pip install ".[response-surface]"`).
2. Read a polar with `smi_framework.read_table(path)`, or the runs named in an input file with
   `smi_framework.from_files`. The runs of each role are named in `inputs/journal_2026.toml`.
3. Follow the steps of the method in `../../method/README.md` and `../../method/method_deck.pdf`: reduction of
   the tail and pylon surface polars, propeller maps, build-up of the totals, stability and sizing, response
   surface, Monte Carlo of the setup biases. Aircraft values come from `inputs/smi_l2.toml`; the case choices
   from the case files; the measured setup biases from `inputs/setup_bias.toml`.
4. Compare the plotted values with the CSVs in `results/`.

The scripts that ran the chain for the paper and drew its figures are not included: the polars are the solver outputs the method starts from, and the steps above are applied with the package and the user's own script.

The wind-tunnel data used for the validation figures are in the Supplemental Data S1 of the paper.
