"""Solar coordinate geometry, ported from HelioFleet's js/frames.js.

Inputs are heliocentric ICRF-ecliptic (J2000) vectors in au. Stonyhurst
(HEEQ) and Carrington longitudes follow the IAU solar rotation model (pole
RA 286.13 deg, Dec 63.87 deg, W = 84.176 deg + 14.1844 deg/day since J2000 TT),
with the Sun seen one light time in the past for Carrington, as in SunPy.

Vectors are plain 3-tuples (or any length-3 sequence) of floats, so the module
needs only the standard library.
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
    """Scalar product of two 3-vectors.

    Parameters
    ----------
    a, b : sequence of float
        Vectors of length 3.

    Returns
    -------
    float
        ``a . b``.

    Examples
    --------
    >>> dot((1, 2, 3), (4, 5, 6))
    32
    """
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def norm(a):
    """Euclidean length of a 3-vector.

    Parameters
    ----------
    a : sequence of float
        Vector of length 3.

    Returns
    -------
    float
        ``|a|``, in the units of ``a``.

    Examples
    --------
    >>> norm((3, 4, 0))
    5.0
    """
    return math.sqrt(dot(a, a))


def scale(a, s):
    """Multiply a 3-vector by a scalar.

    Parameters
    ----------
    a : sequence of float
        Vector of length 3.
    s : float
        Factor.

    Returns
    -------
    tuple of float
        ``s * a``.

    Examples
    --------
    >>> scale((1, 2, 3), 2)
    (2, 4, 6)
    """
    return (a[0] * s, a[1] * s, a[2] * s)


def sub(a, b):
    """Difference of two 3-vectors.

    Parameters
    ----------
    a, b : sequence of float
        Vectors of length 3.

    Returns
    -------
    tuple of float
        ``a - b``.

    Examples
    --------
    >>> sub((1, 2, 3), (1, 1, 1))
    (0, 1, 2)
    """
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def unit(a):
    """Unit vector along a 3-vector.

    Parameters
    ----------
    a : sequence of float
        Non-zero vector of length 3.

    Returns
    -------
    tuple of float
        ``a / |a|``.

    Examples
    --------
    >>> unit((0, 0, 2))
    (0.0, 0.0, 1.0)
    """
    return scale(a, 1 / norm(a))


def cross(a, b):
    """Vector product of two 3-vectors.

    Parameters
    ----------
    a, b : sequence of float
        Vectors of length 3.

    Returns
    -------
    tuple of float
        ``a x b``.

    Examples
    --------
    >>> cross((1, 0, 0), (0, 1, 0))
    (0, 0, 1)
    """
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def eq_to_ecl(v):
    """Rotate a vector from the J2000 equatorial frame to the J2000 ecliptic frame.

    Parameters
    ----------
    v : sequence of float
        Equatorial (ICRF) vector of length 3.

    Returns
    -------
    tuple of float
        The same vector in ecliptic coordinates (obliquity 23.4392911 deg).

    Examples
    --------
    The celestial north pole, seen in ecliptic coordinates:

    >>> tuple(round(c, 4) for c in eq_to_ecl((0, 0, 1)))
    (0, 0.3978, 0.9175)
    """
    return (v[0], v[1] * math.cos(EPS) + v[2] * math.sin(EPS), -v[1] * math.sin(EPS) + v[2] * math.cos(EPS))


def wrap360(a):
    """Wrap an angle into [0, 360).

    Parameters
    ----------
    a : float
        Angle in degrees.

    Returns
    -------
    float
        The same direction, in [0, 360) degrees.

    Examples
    --------
    >>> wrap360(-90.0)
    270.0
    """
    return a % 360.0


def wrap180(a):
    """Wrap an angle into [-180, 180).

    Parameters
    ----------
    a : float
        Angle in degrees.

    Returns
    -------
    float
        The same direction, in [-180, 180) degrees.

    Examples
    --------
    >>> wrap180(270.0)
    -90.0
    """
    return (a + 180.0) % 360.0 - 180.0


_A0, _D0 = 286.13 * D, 63.87 * D
POLE = eq_to_ecl((math.cos(_D0) * math.cos(_A0), math.cos(_D0) * math.sin(_A0), math.sin(_D0)))
NODE = eq_to_ecl((math.cos(_A0 + math.pi / 2), math.sin(_A0 + math.pi / 2), 0.0))
NODE_Q = cross(POLE, NODE)


def prime_meridian(jd_ut: float):
    """Prime-meridian direction of the Carrington frame, and its 90 deg partner.

    Parameters
    ----------
    jd_ut : float
        Julian date (UT) at which the Sun is seen; converted to TT with a fixed 69.2 s.

    Returns
    -------
    m, q : tuple of float
        Ecliptic unit vectors in the solar equatorial plane: ``m`` points to Carrington
        longitude 0 and ``q`` to longitude 90 (``q = POLE x m``).

    Examples
    --------
    >>> m, q = prime_meridian(2451545.0)
    >>> round(norm(m), 12), round(abs(dot(m, q)), 12)
    (1.0, 0.0)
    """
    d = jd_ut + 69.2 / 86400 - 2451545.0  # UT -> TT
    w = (84.176 + 14.1844 * d) * D
    m = tuple(NODE[i] * math.cos(w) + NODE_Q[i] * math.sin(w) for i in range(3))
    return m, cross(POLE, m)


def heliographic(r, e, jd: float, light: float | None = None) -> dict:
    """Heliographic coordinates of a heliocentric position.

    Parameters
    ----------
    r : sequence of float
        Heliocentric ecliptic J2000 position of the body (au).
    e : sequence of float
        Heliocentric ecliptic J2000 position of Earth at the same time (au).
    jd : float
        Julian date (UT).
    light : float, optional
        Distance (au) from the Sun of the observer whose light time sets the Carrington
        longitude. Default: Earth's distance, as SunPy's ``HeliographicCarrington(observer='earth')``.
        Pass the body's own distance for its disk-centre L0 (CRLN_OBS).

    Returns
    -------
    dict
        ``dist`` (au), ``lat`` (Stonyhurst latitude, deg), ``lon`` (Stonyhurst longitude, deg,
        west positive, in [-180, 180)) and ``carr`` (Carrington longitude, deg, in [0, 360)).

    Examples
    --------
    >>> g = heliographic((0.5, 0.5, 0.0), (1.0, 0.0, 0.0), 2451545.0)
    >>> {k: round(v, 3) for k, v in g.items()}
    {'dist': 0.707, 'lat': 3.702, 'lon': 45.092, 'carr': 306.431}
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
    """Angle between two vectors.

    Parameters
    ----------
    a, b : sequence of float
        Non-zero vectors of length 3, e.g. two heliocentric positions.

    Returns
    -------
    float
        Angle in degrees, in [0, 180]; for heliocentric positions, their Sun-centred separation.

    Examples
    --------
    >>> angle_between((1, 0, 0), (0, 1, 0))
    90.0
    """
    c = dot(a, b) / (norm(a) * norm(b))
    return math.acos(max(-1.0, min(1.0, c))) / D


def footpoint_lon(lon: float, r: float, v: float) -> float:
    """Stonyhurst longitude of the nominal Parker-spiral footpoint.

    Uses ``lon + Omega (r - R_sun) / v`` with the sidereal rotation rate 14.1844 deg/day
    and a constant radial wind speed.

    Parameters
    ----------
    lon : float
        Stonyhurst longitude of the body (deg).
    r : float
        Distance of the body from the Sun (au).
    v : float
        Solar-wind speed (km/s).

    Returns
    -------
    float
        Footpoint longitude (deg), in [-180, 180).

    Examples
    --------
    The footpoint of a body at 1 au for a 400 km/s wind:

    >>> round(footpoint_lon(0.0, 1.0, 400.0), 2)
    61.11
    """
    return wrap180(lon + (OMEGA_SIDEREAL * (r - R_SUN_AU) * AU_KM / v) / D)


def to_hee(p, e):
    """Convert a heliocentric ecliptic J2000 position to Heliocentric Earth Ecliptic (HEE).

    Parameters
    ----------
    p : sequence of float
        Heliocentric ecliptic J2000 position (au).
    e : sequence of float
        Earth's heliocentric ecliptic J2000 position at the same time (au).

    Returns
    -------
    tuple of float
        HEE position (au): +x toward Earth, +z ecliptic north.

    Examples
    --------
    >>> tuple(round(c, 6) for c in to_hee((0.0, 1.0, 0.0), (0.0, 1.0, 0.0)))
    (1.0, 0.0, 0.0)
    """
    lon = math.atan2(e[1], e[0])
    c, s = math.cos(lon), math.sin(lon)
    return (c * p[0] + s * p[1], -s * p[0] + c * p[1], p[2])
