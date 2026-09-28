# SMI v1.0.0: airframe geometry and surface meshes

Copyright (c) 2026 Geovana Neves. Licensed under the Creative Commons
Attribution-NonCommercial 4.0 International license (CC BY-NC 4.0); see `LICENSE`.

SMI is an interchangeable-component research configuration: a fuselage (B), a
wing (W), a horizontal tail (H), a nacelle with its spinner (N, S) and a pylon
(P), assembled in the combinations below to study propeller-airframe
integration. This record holds the AIRFRAME ONLY. No propeller blade of any
kind is included; section "Adding a propeller" says how to install one.

## Contents

> The geometry files are being prepared and will be added in a later commit;
> this table describes the v1.0.0 release.

| Folder | What it holds |
|---|---|
| `cad/SMI-L1/` | CATIA V5 parts of the level-1 geometry: lofting skeletons A and B, versions v0 to v6 (including the horizontal-tail incidence variants), the over-wing nacelle and the far-field part |
| `cad/SMI-L2/` | CATIA V5 product and parts of the level-2 geometry (wing at 3 deg, tractor rear-mounted nacelle-pylon, WBPNVH) |
| `ansa/components/` | ANSA meshes of the components: fuselage, the SMI nacelle with and without spinner, the minimal nacelle, and the pylon controls (0 and plus/minus 5 deg) |
| `ansa/assemblies/` | ANSA meshes of assembled airframes without propeller (WB, WBPNH) |
| `obj-power-off/` | Surface meshes (OBJ, triangles, metres) of 21 power-off configurations, one group per component: B, W, H, N, P, S |
| `MANIFEST.json` | Every file with its size and sha256 |

Configuration names read as the components they contain: `B` fuselage, `W`
wing, `H` horizontal tail, `P` pylon, `N` nacelle (with spinner `S` where
present); `PYL0`, `PYLp5`, `PYLn5` the pylon at 0, +5 and -5 deg; `IH0`,
`IHp2`, `IHn2` the tail incidence at 0, +2 and -2 deg.

## Coordinate system

Metres. x positive aft, y positive to starboard, z positive up (the frame the
meshes were saved in). The fuselage is 20.0 m long.

## Adding a propeller

The propeller is NOT part of this record. Any propeller can be installed on the
SMI nacelle as follows (values measured on the OBJ meshes, identical in every
configuration that carries the nacelle):

- Rotation axis: parallel to x, through y = -3.504 m, z = 1.840 m.
- Spinner (group `S`): tip at x = 13.886 m, base at x = 14.983 m; base radius
  0.3656 m. The hub of the propeller is centred on the spinner axis; the blade
  roots attach on the spinner surface.
- Place the propeller disc on that axis at the axial station your propeller
  requires, scale it to the diameter of your study, and set its hand of
  rotation in your solver's rotor definition.
- Mesh the blades with a surface resolution compatible with the spinner and
  nacelle meshes (see the OBJ triangle sizes).

The configurations studied by the author used the TU Delft XPROP propeller,
which is available from its owners on request: TU Delft, "TUD-XPROP propeller
geometry", Zenodo, https://doi.org/10.5281/zenodo.18598046. It is not
redistributed here.

## License and use

CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/). You may share and
adapt this geometry for NON-COMMERCIAL purposes, provided you credit the author,
Geovana Neves, cite this record, link to the license and say whether you changed
the files. Commercial use requires the author's written permission.

## How to cite

Geovana Neves, "SMI v1.0.0: airframe geometry and surface meshes", Zenodo, 2026,
doi: (assigned by Zenodo on publication).

Related: Geovana Neves, *pyflightstream*, Zenodo,
https://doi.org/10.5281/zenodo.21482924 (the software used to run and post-process
the configurations).
