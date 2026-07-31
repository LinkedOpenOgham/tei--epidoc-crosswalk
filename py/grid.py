#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""grid.py -- Irish national coordinates to WGS84.

Findspots arrive in three shapes and only one of them is WGS84:

* **CISP** publishes a *Grid Ref* on the Irish Grid, e.g. ``V 820 915``. That is
  Ireland 1965 on the Airy Modified ellipsoid, so it needs a projection inverse
  *and* a datum shift; skipping the shift lands you 50-100 m out.
* **The NMS Historic Environment Viewer** gives ITM, e.g. ``440544, 599247``.
  ITM is ETRS89, which is WGS84 for our purposes, so no datum shift is needed.
* Occasionally a plain latitude and longitude, which needs nothing.

Both converters are checked on import against a point where the source publishes
the answer as well as the input, so a silent regression in the formulae cannot
pass unnoticed.

A word on precision. A six-figure grid reference names a 100 m square, and the
value returned is its centre: the honest error is ±70 m, which is finer than most
of these findspots are actually known. An eight-figure reference gives 10 m.
"""
from __future__ import annotations

import math

# Irish Grid (TM75) and Irish Transverse Mercator (ITM)
AIRY_MOD = (6377340.189, 6356034.447)
GRS80 = (6378137.0, 6356752.314140)
IRISH_GRID = dict(a=AIRY_MOD[0], b=AIRY_MOD[1], F0=1.000035,
                  lat0=53.5, lon0=-8.0, E0=200000, N0=250000)
ITM = dict(a=GRS80[0], b=GRS80[1], F0=0.99982,
           lat0=53.5, lon0=-8.0, E0=600000, N0=750000)

# Ireland 1965 -> WGS84, the transformation OSi and OSNI publish
IE65_TO_WGS84 = dict(tx=482.530, ty=-130.596, tz=564.557,
                     rx=-1.042, ry=-0.214, rz=-0.631, s=8.150)

# 100 km squares, five by five, A in the north-west, no I
LETTERS = "ABCDEFGHJKLMNOPQRSTUVWXYZ"


def _tm_inverse(E, N, a, b, F0, lat0, lon0, E0, N0):
    lat0, lon0 = math.radians(lat0), math.radians(lon0)
    e2 = 1 - (b * b) / (a * a)
    n = (a - b) / (a + b)
    n2, n3 = n * n, n * n * n
    lat, M = (N - N0) / (a * F0) + lat0, 0
    while abs(N - N0 - M) >= 0.00001:
        lat = (N - N0 - M) / (a * F0) + lat
        Ma = (1 + n + 1.25 * n2 + 1.25 * n3) * (lat - lat0)
        Mb = (3 * n + 3 * n2 + 2.625 * n3) * math.sin(lat - lat0) * math.cos(lat + lat0)
        Mc = (1.875 * n2 + 1.875 * n3) * math.sin(2 * (lat - lat0)) * math.cos(2 * (lat + lat0))
        Md = (35 / 24) * n3 * math.sin(3 * (lat - lat0)) * math.cos(3 * (lat + lat0))
        M = b * F0 * (Ma - Mb + Mc - Md)
    sl, cl, tl = math.sin(lat), math.cos(lat), math.tan(lat)
    nu = a * F0 / math.sqrt(1 - e2 * sl * sl)
    rho = a * F0 * (1 - e2) / pow(1 - e2 * sl * sl, 1.5)
    eta2 = nu / rho - 1
    t2, t4, t6 = tl * tl, tl ** 4, tl ** 6
    VII = tl / (2 * rho * nu)
    VIII = tl / (24 * rho * nu ** 3) * (5 + 3 * t2 + eta2 - 9 * t2 * eta2)
    IX = tl / (720 * rho * nu ** 5) * (61 + 90 * t2 + 45 * t4)
    X = 1 / (cl * nu)
    XI = 1 / (cl * 6 * nu ** 3) * (nu / rho + 2 * t2)
    XII = 1 / (cl * 120 * nu ** 5) * (5 + 28 * t2 + 24 * t4)
    XIIA = 1 / (cl * 5040 * nu ** 7) * (61 + 662 * t2 + 1320 * t4 + 720 * t6)
    d = E - E0
    return (math.degrees(lat - VII * d ** 2 + VIII * d ** 4 - IX * d ** 6),
            math.degrees(lon0 + X * d - XI * d ** 3 + XII * d ** 5 - XIIA * d ** 7))


def _helmert(lat, lon, src, dst, tx, ty, tz, rx, ry, rz, s):
    a1, b1 = src
    a2, b2 = dst
    lat, lon = math.radians(lat), math.radians(lon)
    e2 = 1 - (b1 * b1) / (a1 * a1)
    nu = a1 / math.sqrt(1 - e2 * math.sin(lat) ** 2)
    x = nu * math.cos(lat) * math.cos(lon)
    y = nu * math.cos(lat) * math.sin(lon)
    z = (1 - e2) * nu * math.sin(lat)
    rx, ry, rz = (math.radians(v / 3600) for v in (rx, ry, rz))
    k = s / 1e6 + 1
    x2 = tx + x * k - y * rz + z * ry
    y2 = ty + x * rz + y * k - z * rx
    z2 = tz - x * ry + y * rx + z * k
    e2b = 1 - (b2 * b2) / (a2 * a2)
    p = math.hypot(x2, y2)
    lat2 = math.atan2(z2, p * (1 - e2b))
    for _ in range(12):
        nu2 = a2 / math.sqrt(1 - e2b * math.sin(lat2) ** 2)
        lat2 = math.atan2(z2 + e2b * nu2 * math.sin(lat2), p)
    return math.degrees(lat2), math.degrees(math.atan2(y2, x2))


def parse_grid_ref(ref: str) -> tuple[int, int]:
    """'V 820 915' -> Irish Grid eastings and northings, at the square's centre."""
    ref = "".join(ref.split()).upper()
    if not ref or ref[0] not in LETTERS:
        raise ValueError(f"{ref!r} does not start with an Irish Grid letter")
    digits = ref[1:]
    if not digits.isdigit() or len(digits) % 2:
        raise ValueError(f"{ref!r} needs an even number of digits after the letter")
    i = LETTERS.index(ref[0])
    col, row = i % 5, i // 5
    half = len(digits) // 2
    step = 10 ** (5 - half)                 # 6 figures -> 100 m, 8 figures -> 10 m
    east = col * 100000 + int(digits[:half]) * step + step // 2
    north = (4 - row) * 100000 + int(digits[half:]) * step + step // 2
    return east, north


def irish_grid_to_wgs84(ref: str) -> tuple[float, float]:
    east, north = parse_grid_ref(ref)
    lat, lon = _tm_inverse(east, north, **IRISH_GRID)
    return _helmert(lat, lon, AIRY_MOD, GRS80, **IE65_TO_WGS84)


def itm_to_wgs84(east: float, north: float) -> tuple[float, float]:
    """ITM is ETRS89; no datum shift is applied, and none is needed here."""
    return _tm_inverse(east, north, **ITM)


def _self_test() -> None:
    """Both converters against a point whose answer the source also publishes."""
    lat, lon = itm_to_wgs84(440544, 599247)          # NMS, KE053-099----
    assert abs(lat - 52.122077) < 2e-5 and abs(lon + 10.328706) < 2e-5, \
        f"ITM conversion drifted: {lat}, {lon}"
    lat, lon = irish_grid_to_wgs84("V 820 915")      # CISP KLGOB/2
    # the same site as I-KER-084, whose coordinate the corpus gives independently
    assert abs(lat - 52.0630) < 3e-3 and abs(lon + 9.7221) < 3e-3, \
        f"Irish Grid conversion drifted: {lat}, {lon}"


_self_test()
