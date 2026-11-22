"""Build-up of the aircraft totals.
The aerodynamic data comes at the moment reference point (MRP); this module works at the MRP, and the transposition to any CG comes afterward.

Reference: Neves et al., "Interchangeable Aircraft Framework for Propeller Integration and Aeropropulsive Studies",
Journal of Aircraft, 2026, doi 10.2514/1.C038629, cited as Neves et al. 2026.
"""
import csv

import numpy as np

from .array import PolarArray, _line
from .decomposition import stability_arms


def local_angle(alpha, eps, q, vinf, geom, incidence):
    """The surface's local angle and the rate term, in degrees. Neves et al. 2026, Eqs. (22) and (27); atan2 where Eq. (22) writes the small-angle q x / V."""
    x_arm = geom['XrefHT'] - geom['XrefWing']
    dyn = np.arctan2(q * x_arm, vinf) * 180 / np.pi  # Eq. (22)
    return alpha + incidence - eps + dyn, dyn  # Eq. (27)


def surface_loads(alpha, polar, eps, kq, q, vinf, geom, incidence, scale):
    """One surface at one incidence and pitch rate, in the stability axis. Neves et al. 2026, Eqs. (27) to (33).

    A local angle past the polar's grid reads the straight line through the grid's last interval.
    """
    a_local, dyn = local_angle(alpha, eps, q, vinf, geom, incidence)
    d_alpha = np.deg2rad(eps - dyn)  # Eq. (28)
    grid = polar.get('ALPHA', alpha)  # the polar's own grid, if it carries one
    cl = kq * _line(grid, polar['CL'], a_local, 'linear', 'extrapolate') * scale  # Eq. (30)
    cd_raw = _line(grid, polar['CD'], a_local, 'linear', 'extrapolate')
    cdmin = np.nanmin(polar['CD'])
    # Eq. (32) in its expanded form, as decomposition._moment_error applies it: the minimum drag scales with k_q; the
    # rest is the induced drag, which goes with C_L squared, and C_L scales linearly with k_q, so it scales with k_q squared.
    cd = (kq * cdmin + kq ** 2 * (cd_raw - cdmin)) * scale
    cls = cl * np.cos(d_alpha) - cd * np.sin(d_alpha)  # Eq. (29)
    cds = cl * np.sin(d_alpha) + cd * np.cos(d_alpha)  # Eq. (31)
    xs, zs = stability_arms(alpha, geom)
    return cls, cds, -cls * xs + cds * zs  # Eq. (33)


def build(alpha, ids, ih_range, n_range, vinf, gravity, wb, surfaces, tail_key, measured, gradient, arm_x, arm_z, cref, n_propellers,
          power_off_ids, k_tail=1.0, angle_factor=np.pi * 180, rotation_sign=1.0, rate_speed=None):
    """Totals on (ALPHA, IH, LFACTOR, ID), Neves et al. 2026, Eqs. (21) to (26).

    surfaces[name] = {'geom', 'polar': {'CL','CD'}, 'eps': {id: {'EPS','KQDYN'}}}; the tail is surfaces[tail_key], at incidence IH and scale
    k_tail; any other surface sits at zero incidence. measured[id]: ALPHA_PROP, CDP_X, CMP_X; gradient[id]: per degree, Eq. (17).

    Departures of the source kept as defaults, each a toggle:
    - angle_factor: the source writes ALPHA*pi*180, toggle `alpha_units` passes pi/180.
    - rotation_sign: the source's thrust and in-plane rotation is opposite to its own axis rotation, toggle `thrust_rotation_sign` passes -1.
    """
    # The maneuver flies at its own speed, the polars stay at the speed of their runs: only the rate term reads rate_speed.
    speed = vinf if rate_speed is None else rate_speed
    names = ['CLS', 'CDS', 'CMS25', 'CLS_TOTAL', 'CDS_TOTAL', 'CMS25_TOTAL', 'dCDB', 'dCM', 'dCLB', 'TAIL_LOCAL']
    shape = (alpha.size, ih_range.size, n_range.size, len(ids))
    out = {k: np.full(shape, np.nan) for k in names}
    rad = alpha * angle_factor
    for b, blade in enumerate(ids):
        for j, n in enumerate(n_range):
            q = np.round((n - 1) * gravity / speed, 5)  # Eq. (21)
            alpha_dyn = np.arctan2(q * arm_x, speed) * 180 / np.pi  # Eq. (22), propeller arm
            for i in range(ih_range.size):
                cls, cds, cms = wb['CLS'].copy(), wb['CDS'].copy(), wb['CMS25'].copy()  # Eqs. (24) to (26), wing-body
                tail_local = np.full(alpha.shape, np.nan)
                for name, s in surfaces.items():
                    is_tail = name == tail_key
                    if blade in s.get('absent_for', []):
                        continue
                    e = s['eps'][blade]
                    l = surface_loads(alpha, s['polar'], e['EPS'], e['KQDYN'], q, speed, s['geom'], ih_range[i] if is_tail else 0.0, k_tail if is_tail else 1.0)
                    cls, cds, cms = cls + l[0], cds + l[1], cms + l[2]
                    if is_tail:
                        tail_local = local_angle(alpha, e['EPS'], q, speed, s['geom'], ih_range[i])[0]
                m, g = measured[blade], gradient[blade]
                alpha_prop = m['ALPHA_PROP'] + alpha_dyn
                dclb = g['CLP_X'] * alpha_prop  # Eq. (17)
                dcdb = m['CDP_X'] + g['CDP_X'] * alpha_dyn
                dcm = m['CMP_X'] + g['CMP_X'] * alpha_dyn - dclb * arm_x / cref + dcdb * arm_z / cref
                if blade in power_off_ids:
                    tot = cls, cds, cms
                else:  # Eqs. (24) to (26), installed propellers
                    tot = (cls + n_propellers * dclb * np.cos(rad) + rotation_sign * n_propellers * dcdb * np.sin(rad),
                           cds - rotation_sign * n_propellers * dclb * np.sin(rad) + n_propellers * dcdb * np.cos(rad),
                           cms + n_propellers * dcm)
                for k, v in zip(names, (cls, cds, cms, tot[0], tot[1], tot[2], dcdb, dcm, dclb, tail_local)):
                    out[k][:, i, j, b] = v
    idx = {'ALPHA': alpha, 'IH': ih_range, 'LFACTOR': n_range, 'BLADE': np.array(ids, dtype=float)}
    return PolarArray(idx, out).sort(0).sort(1).sort(2).sort(3)


FLAG_WORDS = ('alpha', 'ih', 'tail_local')


def database_flags(alpha, ih, tail_local, limits):
    """One word per point: `data`, or what lies past the data, among alpha, ih and tail_local, joined by +. limits holds the three ranges of the data."""
    past = [(v < limits[w][0] - 1e-9) | (v > limits[w][1] + 1e-9) for w, v in zip(FLAG_WORDS, (alpha, ih, tail_local))]
    code = past[0] * 1 + past[1] * 2 + past[2] * 4
    words = ['+'.join(w for b, w in enumerate(FLAG_WORDS) if i >> b & 1) or 'data' for i in range(8)]
    return np.array(words, dtype=object)[code]


def distance_past(value, low, high):
    """How far a value lies outside a range, zero inside it."""
    return np.maximum(np.maximum(low - value, value - high), 0.0)


def extrapolated_database(table_of_k, ks, limits, outputs):
    """The build-up as a database over area factor, alpha, IH, load factor and thrust, for one case, with a flag per row.

    table_of_k(k) returns the build-up on axes ALPHA, IH, LFACTOR, TCA, evaluated on the wide grid. Past the data each polar is the straight line through its last interval:
    the configuration polars through their last two points, 4 and 8 deg above and 0 and 2 deg below for a sweep at 0, 2, 4, 8; a surface polar, downwash and dynamic pressure ratio
    through the last interval of their source grid. A tail with no stall and a wing with no stall are premises of this construction.
    """
    out = {}
    for k in ks:
        t = table_of_k(float(k))
        a, i, n, c = np.meshgrid(t.index['ALPHA'], t.index['IH'], t.index['LFACTOR'], t.index['TCA'], indexing='ij')
        tail = t['TAIL_LOCAL'].ravel()
        part = {'K': np.full(a.size, float(k)), 'ALPHA': a.ravel(), 'IH': i.ravel(), 'LFACTOR': n.ravel(), 'TCA': c.ravel()}
        part.update({o: t[o].ravel() for o in outputs})
        part['TAIL_LOCAL'] = tail
        part['FLAG'] = database_flags(part['ALPHA'], part['IH'], tail, limits)
        for name, v in part.items():
            out.setdefault(name, []).append(v)
    return {name: np.concatenate(v) for name, v in out.items()}


def write_database(path, db):
    """The database as CSV, one row per point."""
    names = list(db)
    columns = [db[n] if n == 'FLAG' else np.char.mod('%.7g', db[n]) for n in names]
    with open(path, 'w', newline='', encoding='utf-8') as handle:
        w = csv.writer(handle)
        w.writerow(names)
        w.writerows(zip(*columns))


def read_database(path):
    """The database back from write_database."""
    with open(path, newline='', encoding='utf-8') as handle:
        rows = csv.reader(handle)
        names = next(rows)
        cols = list(zip(*rows))
    return {n: np.array(c, dtype=object) if n == 'FLAG' else np.array(c, dtype=float) for n, c in zip(names, cols)}
