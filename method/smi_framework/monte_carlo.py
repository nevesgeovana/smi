"""Monte Carlo propagation of uncertain scales through a cheap response, with a correlated sampler. Generic: numpy and scipy.special only, no plotting.

A set of uncertain terms is described by one scale s_i each. The response y(s) of an output (a value per position, such as an area factor per CG range) is a surrogate of
solved cases: a first-order sum of the single-term effects, optionally a second-order polynomial fitted to further solved points. The scales are sampled from a marginal
distribution per term, triangular or normal, joined by a Gaussian copula so that a rank correlation can be set. The module reports percentiles with their sampling error,
exceedance probabilities and first-order variance shares.

Conventions: s has shape (samples, terms); a response has shape (samples, positions); a quantity per position has shape (positions,).
"""
from itertools import combinations

import numpy as np
from scipy.special import ndtr, ndtri

KINDS = ('triangular', 'normal')


def triangular_moments(low, peak, high):
    """Mean and variance of a triangular distribution on [low, high] with its peak at `peak` (closed form)."""
    check_triangle(low, peak, high)
    mean = (low + peak + high) / 3.0
    var = (low ** 2 + peak ** 2 + high ** 2 - low * peak - low * high - peak * high) / 18.0
    return mean, var


def check_triangle(low, peak, high):
    if not (low < high and low <= peak <= high):
        raise ValueError('triangular needs low < high and low <= peak <= high, got %r %r %r' % (low, peak, high))


def marginal_ppf(u, kind, *params):
    """Inverse distribution function at the probabilities u. kind 'triangular' takes (low, peak, high); 'normal' takes (mean, sigma)."""
    u = np.asarray(u, float)
    if kind == 'triangular':
        low, peak, high = params
        check_triangle(low, peak, high)
        split = (peak - low) / (high - low)
        left = low + np.sqrt(np.clip(u, 0.0, 1.0) * (high - low) * (peak - low))
        right = high - np.sqrt(np.clip(1.0 - u, 0.0, 1.0) * (high - low) * (high - peak))
        return np.where(u < split, left, right)
    if kind == 'normal':
        mean, sigma = params
        if sigma <= 0:
            raise ValueError('sigma must be positive')
        return mean + sigma * ndtri(u)
    raise ValueError('unknown distribution %r, expected one of %s' % (kind, KINDS))


def copula_correlation(rank_correlation):
    """Gaussian-copula correlation that gives a Spearman rank correlation, for a scalar or a matrix: 2 sin(pi rho / 6), the diagonal staying 1."""
    r = 2.0 * np.sin(np.pi * np.asarray(rank_correlation, float) / 6.0)
    if r.ndim == 2:
        np.fill_diagonal(r, 1.0)
    return r


def correlation_matrix(n_terms, pairs=None):
    """Identity with the off-diagonal entries given as {(i, j): rho}."""
    r = np.eye(n_terms)
    for (i, j), rho in (pairs or {}).items():
        if not -1.0 <= rho <= 1.0:
            raise ValueError('correlation outside [-1, 1]')
        r[i, j] = r[j, i] = rho
    return r


def sample_scales(n, kinds, params, rank_correlation=None, seed=0):
    """n samples of the scales: shape (n, terms).

    kinds and params give the marginal of each term (see marginal_ppf); rank_correlation is a symmetric matrix of Spearman correlations, default identity, applied through a
    Gaussian copula. A matrix that is not positive semi-definite is refused. The generator is seeded, so a call is reproducible.
    """
    k = len(kinds)
    if len(params) != k:
        raise ValueError('one parameter tuple per term')
    rho = np.eye(k) if rank_correlation is None else np.asarray(rank_correlation, float)
    if rho.shape != (k, k) or not np.allclose(rho, rho.T) or not np.allclose(np.diag(rho), 1.0):
        raise ValueError('rank_correlation must be a symmetric %dx%d matrix with unit diagonal' % (k, k))
    g = copula_correlation(rho)
    w, v = np.linalg.eigh(g)
    if w.min() < -1e-10:
        raise ValueError('correlation matrix is not positive semi-definite')
    factor = v * np.sqrt(np.clip(w, 0.0, None))  # g = factor factor^T; also valid for a singular matrix such as rho = 1
    z = np.random.default_rng(seed).standard_normal((n, k)) @ factor.T
    u = ndtr(z)
    return np.column_stack([marginal_ppf(u[:, i], kinds[i], *params[i]) for i in range(k)])


def nonphysical_mask(s, deficits):
    """True for samples where any term's factor 1 - d_i s_i is not positive: the corrected quantity would change sign or diverge."""
    return np.any(1.0 - np.asarray(deficits, float) * np.asarray(s, float) <= 0.0, axis=1)


def features(s, order=1):
    """Polynomial features of the scales without a constant: s; order 2 adds the squares and the products of every pair."""
    s = np.atleast_2d(np.asarray(s, float))
    cols = [s]
    if order == 2:
        cols.append(s ** 2)
        cols.append(np.column_stack([s[:, i] * s[:, j] for i, j in combinations(range(s.shape[1]), 2)]))
    elif order != 1:
        raise ValueError('order must be 1 or 2')
    return np.hstack(cols)


class Response:
    """y(s) = baseline + features(s) @ coefficients, per position. baseline has shape (positions,), coefficients (features, positions)."""

    def __init__(self, baseline, coefficients, order=1):
        self.baseline = np.asarray(baseline, float)
        self.coefficients = np.asarray(coefficients, float)
        self.order = order

    def __call__(self, s):
        return self.baseline + features(s, self.order) @ self.coefficients


def first_order(baseline, singles, scale=1.0):
    """First-order response from the single-term cases solved at scale `scale`: singles has shape (terms, positions), coefficient a_i = (single_i - baseline) / scale."""
    base = np.asarray(baseline, float)
    return Response(base, (np.asarray(singles, float) - base) / scale, 1)


def fit_response(s_points, y_points, baseline, order=2):
    """Least-squares polynomial of the given order through solved points (points, terms) and (points, positions), forced through the baseline at s = 0.

    Needs at least as many points as features. Returns the response and the in-sample residuals (points, positions).
    """
    x = features(s_points, order)
    if x.shape[0] < x.shape[1]:
        raise ValueError('%d points for %d coefficients' % x.shape)
    base = np.asarray(baseline, float)
    coef = np.linalg.lstsq(x, np.asarray(y_points, float) - base, rcond=None)[0]
    resp = Response(base, coef, order)
    return resp, resp(s_points) - np.asarray(y_points, float)


def leave_one_out(s_points, y_points, baseline, order=2):
    """Prediction error (points, positions) of each point when it is left out of the fit."""
    s_points, y_points = np.asarray(s_points, float), np.asarray(y_points, float)
    out = np.empty_like(y_points)
    for i in range(s_points.shape[0]):
        keep = np.arange(s_points.shape[0]) != i
        resp, _ = fit_response(s_points[keep], y_points[keep], baseline, order)
        out[i] = resp(s_points[i:i + 1])[0] - y_points[i]
    return out


def percentiles(y, levels=(2.5, 16, 50, 84, 97.5)):
    """Percentiles per position: shape (levels, positions). NaN positions stay NaN."""
    return np.nanpercentile(y, levels, axis=0)


def percentile_standard_error(y, levels=(2.5, 97.5), half_width=0.01):
    """Sampling standard error of each percentile, (levels, positions): sqrt(p (1-p) / n) divided by the density at the percentile, which is taken from the spacing of the
    percentiles half_width either side (in probability)."""
    n = y.shape[0]
    out = []
    for lv in levels:
        p = lv / 100.0
        lo, hi = max(p - half_width, 0.0), min(p + half_width, 1.0)
        spread = np.nanpercentile(y, 100 * hi, axis=0) - np.nanpercentile(y, 100 * lo, axis=0)
        with np.errstate(divide='ignore', invalid='ignore'):
            out.append(np.sqrt(p * (1 - p) / n) * spread / (hi - lo))
    return np.array(out)


def probability_above(y, threshold):
    """Fraction of samples with y > threshold, per position (threshold a scalar or an array per position)."""
    return np.mean(y > threshold, axis=0)


def variance_shares(s, y, bins=50):
    """First-order variance share of each term, Var(E[y | s_i]) / Var(y), per position: shape (terms, positions).

    The conditional mean is taken over bins of equal sample count in s_i, so it holds for any response and any dependence between the terms. With correlated terms the shares
    include what a term carries through the others and need not sum to 1.
    """
    s, y = np.asarray(s, float), np.asarray(y, float)
    total = np.nanvar(y, axis=0)
    shares = np.empty((s.shape[1], y.shape[1]))
    for i in range(s.shape[1]):
        order = np.argsort(s[:, i], kind='stable')
        means = np.array([y[idx].mean(axis=0) for idx in np.array_split(order, bins)])
        counts = np.array([len(idx) for idx in np.array_split(order, bins)])
        centre = np.average(means, axis=0, weights=counts)
        with np.errstate(divide='ignore', invalid='ignore'):
            shares[i] = np.average((means - centre) ** 2, axis=0, weights=counts) / total
    return shares


def linear_variance_shares(coefficients, variances):
    """Analytic first-order shares of independent terms in a linear response: a_i^2 var_i / sum_j a_j^2 var_j. coefficients (terms, positions), variances (terms,)."""
    part = np.asarray(coefficients, float) ** 2 * np.asarray(variances, float)[:, None]
    return part / part.sum(axis=0)
