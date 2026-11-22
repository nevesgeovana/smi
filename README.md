# SMI Framework

<!-- --8<-- [start:intro] -->
SMI, the Standard Model ITA, is an interchangeable-component research configuration for the study of
propeller-airframe integration: a common airframe (wing, body, vertical and horizontal tail) and three
pylon-nacelle installations, L1, L2 and L3. This repository holds the geometry, the method that turns solver
polars into the decomposition, stability and sizing data of a study, and the data of the papers that used it.
No propeller blade of any kind is included.
<!-- --8<-- [end:intro] -->

Copyright (c) 2026 Geovana Neves. The geometry, data and documents are licensed under the Creative Commons
Attribution-NonCommercial 4.0 International license (CC BY-NC 4.0); see `LICENSE`. The code, every Python
file of the repository, is licensed under the MIT License; see `LICENSE-CODE`.

Documentation site: https://nevesgeovana.github.io/smi/

## Contents

| Folder | What it holds |
|---|---|
| `geometry/` | The SMI geometry as IGES surfaces, by generation, with `GEOMETRY_LOG.md`: what each file holds, axes, reference dimensions and history. |
| `method/` | The method: the Python package `smi_framework` and `method_deck.pdf`, which explains each step. |
| `publications/` | One folder per paper: `paper-info.md`, the `inputs` of the method, the solver polars in `data`, and one CSV per plotted figure in `results`. |

## Install

<!-- --8<-- [start:install] -->
Needs Python 3.11 or later. From the root of this repository:

    python -m venv .venv
    python -m pip install .

Check with `python -c "import smi_framework"`. The kriging response surface also needs `smt`:
`python -m pip install ".[response-surface]"`.
<!-- --8<-- [end:install] -->

## Geometry

IGES files in millimetres, x axial (positive aft), y spanwise, z up. See `geometry/GEOMETRY_LOG.md`.
The studies used the TU Delft XPROP propeller, which is available from its owners on request:
TU Delft, "TUD-XPROP propeller geometry", Zenodo, https://doi.org/10.5281/zenodo.18598046.
It is not redistributed here.

## Publications

`publications/2027-ja-smi-l2/`: Journal of Aircraft paper on the SMI-L2 configuration (under preparation).
Its `paper-info.md` states the geometry version, the software, the folder contents and how to reproduce.

## License and use

Geometry, data and documents: CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/). You may share
and adapt them for NON-COMMERCIAL purposes, provided you credit the author, Geovana Neves, cite this record,
link to the license and say whether you changed the files. Commercial use requires the author's written
permission. Code (`method/smi_framework/`): MIT License, see `LICENSE-CODE`.

## How to cite

<!-- --8<-- [start:cite] -->
Geovana Neves, "SMI Framework", Zenodo, 2026, https://doi.org/10.5281/zenodo.23025104 (all versions).
See `CITATION.cff`.

Related: Geovana Neves, *pyflightstream*, Zenodo, https://doi.org/10.5281/zenodo.21482924 (the software used
to run and post-process the configurations).
<!-- --8<-- [end:cite] -->
