"""Response surface of the build-up by kriging, and the trim and sizing lines solved on it. Requires smt.

The band this module gives is the surrogate's own error, from the kriging variance. It is not a physical uncertainty and it is not the solver's uncertainty.
Trim and sizing have no equation in Neves et al., Journal of Aircraft, 2026, doi 10.2514/1.C038629; the surface replaces the tables of the build-up, Eqs. (24) to (26) of that paper.
"""
import numpy as np


def sample_grid(shape, size, seed):
    """Seeded sample without repeats of a full-factorial grid: flat indices, a stratified draw through the points in order."""
    total = int(np.prod(shape))
    rng = np.random.default_rng(seed)
    if size >= total:
        return np.arange(total)
    edges = np.linspace(0, total, size + 1).astype(int)
    return np.array([rng.integers(a, max(a + 1, b)) for a, b in zip(edges[:-1], edges[1:])])


class Surface:
    """One kriging model per output, on inputs scaled to [0, 1]."""

    def __init__(self, x, y, names, corr='matern52', poly='quadratic', nugget=None, eval_noise=False, n_start=2):
        from smt.surrogate_models import KRG
        self.low, self.high = x.min(axis=0), x.max(axis=0)
        self.names = names
        self.models = {}
        self.band_scale = {n: (1.0, 1.0) for n in names}  # multiplies the kriging deviation, inside and outside the swept box; see calibrate_band
        self.swept = None  # (alpha low, alpha high, IH low, IH high)
        options = dict(corr=corr, poly=poly, print_global=False, n_start=n_start, eval_noise=eval_noise)
        if nugget is not None:
            options['nugget'] = nugget
        for j, name in enumerate(names):
            model = KRG(**options)
            model.set_training_values(self.scale(x), y[:, j])
            model.train()
            self.models[name] = model

    def scale(self, x):
        return (x - self.low) / (self.high - self.low)

    def predict(self, x, variance=True):
        """Means and variances per output at the points x."""
        u = self.scale(x)
        mean = {n: m.predict_values(u).ravel() for n, m in self.models.items()}
        if not variance:
            return mean, None
        inside = self.inside(x)
        return mean, {n: np.maximum(m.predict_variances(u).ravel(), 0.0) * np.where(inside, self.band_scale[n][0], self.band_scale[n][1]) ** 2 for n, m in self.models.items()}

    def inside(self, x):
        """Which points lie inside the swept alpha and IH; all of them when no box was given."""
        if self.swept is None:
            return np.ones(x.shape[0], bool)
        return (x[:, 0] >= self.swept[0]) & (x[:, 0] <= self.swept[1]) & (x[:, 1] >= self.swept[2]) & (x[:, 1] <= self.swept[3])

    def calibrate_band(self, x, y, coverage=0.954, swept=None):
        """Scale each kriging deviation so that the two-sigma band holds the given fraction of held points (x, y; y by output in the order of names).

        With a swept box (alpha low, alpha high, IH low, IH high) inside and outside get their own scale: the polars kink inside their data and are straight lines outside it. Returns the scales.
        """
        self.swept = swept
        mean, var = self.predict(x)
        inside = self.inside(x)
        for j, n in enumerate(self.names):
            sig = np.sqrt(var[n])
            ratio = np.abs(mean[n] - y[:, j]) / (2 * np.where(sig > 0, sig, np.inf))
            scales = [float(np.quantile(ratio[m], coverage)) * old if m.any() else old for m, old in zip((inside, ~inside), self.band_scale[n])]
            self.band_scale[n] = tuple(scales)
        return dict(self.band_scale)


def trim_table(surface, n, tca, k, alpha, ih):
    """Means and standard deviations of the outputs on an (alpha, IH) table at one load factor, thrust and area factor."""
    aa, ii = np.meshgrid(alpha, ih, indexing='ij')
    x = np.column_stack([aa.ravel(), ii.ravel(), np.full(aa.size, n), np.full(aa.size, tca), np.full(aa.size, k)])
    mean, var = surface.predict(x)
    return {'alpha': alpha, 'ih': ih, 'mean': {o: v.reshape(aa.shape) for o, v in mean.items()}, 'std': {o: np.sqrt(v).reshape(aa.shape) for o, v in var.items()}}


def perturbed(table, z):
    """The table with each output moved by z times its standard deviation; z maps output to one number per draw."""
    out = dict(table)
    out['mean'] = {o: table['mean'][o] + z[o] * table['std'][o] for o in table['mean']}
    return out


def trim(table, cl_required, cg, cg_ref, names):
    """Angle and incidence where the lift is the required one and the moment about the CG vanishes, on the table; NaN if the table does not hold it."""
    cl_name, cd_name, cm_name = names
    alpha, ih = table['alpha'], table['ih']
    a_at = np.full(ih.size, np.nan)
    cm_at = np.full(ih.size, np.nan)
    xb = cg - cg_ref
    for i in range(ih.size):
        cl = table['mean'][cl_name][:, i]
        if cl.min() <= cl_required <= cl.max():
            o = np.argsort(cl)
            a = np.interp(cl_required, cl[o], alpha[o])
            r = np.deg2rad(a)
            a_at[i] = a
            cm_at[i] = np.interp(a, alpha, table['mean'][cm_name][:, i]) + cl_required * xb * np.cos(r) + np.interp(a, alpha, table['mean'][cd_name][:, i]) * xb * np.sin(r)
    ok = np.isfinite(cm_at)
    if ok.sum() < 2 or cm_at[ok].min() > 0 or cm_at[ok].max() < 0:
        return np.nan, np.nan
    o = np.argsort(cm_at[ok])
    at = np.interp(0.0, cm_at[ok][o], ih[ok][o])
    return at, np.interp(at, ih[ok], a_at[ok])


def limit_at_incidence(table, cl_required, target_ih, cgs, cg_ref, names):
    """The CG that trims at a given incidence, through the trims at the listed CGs. Returns CG, alpha, IH."""
    ii = np.array([trim(table, cl_required, c, cg_ref, names) for c in cgs])
    ok = np.isfinite(ii[:, 0])
    if ok.sum() < 2:
        return np.nan, np.nan, np.nan
    o = np.argsort(ii[ok, 0])
    cg = np.interp(target_ih, ii[ok, 0][o], cgs[ok][o], left=np.nan, right=np.nan)
    return (cg, *trim(table, cl_required, cg, cg_ref, names)[::-1]) if np.isfinite(cg) else (np.nan, np.nan, np.nan)


def limit_at_elevator(table_n, table_1, cl_n, cl_1, target, effectiveness, cgs, cg_ref, names):
    """The CG where the incidence change from level flight to the manoeuvre, over the effectiveness, equals the target. Returns CG, alpha, IH at the manoeuvre."""
    y = []
    for c in cgs:
        a, b = trim(table_n, cl_n, c, cg_ref, names)[0], trim(table_1, cl_1, c, cg_ref, names)[0]
        y.append((a - b) / effectiveness)
    y = np.array(y)
    ok = np.isfinite(y)
    if ok.sum() < 2:
        return np.nan, np.nan, np.nan
    o = np.argsort(y[ok])
    cg = np.interp(target, y[ok][o], cgs[ok][o], left=np.nan, right=np.nan)
    return (cg, *trim(table_n, cl_n, cg, cg_ref, names)[::-1]) if np.isfinite(cg) else (np.nan, np.nan, np.nan)


def neutral_point(surface, alpha, n, tca, k, ih, cg_ref, names, draws=0, rng=None):
    """Neutral point from least-squares slopes of the surface against alpha, at one condition, in fractions of chord, and the deviation of `draws` normal draws of the outputs, independent per point."""
    x = np.column_stack([alpha, np.full(alpha.size, ih), np.full(alpha.size, n), np.full(alpha.size, tca), np.full(alpha.size, k)])
    mean, var = surface.predict(x, variance=draws > 0)

    def value(cl, cm):
        return cg_ref - np.polyfit(alpha, cm, 1)[0] / np.polyfit(alpha, cl, 1)[0]

    centre = value(mean[names[0]], mean[names[2]])
    if not draws:
        return centre, 0.0
    samples = [value(mean[names[0]] + rng.standard_normal(alpha.size) * np.sqrt(var[names[0]]), mean[names[2]] + rng.standard_normal(alpha.size) * np.sqrt(var[names[2]])) for _ in range(draws)]
    return centre, float(np.std(samples))
