# SMI geometry log

## What SMI is

SMI, the Standard Model ITA, is an interchangeable-component research configuration for the study of
propeller-airframe integration. It has a common airframe (wing, body, vertical tail and horizontal tail)
and three pylon-nacelle installations, called levels:

| Level | Installation |
|---|---|
| L1 | wing-mounted |
| L2 | rear-mounted tractor |
| L3 | rear-mounted pusher |

The levels share the airframe, so a study changes the installation and nothing else. The geometry is given
as IGES surfaces. No propeller blade of any kind is included. The propeller of the studies is the TU Delft
XPROP propeller, which its owners provide on request: TU Delft, "TUD-XPROP propeller geometry", Zenodo,
https://doi.org/10.5281/zenodo.18598046. It is not redistributed here.

## Origin

Author: Geovana Neves, Instituto Tecnologico de Aeronautica (ITA). Released on Zenodo as "SMI Framework":
concept DOI 10.5281/zenodo.23025104 (all versions). The geometry was first released in version 1.0.0
(DOI 10.5281/zenodo.23025105); version 2.0.0 adds the method and the data of the publications.
Licenses: geometry CC BY-NC 4.0, code MIT (see `LICENSE` and `LICENSE-CODE`).

## Generations

### 1st-generation

<!-- --8<-- [start:files] -->
Files in `1st-generation/`, all in millimetres. Their IGES header names the system "SMI" with version "SMI 1.0",
which identifies the 1st generation of the geometry, not the release of this repository:

| File | Holds |
|---|---|
| `SMI-WBVH.igs` | The geometry common to every configuration: wing, body, vertical tail and horizontal tail. |
| `SMI-Fuselage.igs` | The fuselage (body) alone. |
| `SMI-liftingsurfaces-nocap.igs` | The lifting surfaces without tip caps. |
| `SMI-L1-PN.igs` | Pylon and nacelle of level L1. |
| `SMI-L2-PN.igs` | Pylon and nacelle of level L2, with the spinner. |
| `SMI-L3-PN.igs` | Pylon and nacelle of level L3. |
<!-- --8<-- [end:files] -->

### History

| Date | Entry |
|---|---|
| 2026-09-28 | 1st-generation: the six IGES files above exported from the SMI model. |
| 2026-11-22 | Repository reorganized; the geometry moved to `geometry/1st-generation/` without any change to the files. |

## Axes and units

The stored IGES files use the analysis frame directly: x axial (0 at the nose, 20 000 mm at the tail of the
fuselage, positive aft), y spanwise, z up. Units are millimetres. (An earlier version of this repository
described y as axial; that text was wrong for the files stored here.)

## Reference dimensions (SMI-L2)

Read from the aircraft input `publications/2027-ja-smi-l2/inputs/smi_l2.toml`, in SI units.

| Quantity | Value | Unit |
|---|---|---|
| Reference area, Sref | 50.0 | m2 |
| Mean aerodynamic chord, Cref | 2.526 | m |
| x of the moment reference | 9.152 | m |
| x of the propeller plane | 14.76344 | m |
| Propeller radius | 1.8288 | m |
| Number of propellers | 2 | |
| Arm x(propeller plane) minus x(wing 25% MAC) | 5.6033 | m |
| Vertical arm of the propeller thrust | 1.84 | m |
| Horizontal tail area | 11.5759 | m2 |
| x of the horizontal tail 25% MAC | 19.1159 | m |
| z of the horizontal tail 25% MAC | 5.422 | m |
| Pylon area | 10.9928184 | m2 |
| x of the exposed pylon 25% MAC | 15.7373 | m |
| z of the exposed pylon 25% MAC | 1.6639 | m |
| x of the wing 25% MAC | 8.529 | m |

## Adding a propeller

The studies use the TU Delft XPROP propeller, which is not part of this repository. Its geometry is available on request from its owners through the Zenodo record "TUD-XPROP Propeller Geometry" (T. Sinnige and B. Della Corte), https://doi.org/10.5281/zenodo.18598046.

For the L2 installation, the surfaces of `SMI-L2-PN.igs` start at x = 13 886.0 mm, the spinner tip. The
values below are the ones the earlier text of this repository gave, converted to the frame above (x axial,
y spanwise, z up):

- Rotation axis: parallel to x, through y = -3 504 mm, z = 1 840 mm.
- Spinner: tip at x = 13 886 mm, base at x = 14 983 mm, base radius 365.6 mm. The hub is centred on the
  spinner axis; the blade roots attach on the spinner surface.
- Place the propeller disc on that axis at the axial station your propeller requires, scale it to the
  diameter of your study, and set its hand of rotation in your solver's rotor definition.

For L1 and L3, take the axis from the spinner or nacelle of the corresponding file the same way.

Engine reference point of each installation, read from the spinner surfaces of its file (the tractor spinner
tip lies forward of its base, the pusher tip aft of it). This table is the reference for the values above:

| Installation | Type | Axis y (mm) | Axis z (mm) | Spinner tip x (mm) | Spinner base x (mm) | Spinner base radius (mm) | Propeller plane x (mm) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SMI-L1 | tractor | -3 504.0 | 600.0 | 5 214.0 | 6 310.8 | 365.6 | not defined by the IGES |
| SMI-L2 | tractor | -3 504.0 | 1 840.0 | 13 886.0 | 14 982.8 | 365.6 | not defined by the IGES |
| SMI-L3 | pusher | -2 600.0 | 2 720.0 | 19 204.9 | 18 080.0 | 365.6 | not defined by the IGES |

The axis of each installation is parallel to x. The propeller plane follows from the propeller that is added,
not from the IGES file.
