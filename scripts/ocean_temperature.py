"""Small, dependency-light NOAA NetCDF and provenance helpers.

libnetcdf reads both classic and HDF5 NetCDF; packed fields are decoded explicitly.
No remote request occurs during preparation or rendering.
"""
from __future__ import annotations

import ctypes as C
import ctypes.util
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(8 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


class NetCDF:
    lib = C.CDLL(ctypes.util.find_library('netcdf'))
    lib.nc_strerror.restype = C.c_char_p

    def check(self, status):
        if status:
            raise RuntimeError(self.lib.nc_strerror(status).decode())

    def __init__(self, path):
        self.id = C.c_int()
        self.check(self.lib.nc_open(str(path).encode(), 0, C.byref(self.id)))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.check(self.lib.nc_close(self.id))

    def variable(self, name):
        result = C.c_int()
        self.check(self.lib.nc_inq_varid(self.id, name.encode(), C.byref(result)))
        return result.value

    def attributes(self, name=None):
        var = self.variable(name) if name else -1
        count = C.c_int()
        self.check(self.lib.nc_inq_varnatts(self.id, var, C.byref(count)))
        result = {}
        for i in range(count.value):
            key = C.create_string_buffer(257)
            self.check(self.lib.nc_inq_attname(self.id, var, i, key))
            length, kind = C.c_size_t(), C.c_int()
            self.check(self.lib.nc_inq_att(self.id, var, key, C.byref(kind), C.byref(length)))
            if kind.value == 2:
                value = C.create_string_buffer(length.value + 1)
                self.check(self.lib.nc_get_att_text(self.id, var, key, value))
                value = value.value.decode('utf-8', errors='replace')
            elif kind.value == 12:  # NC_STRING (not used by the selected products)
                continue
            else:
                value = np.empty(length.value, dtype='float64')
                self.check(self.lib.nc_get_att_double(self.id, var, key, value.ctypes.data_as(C.POINTER(C.c_double))))
                value = value.item() if value.size == 1 else value.tolist()
            result[key.value.decode()] = value
        return result

    def shape(self, name):
        var, ndims = self.variable(name), C.c_int()
        self.check(self.lib.nc_inq_varndims(self.id, var, C.byref(ndims)))
        dims = (C.c_int * ndims.value)()
        self.check(self.lib.nc_inq_vardimid(self.id, var, dims))
        result = []
        for dim in dims:
            length = C.c_size_t()
            self.check(self.lib.nc_inq_dimlen(self.id, dim, C.byref(length)))
            result.append(length.value)
        return tuple(result)

    def read(self, name, start=None, count=None, decode=True):
        shape = self.shape(name)
        start = start or (0,) * len(shape)
        count = count or shape
        result = np.empty(count, dtype='float32')
        self.check(self.lib.nc_get_vara_float(self.id, self.variable(name),
                   (C.c_size_t * len(shape))(*start), (C.c_size_t * len(shape))(*count),
                   result.ctypes.data_as(C.POINTER(C.c_float))))
        if decode:
            attrs = self.attributes(name)
            invalid = ~np.isfinite(result)
            for key in ('_FillValue', 'missing_value'):
                if key in attrs:
                    invalid |= result == np.float32(attrs[key])
            if 'valid_range' in attrs:
                lo, hi = attrs['valid_range']
                invalid |= (result < lo) | (result > hi)
            if 'valid_min' in attrs:
                invalid |= result < attrs['valid_min']
            if 'valid_max' in attrs:
                invalid |= result > attrs['valid_max']
            result = result * attrs.get('scale_factor', 1) + attrs.get('add_offset', 0)
            result[invalid] = np.nan
        return result


class LatLng(C.Structure):
    _fields_ = [('lat', C.c_double), ('lng', C.c_double)]


H3 = C.CDLL(ctypes.util.find_library('h3'))
H3.latLngToCell.argtypes = [C.POINTER(LatLng), C.c_int, C.POINTER(C.c_uint64)]
H3.cellToLatLng.argtypes = [C.c_uint64, C.POINTER(LatLng)]


def h3_cell(lat, lon, resolution=5):
    point, value = LatLng(math.radians(lat), math.radians(lon)), C.c_uint64()
    if H3.latLngToCell(C.byref(point), resolution, C.byref(value)):
        raise ValueError('Invalid H3 coordinate')
    return value.value


def h3_center(cell):
    point = LatLng()
    if H3.cellToLatLng(int(cell), C.byref(point)):
        raise ValueError('Invalid H3 cell')
    return math.degrees(point.lat), math.degrees(point.lng)
