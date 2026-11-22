"""Generic steps repeated across the analysis. Every number comes in as an argument.

Reference: Neves et al., "Interchangeable Aircraft Framework for Propeller Integration and Aeropropulsive Studies",
Journal of Aircraft, 2026, doi 10.2514/1.C038629, cited as Neves et al. 2026. These steps have no equation in that paper unless a comment names one.
"""
import numpy as np


def thrust_loading(ct, j):
    """T_C = T/(q D^2) = 2 C_T / J^2. No equation in Neves et al. 2026."""
    return 2 * ct / j ** 2


def thrust_loading_area(ct, j, diameter, sref):
    """Thrust over q S per propeller, doubled as the source does: 2 C_T D^2 / (J^2 S). No equation in Neves et al. 2026."""
    return 2 * ct * diameter ** 2 / j ** 2 / sref


def tc_from_total_tca(tca, sref, diameter):
    """T_C per propeller from the area coefficient held by the build-up: 0.5 TCA S / D^2. No equation in Neves et al. 2026."""
    return 0.5 * tca * sref / diameter ** 2


def static_margin(cm_alpha, cl_alpha):
    """SM = -C_M,alpha / C_L,alpha, in fractions of the reference chord. No equation in Neves et al. 2026."""
    return -cm_alpha / cl_alpha


def flight_reference(mass, sref, cref, rho, cl_max, gravity):
    """Wing loading, stall speed from V^2 = 2 (W/S) / (rho CLmax), and relative density mu = 2 m / (rho S c), from a mass."""
    loading = mass * gravity / sref
    return {'mass': mass, 'wing_loading': loading, 'stall_speed': float(np.sqrt(2 * loading / (rho * cl_max))), 'mu': 2 * mass / (rho * sref * cref)}


def neutral_point(cm_alpha, cl_alpha, x_ref):
    """Neutral point in fractions of chord from the moment reference x_ref. No equation in Neves et al. 2026."""
    return x_ref - cm_alpha / cl_alpha


def increment_from_case(array, case_axis_name, reference_value):
    """The increment that case makes: -(case - reference), as the decomposition plots it. No equation in Neves et al. 2026."""
    return -array.subtract(array.slice(**{case_axis_name: reference_value}))


def grid(spec):
    """A rounded regular grid from {start, stop, step, round}; stop is exclusive, as in numpy.arange."""
    return np.round(np.arange(spec['start'], spec['stop'], spec['step']), spec['round'])


def shift_moment_reference(cd, cy, cl, cr_a, cm_a, cn_a, r_ab_body, alpha_deg, beta_deg, chord, span):
    """Moments about point B from those about point A, in the stability axis. Not used by the article's figures.

    r_ab_body is the vector from A to B in the body axis (x forward, y right, z down), in length units. The forces do not change.
    M_B = M_A - r_AB x F with F = (-CD, CY, -CL); rolling and yawing moments over span, pitching moment over chord.
    No equation in Neves et al. 2026; the axes are those of its Table 4.
    """
    a, b = np.deg2rad(alpha_deg), np.deg2rad(beta_deg)
    rx, ry, rz = r_ab_body
    # Body axis to stability axis, a rotation by alpha; beta carries the stability components to the wind axis used by the coefficients.
    sx = rx * np.cos(a) + rz * np.sin(a)
    sz = -rx * np.sin(a) + rz * np.cos(a)
    wx = sx * np.cos(-b) - ry * np.sin(-b)
    wy = sx * np.sin(-b) + ry * np.cos(-b)
    fx, fy, fz = -cd, cy, -cl
    return (cr_a - (wy * fz - sz * fy) / span,
            cm_a - (sz * fx - wx * fz) / chord,
            cn_a - (wx * fy - wy * fx) / span)


def propeller_equivalent_angle(alpha_deg, beta_deg):
    """Angle between the thrust axis and the wind, and the roll of the in-plane force about the thrust axis. Not used by the article's figures.

    The wind direction in propeller axes is (cos a cos b, cos a sin b, sin a); the equivalent angle is its angle from the thrust axis.
    """
    a, b = np.deg2rad(alpha_deg), np.deg2rad(beta_deg)
    wx, wy, wz = np.cos(a) * np.cos(b), np.cos(a) * np.sin(b), np.sin(a)
    return np.rad2deg(np.arccos(np.clip(wx, -1.0, 1.0))), np.rad2deg(np.arctan2(wy, wz))


def expand_propeller(alpha_table, normal_table, alpha_deg, beta_deg):
    """In-plane force at combined alpha and beta from an isolated propeller polar known against alpha only. Not used by the article's figures.

    Reads the polar at the equivalent angle and resolves the force along the roll angle: returns (normal, side).
    The linear in-plane behaviour is Neves et al. 2026, Eq. (17); this expansion has no equation there.
    """
    eq, roll = propeller_equivalent_angle(alpha_deg, beta_deg)
    force = np.interp(eq, alpha_table, normal_table)
    return force * np.cos(np.deg2rad(roll)), force * np.sin(np.deg2rad(roll))


def smooth_curve(y, alpha, window, at=None):
    """A curve against alpha as its quadratic least-squares fit over the window, read at `at` (default `alpha`), with the tangent line of the fit outside the window.

    Value and slope are continuous at the ends of the window. A curve with fewer than four finite points in the window, or a constant one, is left as it is.
    """
    y, alpha = np.asarray(y, float), np.asarray(alpha, float)
    at = alpha if at is None else np.asarray(at, float)
    finite = np.isfinite(y)
    inside = finite & (alpha >= window[0] - 1e-9) & (alpha <= window[1] + 1e-9)
    if inside.sum() < 4 or np.ptp(y[finite]) < 1e-12:
        return np.full(at.shape, np.nan) if not finite.any() else np.interp(at, alpha[finite], y[finite])
    p = np.polyfit(alpha[inside], y[inside], 2)
    slope = np.polyder(p)
    out = np.polyval(p, at)
    out = np.where(at < window[0], np.polyval(p, window[0]) + np.polyval(slope, window[0]) * (at - window[0]), out)
    return np.where(at > window[1], np.polyval(p, window[1]) + np.polyval(slope, window[1]) * (at - window[1]), out)


def line_through_middle(y, alpha, middle, at=None):
    """A curve against alpha as the straight least-squares line through its points in the middle window, read at `at` (default `alpha`), the same line across the whole range. A constant curve is left as it is."""
    y, alpha = np.asarray(y, float), np.asarray(alpha, float)
    at = alpha if at is None else np.asarray(at, float)
    finite = np.isfinite(y)
    inside = finite & (alpha >= middle[0] - 1e-9) & (alpha <= middle[1] + 1e-9)
    if inside.sum() < 2 or np.ptp(y[finite]) < 1e-12:
        return np.full(at.shape, np.nan) if not finite.any() else np.interp(at, alpha[finite], y[finite])
    return np.polyval(np.polyfit(alpha[inside], y[inside], 1), at)
