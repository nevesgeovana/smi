"""A labelled n-dimensional table: named index axes and named variables sharing one shape.

The semantics below are stated, not assumed:
- interp: per line, along one axis, with NaN pairs dropped first; kind 'linear' or 'cubic'; fill_value is 'extrapolate' or a number.
  With a second axis named, the variable named in `targets` becomes the new index and the old index becomes a variable.
- polyFitCoeffs: least squares per line, coefficient 0 is the highest power (the convention of numpy.polyfit).
- slice keeps the axis with length 1; squeeze removes such axes and keeps their value as a variable.
"""
import copy as _copy
import csv

import numpy as np
from scipy.interpolate import interp1d


def _line(x, y, grid, kind, fill_value):
    """Interpolate one line after dropping non-finite pairs."""
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    need = 4 if kind == 'cubic' else 2
    if x.size < need:
        return np.full(grid.shape, np.nan)
    order = np.argsort(x, kind='stable')
    x, y = x[order], y[order]
    if kind == 'cubic':
        return interp1d(x, y, kind='cubic', bounds_error=False, fill_value=fill_value)(grid)
    i = np.clip(np.searchsorted(x, grid), 1, x.size - 1)
    with np.errstate(divide='ignore', invalid='ignore'):
        out = y[i - 1] + (y[i] - y[i - 1]) / (x[i] - x[i - 1]) * (grid - x[i - 1])
    if not isinstance(fill_value, str):
        out[(grid < x[0]) | (grid > x[-1])] = fill_value
    return out


def read_table(path, rename=None):
    """Read a superfile CSV into numeric columns: `NA` and text become NaN, columns with no number are dropped.

    `rename` maps a file column to the name used by the framework; a LEGACY_ prefix is removed.
    """
    with open(path, newline='', encoding='utf-8') as handle:
        rows = list(csv.reader(handle))
    out = {}
    for j, name in enumerate(rows[0]):
        vals = []
        for r in rows[1:]:
            try:
                vals.append(float(r[j]))
            except ValueError:
                vals.append(np.nan)
        vals = np.array(vals)
        if np.isfinite(vals).any():
            key = (rename or {}).get(name, name)
            out[key[7:] if key.startswith('LEGACY_') else key] = vals
    return out


class PolarArray:
    """Index axes in order, and variables that all have the shape of those axes."""

    def __init__(self, index, data):
        self.index = {k: np.asarray(v, dtype=float) for k, v in index.items()}
        self.data = data

    @property
    def dims(self):
        return list(self.index)

    @property
    def shape(self):
        return tuple(v.size for v in self.index.values())

    def __getitem__(self, name):
        if name in self.index:
            sh = [1] * len(self.dims)
            sh[self.dims.index(name)] = -1
            return np.broadcast_to(self.index[name].reshape(sh), self.shape)
        return self.data[name]

    def __setitem__(self, name, value):
        self.data[name] = np.broadcast_to(value, self.shape).copy()

    def __contains__(self, name):
        return name in self.index or name in self.data

    def __neg__(self):
        return PolarArray(self.index, {k: -v for k, v in self.data.items()})

    def copy(self):
        return _copy.deepcopy(self)

    def _take(self, axis, mask):
        name = self.dims[axis]
        idx = dict(self.index)
        idx[name] = self.index[name][mask]
        return PolarArray(idx, {k: np.compress(mask, v, axis=axis) for k, v in self.data.items()})

    def slice(self, **kw):
        """Keep the given index values; the axis stays, with length 1 for a scalar."""
        out = self
        for k, v in kw.items():
            ax = out.dims.index(k)
            want = np.atleast_1d(v)
            out = out._take(ax, np.isclose(out.index[k][:, None], want[None, :], atol=1e-7).any(axis=1))
        return out

    def sliceNotIn(self, **kw):
        out = self
        for k, v in kw.items():
            ax = out.dims.index(k)
            want = np.atleast_1d(v)
            out = out._take(ax, ~np.isclose(out.index[k][:, None], want[None, :], atol=1e-7).any(axis=1))
        return out

    def sliceLess(self, **kw):
        out = self
        for k, v in kw.items():
            out = out._take(out.dims.index(k), out.index[k] < v)
        return out

    def squeeze(self):
        """Remove axes of length 1; the index value stays as a variable."""
        keep = [k for k in self.dims if self.index[k].size != 1]
        gone = [k for k in self.dims if self.index[k].size == 1]
        axes = tuple(self.dims.index(k) for k in gone)
        data = {k: v.squeeze(axis=axes) for k, v in self.data.items()}
        out = PolarArray({k: self.index[k] for k in keep}, data)
        for k in gone:
            if k not in data:  # atMaximum keeps the selected index values as a variable
                out[k] = self.index[k][0]
        return out

    def expandDims(self, newIndexName, newIndexValue, axis=-1):
        pos = len(self.dims) if axis == -1 else axis
        items = list(self.index.items())
        items.insert(pos, (newIndexName, np.array([newIndexValue], dtype=float)))
        data = {k: np.expand_dims(v, pos) for k, v in self.data.items() if k != newIndexName}
        return PolarArray(dict(items), data)

    def concatenate(self, other, axis=-1):
        ax = axis if axis >= 0 else len(self.dims) + axis
        name = self.dims[ax]
        idx = dict(self.index)
        idx[name] = np.concatenate([self.index[name], other.index[name]])
        names = list(self.data) + [k for k in other.data if k not in self.data]
        data = {}
        for k in names:
            a = self.data.get(k, np.full(self.shape, np.nan))
            b = other.data.get(k, np.full(other.shape, np.nan))
            data[k] = np.concatenate([a, b], axis=ax)
        return PolarArray(idx, data)

    def swapAxis(self, a, b):
        names = self.dims
        names[a], names[b] = names[b], names[a]
        return PolarArray({k: self.index[k] for k in names}, {k: np.swapaxes(v, a, b) for k, v in self.data.items()})

    def sort(self, axis):
        name = self.dims[axis]
        order = np.argsort(self.index[name])
        idx = dict(self.index)
        idx[name] = self.index[name][order]
        return PolarArray(idx, {k: np.take(v, order, axis=axis) for k, v in self.data.items()})

    def _binary(self, other, varsList, sign):
        data = {k: v.copy() for k, v in self.data.items()}
        for k in (varsList or list(self.data)):
            if k in other.data:
                data[k] = self.data[k] + sign * other.data[k]
        return PolarArray(self.index, data)

    def add(self, other, varsList=None):
        return self._binary(other, varsList, 1.0)

    def subtract(self, other, varsList=None):
        return self._binary(other, varsList, -1.0)

    def assign(self, value, sliceType='slice', varNames=None, **cond):
        """Set `varNames` (default all) to `value` where the condition on one variable or index holds."""
        out = self.copy()
        (name, ref), = cond.items()
        a = self[name]
        if sliceType == 'slice':
            mask = np.isclose(a, ref, atol=1e-7)
        elif sliceType == 'sliceLess':
            mask = a < ref
        elif sliceType == 'sliceGreater':
            mask = a > ref
        else:
            raise ValueError(sliceType)
        for k in (varNames or list(out.data)):
            out.data[k][mask] = value
        return out

    def interp(self, targets, asAxis=None, kind='linear', bounds_error=False, fill_value=np.nan):
        """Interpolate onto the grids of `targets`, one after the other, in the order given (see the module docstring)."""
        out = self
        for name, grid in targets.items():
            out = out._interp_one(name, np.atleast_1d(np.asarray(grid, dtype=float)), (asAxis or {}).get(name, name), kind, fill_value)
        return out

    def _interp_one(self, name, grid, axis_name, kind, fill_value):
        ax = self.dims.index(axis_name)
        n_other = int(np.prod(self.shape)) // self.shape[ax]
        newshape = list(self.shape)
        newshape[ax] = grid.size
        names = [k for k in self.data if k != name]
        xfull = np.moveaxis(self[name], ax, -1).reshape(n_other, -1)
        data = {}
        for k in names + ([axis_name] if axis_name != name and axis_name != '__index__' else []):
            yfull = np.moveaxis(self[k], ax, -1).reshape(n_other, -1)
            res = np.empty((n_other, grid.size))
            for i in range(n_other):
                res[i] = _line(xfull[i], yfull[i], grid, kind, fill_value)
            ms = list(np.moveaxis(np.empty(newshape), ax, -1).shape)
            data[k] = np.moveaxis(res.reshape(ms), -1, ax)
        idx = {}
        for k in self.dims:
            if k == axis_name:
                idx[name] = grid
            else:
                idx[k] = self.index[k]
        return PolarArray(idx, data)

    def polyFitCoeffs(self, xVar, polyOrder=1, asAxis=None):
        """Least squares per line; the fitted axis becomes `coeffs` (0 = highest power, numpy.polyfit order)."""
        ax = self.dims.index(xVar) if asAxis is None else (asAxis if asAxis >= 0 else len(self.dims) + asAxis)
        fitted = self.dims[ax]
        n_other = int(np.prod(self.shape)) // self.shape[ax]
        xfull = np.moveaxis(self[xVar], ax, -1).reshape(n_other, -1)
        data = {}
        idx = {}
        for k in self.dims:
            idx['coeffs' if k == fitted else k] = np.arange(polyOrder + 1, dtype=float) if k == fitted else self.index[k]
        newshape = list(self.shape)
        newshape[ax] = polyOrder + 1
        ms = list(np.moveaxis(np.empty(newshape), ax, -1).shape)
        for k, v in self.data.items():
            y = np.moveaxis(v, ax, -1).reshape(n_other, -1)
            res = np.full((n_other, polyOrder + 1), np.nan)
            for i in range(n_other):
                ok = np.isfinite(xfull[i]) & np.isfinite(y[i])
                if ok.sum() > polyOrder:
                    res[i] = np.polyfit(xfull[i][ok], y[i][ok], polyOrder)
            data[k] = np.moveaxis(res.reshape(ms), -1, ax)
        return PolarArray(idx, data)

    def atMaximum(self, name, argAxis):
        """Along one axis, keep the point where `name` is largest; the axis stays with length 1 and its index becomes a variable."""
        axname = self.dims[argAxis]
        sel = np.nan_to_num(self[name], nan=-np.inf)
        arg = np.expand_dims(np.argmax(sel, axis=argAxis), argAxis)
        idx = dict(self.index)
        idx[axname] = np.array([np.nan])
        data = {k: np.take_along_axis(v, arg, axis=argAxis) for k, v in self.data.items()}
        data[axname] = np.take_along_axis(np.array(self[axname]), arg, axis=argAxis)
        return PolarArray(idx, data)


def from_files(files, folder, names, rename=None, keep=None, xvar=None, grid=None, kind='linear', fill_value='extrapolate', by_row=False):
    """Stack superfile CSVs into one array. `files` maps a key tuple to a file name; `names` names the key axes.

    Each table is put on the last axis either by interpolation of `xvar` onto `grid` or, with `by_row`, by its row number.
    Variables are the union over the files; a variable a file lacks is NaN there.
    """
    tables = {k: read_table(folder + '/' + v, rename) for k, v in files.items()}
    vals = [sorted({k[i] for k in files}) for i in range(len(names))]
    if by_row:
        last_name, last = '__index__', np.arange(max(len(next(iter(t.values()))) for t in tables.values()), dtype=float)
    else:
        last_name, last = xvar, np.asarray(grid, dtype=float)
    shape = [len(v) for v in vals] + [last.size]
    varnames = set()
    for t in tables.values():
        varnames |= set(t)
    varnames -= set(names) | {last_name}
    if keep:
        varnames &= set(keep)
    data = {k: np.full(shape, np.nan) for k in varnames}
    for key, t in tables.items():
        pos = tuple(vals[i].index(key[i]) for i in range(len(names)))
        for k in varnames:
            if k not in t:
                continue
            if by_row:
                data[k][pos][:t[k].size] = t[k]
            else:
                data[k][pos] = _line(t[xvar], t[k], last, kind, fill_value)
    idx = {n: vals[i] for i, n in enumerate(names)}
    idx[last_name] = last
    return PolarArray(idx, data)
