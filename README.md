# SMI v1.0.0: airframe geometry

Copyright (c) 2026 Geovana Neves. Licensed under the Creative Commons
Attribution-NonCommercial 4.0 International license (CC BY-NC 4.0); see `LICENSE`.

SMI is an interchangeable-component research configuration for the study of
propeller-airframe integration: a common airframe (wing, body, vertical and
horizontal tail) and three pylon-nacelle installations, L1, L2 and L3. This
release holds the AIRFRAME ONLY, as IGES surfaces. No propeller blade of any
kind is included; section "Adding a propeller" says how to install one.

## Contents

| File | What it holds |
|---|---|
| `iges/SMI-Fuselage.igs` | The fuselage alone. |
| `iges/SMI-L1-PN.igs` | The L1 nacelle with its spinner, and the nacelle without the trim, for isolated-nacelle runs. |
| `iges/SMI-L2-PN.igs` | The L2 pylon and nacelle. |
| `iges/SMI-L3-PN.igs` | The L3 pylon and nacelle. |
| `iges/SMI-liftingsurfaces-nocap.igs` | The wing, the horizontal tail and the vertical tail, without the tip-cap lofting. |
| `iges/SMI-WBVH.igs` | The geometry common to every SMI configuration. |
| `MANIFEST.json` | Every file with its size and sha256. |

Every component is whole: no spare part was deleted, so intermediate
geometries can be built from these surfaces.

## Units and axes

Millimetres. IGES y runs along the fuselage (0 at the nose, 20 000 at the
tail), IGES z is spanwise, IGES x is vertical. (A mesh built in the usual
aerodynamic frame, x aft, y spanwise, z up, maps as x = IGES y, y = IGES z,
z = IGES x.)

## Adding a propeller

The propeller is NOT part of this release. For the L2 installation, the values
below can be read from `SMI-L2-PN.igs` itself (its surfaces start at
IGES y = 13 886.0 mm, the spinner tip):

- Rotation axis: parallel to IGES y, through IGES x = 1 840 mm, z = -3 504 mm.
- Spinner: tip at IGES y = 13 886 mm, base at IGES y = 14 983 mm, base radius
  365.6 mm. The hub is centred on the spinner axis; the blade roots attach on
  the spinner surface.
- Place the propeller disc on that axis at the axial station your propeller
  requires, scale it to the diameter of your study, and set its hand of
  rotation in your solver's rotor definition.

For L1 and L3, take the axis from the spinner or nacelle of the corresponding
file the same way. The configurations studied by the author used the TU Delft
XPROP propeller, which is available from its owners on request: TU Delft,
"TUD-XPROP propeller geometry", Zenodo, https://doi.org/10.5281/zenodo.18598046.
It is not redistributed here.

## License and use

CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/). You may share and
adapt this geometry for NON-COMMERCIAL purposes, provided you credit the author,
Geovana Neves, cite this record, link to the license and say whether you changed
the files. Commercial use requires the author's written permission.

## How to cite

Geovana Neves, "SMI v1.0.0: airframe geometry", Zenodo, 2026,
doi: (assigned by Zenodo on publication).

Related: Geovana Neves, *pyflightstream*, Zenodo,
https://doi.org/10.5281/zenodo.21482924 (the software used to run and post-process
the configurations).
