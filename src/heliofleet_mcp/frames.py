"""Solar coordinate geometry, ported from HelioFleet's js/frames.js.

Inputs are heliocentric ICRF-ecliptic (J2000) vectors in au. Stonyhurst
(HEEQ) and Carrington longitudes follow the IAU solar rotation model (pole
RA 286.13 deg, Dec 63.87 deg, W = 84.176 deg + 14.1844 deg/day since J2000 TT),
with the Sun seen one light time in the past for Carrington, as in SunPy.
"""

from __future__ import annotations

import math

D = math.pi / 180
EPS = 23.4392911 * D  # obliquity of the J2000 ecliptic
AU_KM = 149597870.7
C_KM_S = 299792.458
R_SUN_KM = 695700.0
R_SUN_AU = R_SUN_KM / AU_KM
OMEGA_SIDEREAL = 14.1844 * D / 86400  # rad/s
ARCSEC = math.pi / 648000


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def norm(a):
    return math.sqrt(dot(a, a))


def scale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def unit(a):
    return scale(a, 1 / norm(a))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def eq_to_ecl(v):
    return (v[0], v[1] * math.cos(EPS) + v[2] * math.sin(EPS), -v[1] * math.sin(EPS) + v[2] * math.cos(EPS))


def wrap360(a):
    return a % 360.0


def wrap180(a):
    return (a + 180.0) % 360.0 - 180.0


_A0, _D0 = 286.13 * D, 63.87 * D
POLE = eq_to_ecl((math.cos(_D0) * math.cos(_A0), math.cos(_D0) * math.sin(_A0), math.sin(_D0)))
NODE = eq_to_ecl((math.cos(_A0 + math.pi / 2), math.sin(_A0 + math.pi / 2), 0.0))
NODE_Q = cross(POLE, NODE)


def prime_meridian(jd_ut: float):
    """Prime-meridian direction of the Carrington frame (and its 90 deg partner)."""
    d = jd_ut + 69.2 / 86400 - 2451545.0  # UT -> TT
    w = (84.176 + 14.1844 * d) * D
    m = tuple(NODE[i] * math.cos(w) + NODE_Q[i] * math.sin(w) for i in range(3))
    return m, cross(POLE, m)


def heliographic(r, e, jd: float, light: float | None = None) -> dict:
    """Heliographic coordinates of position r (au) at jd (UT) with Earth at e.

    Carrington longitude is as seen from Earth unless `light` (au) gives
    another observer's distance from the Sun (its own disk-centre L0).
    """
    if light is None:
        light = norm(e)
    dist = norm(r)
    ru = scale(r, 1 / dist)
    x = unit(sub(e, scale(POLE, dot(e, POLE))))
    y = cross(POLE, x)
    lat = math.asin(max(-1.0, min(1.0, dot(ru, POLE)))) / D
    lon = math.atan2(dot(ru, y), dot(ru, x)) / D
    m, my = prime_meridian(jd - light * AU_KM / C_KM_S / 86400)
    carr = wrap360(math.atan2(dot(ru, my), dot(ru, m)) / D)
    return {"dist": dist, "lat": lat, "lon": wrap180(lon), "carr": carr}


def angle_between(a, b) -> float:
    c = dot(a, b) / (norm(a) * norm(b))
    return math.acos(max(-1.0, min(1.0, c))) / D


def footpoint_lon(lon: float, r: float, v: float) -> float:
    """Stonyhurst longitude of the Parker-spiral footpoint at r (au) for wind v (km/s)."""
    return wrap180(lon + (OMEGA_SIDEREAL * (r - R_SUN_AU) * AU_KM / v) / D)


def to_hee(p, e):
    """Heliocentric Earth Ecliptic: +x toward Earth, z = ecliptic north."""
    lon = math.atan2(e[1], e[0])
    c, s = math.cos(lon), math.sin(lon)
    return (c * p[0] + s * p[1], -s * p[0] + c * p[1], p[2])
