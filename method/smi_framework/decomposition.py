"""Breakdown of the aeropropulsive contributions.
The aerodynamic data comes at the moment reference point (MRP); this module works at the MRP, and the transposition to any CG comes afterward.

Reference: Neves et al., "Interchangeable Aircraft Framework for Propeller Integration and Aeropropulsive Studies",
Journal of Aircraft, 2026, doi 10.2514/1.C038629, cited as Neves et al. 2026.
"""
import numpy as np
from scipy.optimize import minimize

from .array import _line


def stability_arms(alpha_deg, geom):
    """Tail arms in the stability axis, in chords. The tail arm term of Neves et al. 2026, Eq. (33); the paper leaves its form as f(...)."""
    x = (geom['XrefHT'] - geom['XrefWing']) / geom['CrefWing']
    z = (geom['ZrefHT'] - geom['ZrefWing']) / geom['CrefWing']
    a = np.deg2rad(alpha_deg)
    return x * np.cos(a) + z * np.sin(a), -x * np.sin(a) + z * np.cos(a)


def lift_from_moment(cm, cd, alpha_deg, geom):
    """Surface lift back-calculated from the moment, Neves et al. 2026, Eq. (6), with Eq. (5): no moment about its own quarter chord."""
    xs, zs = stability_arms(alpha_deg, geom)
    return -(cm - zs * cd) / xs


def reduce_surface(alpha, geom, wing_off, wing_on, tail_off, kq_limits, tol, maxiter, eps0_slope, eps0_offset, extrapolate=True, trace=None):
    """Sequential solution for downwash and dynamic pressure ratio, Neves et al. 2026, Eqs. (9) to (12).

    alpha: angle grid, deg. geom: surface block. wing_off[control] and wing_on[control]: surface polars CDS, CMS25 on `alpha`, as
    configuration differences, Eqs. (3) and (4). tail_off: CMS25 of the configuration without the surface. `tail_off` CMS is used as
    in Eq. (11). Returns EPS and KQDYN on `alpha`.

    kq_limits: None leaves the ratio as solved; a pair holds it between them (equal values fix it). extrapolate: the wing-off lift difference is read on its straight line past its range;
    False leaves those points without a value and fills them from the nearest one. trace: a list that receives, per iteration, the ratio per deflection as solved, its mean and the angle.
    """
    controls = sorted(wing_off)
    ref = 0
    off = {c: {'CL': lift_from_moment(wing_off[c]['CMS25'], wing_off[c]['CDS'], alpha, geom), 'CD': wing_off[c]['CDS']} for c in controls}
    on = {c: {'CL': lift_from_moment(wing_on[c]['CMS25'], wing_on[c]['CDS'], alpha, geom), 'CD': wing_on[c]['CDS'], 'CM': wing_on[c]['CMS'] } for c in controls}
    eps0 = alpha * eps0_slope + eps0_offset
    kq_prev = alpha * 0.0
    xs, zs = stability_arms(alpha, geom)
    eps = np.zeros_like(alpha)
    for _ in range(int(maxiter)):
        kq = _kq_mean(alpha, geom, eps0, off, on, controls, ref, kq_limits, extrapolate, trace)
        for a in range(alpha.size):
            eps[a] = minimize(_moment_error, eps0[a], args=(alpha[a] + geom['iHT'], kq[a], xs[a], zs[a], alpha, off, on, controls, tail_off[a], a),
                              method='Nelder-Mead', tol=tol).x[0]
        if np.mean(np.sqrt((kq - kq_prev) ** 2)) <= tol:
            break
        kq_prev = kq.copy()
        eps0 = eps.copy()
    return eps.copy(), kq.copy()


def _kq_mean(alpha, geom, eps, off, on, controls, ref, limits, extrapolate=True, trace=None):
    """Neves et al. 2026, Eq. (12): tail lift difference between two incidences, wing-on over wing-off, averaged over the deflections."""
    alpha_t = alpha + geom['iHT'] - eps  # Eq. (9)
    rad = np.deg2rad(eps)
    local = {c: on[c]['CL'] * np.cos(rad) + on[c]['CD'] * np.sin(rad) for c in controls}
    others = [c for c in controls if c != ref]
    kq = np.ones((len(others), alpha.size))
    amax = None
    for i, c in enumerate(others):
        if amax is None:  # the first deflection's limit stays for the others, as in the source
            amax = alpha[np.nanargmax(off[c]['CL'])]
        mask = alpha <= amax
        d = off[c]['CL'][mask] - off[ref]['CL'][mask]
        kq[i] = (local[c] - local[ref]) / _line(alpha[mask], d, alpha_t, 'linear', 'extrapolate' if extrapolate else np.nan)
    solved = kq.copy()
    if limits is not None:
        kq = np.clip(kq, limits[0], limits[1])
    mean = np.mean(kq, axis=0)
    good = np.where(np.isfinite(mean))[0]
    if trace is not None:
        trace.append({'controls': [c for c in others], 'solved': solved, 'mean': mean.copy(), 'eps': np.array(eps, float), 'amax': None if amax is None else float(amax)})
    if good.size:
        mean[:good[0]] = mean[good[0]]
        mean[good[-1] + 1:] = mean[good[-1]]
        mean = np.where(np.isfinite(mean), mean, np.interp(alpha, alpha[good], mean[good]))
    return mean


def _moment_error(e, alpha_a, kq, xs, zs, alpha, off, on, controls, tail_off_cm, a):
    """Sum over deflections of |C_M measured - C_M built|, Neves et al. 2026, Eq. (11), with the surface loads of Eqs. (9), (10) and (29) to (32)."""
    e = float(np.ravel(e)[0])
    at = np.array([alpha_a - e])
    r = np.deg2rad(e)
    err = 0.0
    for c in controls:
        cl = kq * _line(alpha, off[c]['CL'], at, 'linear', 'extrapolate')[0]
        cd_raw = _line(alpha, off[c]['CD'], at, 'linear', 'extrapolate')[0]
        cdmin = np.nanmin(off[c]['CD'])
        cd = kq * cdmin + kq ** 2 * (cd_raw - cdmin)  # the expanded form of Neves et al. 2026, Eq. (32): the minimum drag scales with k_q and the rest with k_q squared
        cls = cl * np.cos(r) - cd * np.sin(r)
        cds = cl * np.sin(r) + cd * np.cos(r)
        err += abs(on[c]['CM'][a] - (tail_off_cm + (-cls * xs + cds * zs)))
    return err


def inplane_gradient_inverse(cn_installed, a_lx):
    """Installed propeller angle from the installed force and the isolated gradient, Neves et al. 2026, Eq. (19)."""
    return cn_installed / a_lx


def inplane_moment_per_alpha(cn, arm, alpha_deg, n_propellers=1, chord=1.0):
    """In-plane moment slope -C_N*arm/alpha, per rad. Eq. (17) of Neves et al. 2026 gives the force.

    Old behaviour: n_propellers=1, chord=1 (one propeller, arm in metres). Correction toggle `inplane_moment_coefficient` passes the
    propeller count and the chord.
    """
    return -n_propellers * cn * arm / chord / alpha_deg * 180 / np.pi


def crossing_downwash(alpha, incidences, delta_cm):
    """Downwash from wing-on runs at several incidences, with no wing-off run. Not used by the article's figures.

    delta_cm[incidence] is the moment the surface adds (with minus without it) on `alpha`. At the angle where it vanishes the surface carries no load,
    so its local angle is zero and Neves et al. 2026, Eq. (9) gives epsilon = alpha + i. A symmetric surface is assumed. Returns epsilon on `alpha`,
    through the crossings, extrapolated linearly. The crossing itself has no equation in the paper.
    """
    a_cross, eps_cross = [], []
    for i in incidences:
        y = np.asarray(delta_cm[i], dtype=float)
        ok = np.isfinite(y)
        z = _line(y[ok], alpha[ok], np.array([0.0]), 'linear', 'extrapolate')[0]
        a_cross.append(z)
        eps_cross.append(z + i)
    return _line(np.array(a_cross), np.array(eps_cross), alpha, 'linear', 'extrapolate')


def equivalent_downwash(alpha, geom, polar, wing_on_cm, tail_off_cm, tol=1e-6):
    """Reduced equivalent downwash when a wing-off polar exists but no incidence sweep. Not used by the article's figures.

    With k_q fixed at 1 in Neves et al. 2026, Eq. (10), the angle that closes Eq. (11) carries the whole effect of the installation, the
    dynamic pressure change included. polar: {'CL', 'CD'} of the surface wing-off on `alpha`. Returns epsilon on `alpha`.
    """
    xs, zs = stability_arms(alpha, geom)
    off = {0.0: polar}
    on = {0.0: {'CM': wing_on_cm}}
    eps = np.zeros_like(alpha)
    guess = 0.0
    for a in range(alpha.size):
        eps[a] = minimize(_moment_error, guess, args=(alpha[a] + geom['iHT'], 1.0, xs[a], zs[a], alpha, off, on, [0.0], tail_off_cm[a], a),
                          method='Nelder-Mead', tol=tol).x[0]
        guess = eps[a]
    return eps


def downwash_method(block):
    """Which method a reduction block allows, from the runs it names: 'sequential', 'equivalent' or 'crossing'.

    - a wing-off polar at two or more deflections and wing-on runs at the same deflections: 'sequential', Neves et al. 2026, Eqs. (9) to (12);
    - a wing-off polar at one deflection: 'equivalent', the whole effect in the reduced downwash;
    - wing-on runs at several incidences and no wing-off polar: 'crossing'.
    """
    wing_off = block.get('wing_off') or {}
    if len(wing_off) >= 2:
        return 'sequential'
    if len(wing_off) == 1:
        return 'equivalent'
    wing_on = block.get('wing_on') or {}
    if any(len(v) >= 2 for v in wing_on.values()):
        return 'crossing'
    raise ValueError('a reduction block needs a wing-off polar or wing-on runs at two or more incidences')
