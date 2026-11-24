"""Observation footprints of high-resolution solar instruments, from HelioFleet's data/obs/.

The files are built by HelioFleet's scripts/fetch_observations.py from the IRIS coverage
registry, the Hinode/EIS as-run catalogue, the DKIST Data Center, the Solar Orbiter Archive and
a curated list of sounding-rocket flights. Solar Orbiter fields are recorded in Solar Orbiter's
own helioprojective frame and are carried into Earth's view through the solar surface, as
js/observations.js does for the sky view.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from urllib.parse import urlencode

from .data import Store
from .links import sky_link
from .timeutil import iso, parse_time

INSTRUMENTS = {
    "cryonirsp": ("DKIST Cryo-NIRSP", "dkist"), "vbi": ("DKIST VBI", "dkist"), "visp": ("DKIST ViSP", "dkist"),
    "dlnirsp": ("DKIST DL-NIRSP", "dkist"), "vtf": ("DKIST VTF", "dkist"), "iris": ("IRIS", "iris"),
    "eis": ("Hinode EIS", "eis"), "euihri": ("Solar Orbiter EUI-HRI EUV", "solo"),
    "euilya": ("Solar Orbiter EUI-HRI Lyman-alpha", "solo"), "phihrt": ("Solar Orbiter PHI-HRT", "solo"),
    "spice": ("Solar Orbiter SPICE", "solo"), "hic": ("Hi-C sounding rocket", "rocket"),
    "clasp": ("CLASP sounding rockets", "rocket"),
}
FACILITIES = sorted({f for _, f in INSTRUMENTS.values()})
MAX_RANGE_DAYS = 366
RAD = math.pi / 180
ARC = RAD / 3600
R_SUN_AU = 695700 / 149597870.7
JD_UNIX = 2440587.5
HELIOVIEWER = "https://api.helioviewer.org/v2/takeScreenshot/?"
LAYERS = {"aia171": "[SDO,AIA,AIA,171,1,100]", "aia193": "[SDO,AIA,AIA,193,1,100]",
          "hmi": "[SDO,HMI,HMI,magnetogram,1,100]"}


def _jd(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() / 86400 + JD_UNIX


def _month(jd: float) -> str:
    return datetime.fromtimestamp((jd - JD_UNIX) * 86400, tz=timezone.utc).strftime("%Y-%m")


def earth_view(jd: float) -> tuple[float, float, float]:
    """Earth's position for the footprint transform, after Meeus (as js/observations.js).

    Parameters
    ----------
    jd : float
        Julian date (UT).

    Returns
    -------
    tuple of float
        Stonyhurst longitude (always 0), B0 (deg) and distance from the Sun (au).

    Examples
    --------
    >>> [round(v, 3) for v in earth_view(2451545.0)]
    [0.0, -3.014, 0.983]
    """
    t = (jd - 2451545) / 36525
    m = (357.52911 + 35999.05029 * t) * RAD
    lon = 280.46646 + 36000.76983 * t + (1.914602 - 0.004817 * t) * math.sin(m) + 0.019993 * math.sin(2 * m)
    node = 73.6667 + 1.3958333 * (jd - 2396758) / 36525
    b0 = math.asin(math.sin((lon - node) * RAD) * math.sin(7.25 * RAD)) / RAD
    return 0.0, b0, 1.000140 - 0.016708 * math.cos(m) - 0.000139 * math.cos(2 * m)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _axes(lon, lat, d):
    o = [d * math.cos(lat * RAD) * math.cos(lon * RAD), d * math.cos(lat * RAD) * math.sin(lon * RAD),
         d * math.sin(lat * RAD)]
    s = [-v / d for v in o]
    n = [-s[2] * s[0], -s[2] * s[1], 1 - s[2] * s[2]]
    nn = math.hypot(*n)
    n = [v / nn for v in n]
    w = [s[1] * n[2] - s[2] * n[1], s[2] * n[0] - s[0] * n[2], s[0] * n[1] - s[1] * n[0]]
    return {"o": o, "s": s, "n": n, "w": w}


def _carry(tx, ty, frm, to):
    a, b = tx * ARC, ty * ARC
    d = [math.cos(b) * math.cos(a) * frm["s"][k] + math.cos(b) * math.sin(a) * frm["w"][k] + math.sin(b) * frm["n"][k]
         for k in range(3)]
    od = _dot(frm["o"], d)
    disc = od * od - (_dot(frm["o"], frm["o"]) - R_SUN_AU ** 2)
    t = -od - math.sqrt(disc) if disc >= 0 else -od
    p = [frm["o"][k] + t * d[k] for k in range(3)]
    v = [p[k] - to["o"][k] for k in range(3)]
    r = math.hypot(*v)
    hidden = disc >= 0 and _dot(p, p) > _dot(p, to["o"])
    return (math.atan2(_dot(v, to["w"]), _dot(v, to["s"])) / ARC, math.asin(_dot(v, to["n"]) / r) / ARC, hidden)


def earth_polygon(row: dict, jd: float) -> tuple[list[float], list[float], bool]:
    """The footprint in Earth's helioprojective view: as recorded, or carried over from Solar Orbiter.

    Parameters
    ----------
    row : dict
        One observation from a monthly file (``x``, ``y``, ``f`` and, for Solar Orbiter, ``o``).
    jd : float
        Moment of Earth's view (the observation's mid-time).

    Returns
    -------
    tuple
        Polygon ``x`` and ``y`` (arcsec, closed) and whether most of it is on the far side of the Sun
        from Earth.

    Examples
    --------
    >>> earth_polygon({"f": "E", "x": [0, 10, 10, 0], "y": [0, 0, 10, 10]}, 2460000.5)
    ([0, 10, 10, 0], [0, 0, 10, 10], False)
    """
    if row.get("f") != "S":
        return row["x"], row["y"], False
    frm = _axes(*row["o"])
    to = _axes(*earth_view(jd))
    xs, ys, hid = [], [], 0
    for i in range(len(row["x"]) - 1):
        for k in range(8):
            u = k / 8
            tx, ty, h = _carry(row["x"][i] + (row["x"][i + 1] - row["x"][i]) * u,
                               row["y"][i] + (row["y"][i + 1] - row["y"][i]) * u, frm, to)
            xs.append(round(tx, 1))
            ys.append(round(ty, 1))
            hid += h
    xs.append(xs[0])
    ys.append(ys[0])
    return xs, ys, hid > 0.5 * (len(xs) - 1)


def _inside(px, py, xs, ys):
    c = False
    j = len(xs) - 1
    for i in range(len(xs)):
        if (ys[i] > py) != (ys[j] > py) and px < (xs[j] - xs[i]) * (py - ys[i]) / (ys[j] - ys[i] + 1e-300) + xs[i]:
            c = not c
        j = i
    return c


def _edge_distance(px, py, xs, ys):
    best = math.inf
    for i in range(len(xs) - 1):
        ax, ay, bx, by = xs[i], ys[i], xs[i + 1], ys[i + 1]
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        t = 0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
        best = min(best, math.hypot(px - ax - t * dx, py - ay - t * dy))
    return best


def image_urls(t_iso: str, x0: float, y0: float, w: float, h: float) -> dict[str, str]:
    """Helioviewer PNG cutouts of SDO AIA 171, AIA 193 and HMI around a field (as the sky view loads).

    Parameters
    ----------
    t_iso : str
        Image time (UTC, ISO 8601).
    x0, y0 : float
        Field centre in Earth's helioprojective view (arcsec).
    w, h : float
        Field width and height (arcsec); the cutout is 720 pixels across, at least 1.25 times the field.

    Returns
    -------
    dict
        PNG URL per channel: ``aia171``, ``aia193``, ``hmi``.

    Examples
    --------
    >>> sorted(image_urls("2024-03-01T04:41:06Z", 0, 50, 120, 120))
    ['aia171', 'aia193', 'hmi']
    """
    scale = round(max(0.6, max(w, h, 330) * 1.25 / 720), 3)
    out = {}
    for ch, layer in LAYERS.items():
        q = {"date": t_iso, "imageScale": scale, "layers": layer, "x0": round(x0), "y0": -round(y0),
             "width": 720, "height": 720, "display": "true", "watermark": "false"}
        out[ch] = HELIOVIEWER + urlencode(q, safe="[],")
    return out


class Observations:
    """Search HelioFleet's observation footprints and its list of coordinated observations.

    Parameters
    ----------
    store : Store, optional
        The data source (default: a new [`Store`][heliofleet_mcp.data.Store]).

    Examples
    --------
    >>> Observations().coordinated("2012-07-11", "2012-07-12", "rocket")["groups"][0]["first_id"]
    'hic-2012'
    """

    def __init__(self, store: Store | None = None):
        self.store = store or Store()

    def _wanted(self, instruments):
        if not instruments:
            return set(INSTRUMENTS)
        names = [s.strip().lower().replace("-", "") for s in
                 (instruments.split(",") if isinstance(instruments, str) else instruments) if s.strip()]
        keep = set()
        for n in names:
            if n in INSTRUMENTS:
                keep.add(n)
            elif n in FACILITIES or n in ("rockets", "hinode"):
                fac = {"rockets": "rocket", "hinode": "eis"}.get(n, n)
                keep |= {k for k, (_, f) in INSTRUMENTS.items() if f == fac}
            else:
                raise ValueError(f"unknown instrument {n!r}; use one of {', '.join(sorted(INSTRUMENTS))} "
                                 f"or a facility: {', '.join(FACILITIES)}")
        return keep

    def search(self, start=None, end=None, instruments=None, x_arcsec=None, y_arcsec=None, radius_arcsec=0.0,
               max_results=50, include_images=True):
        """Observations that overlap a time range, optionally covering a point on the Sun.

        Parameters
        ----------
        start, end : str or float, optional
            UTC range. Default: the day starting at ``start`` (now if not given). At most a year.
        instruments : str or list of str, optional
            Instrument keys (``iris``, ``eis``, ``vbi``, ``visp``, ``dlnirsp``, ``vtf``,
            ``cryonirsp``, ``euihri``, ``euilya``, ``phihrt``, ``spice``, ``hic``, ``clasp``) or
            facilities (``dkist``, ``iris``, ``eis``, ``solo``, ``rocket``). Default: all.
        x_arcsec, y_arcsec : float, optional
            A point in Earth's helioprojective view (arcsec); keep fields that contain it.
        radius_arcsec : float, optional
            Also keep fields within this distance of the point.
        max_results : int, optional
            Most observations returned, earliest first (default 50); ``total`` counts all matches.
        include_images : bool, optional
            Add Helioviewer PNG cutouts (SDO AIA 171, AIA 193, HMI) around each field.

        Returns
        -------
        dict
            ``range_utc``, ``total``, ``returned``, ``observations`` and ``sources``.

        Examples
        --------
        >>> r = Observations().search("2024-03-01T04:00Z", "2024-03-01T06:00Z", "iris")
        >>> r["observations"][0]["id"]
        '20240301_043205_3882010194'
        """
        jd0 = parse_time(start)
        jd1 = parse_time(end) if end is not None else jd0 + 1
        if jd1 < jd0:
            raise ValueError("end is before start")
        if jd1 - jd0 > MAX_RANGE_DAYS:
            raise ValueError(f"range longer than {MAX_RANGE_DAYS} days; search a year at a time")
        if (x_arcsec is None) != (y_arcsec is None):
            raise ValueError("give both x_arcsec and y_arcsec, or neither")
        keep = self._wanted(instruments)
        idx = self.store.json("data/obs/index.json") or {"months": {}}
        months, t = [], jd0 - 1
        while True:
            m = _month(t)
            if m not in months:
                months.append(m)
            if t >= jd1:
                break
            t = min(t + 27, jd1)
        hits = []
        for m in months:
            if not (set(idx["months"].get(m, {})) & keep):
                continue
            for r in (self.store.json(f"data/obs/{m}.json") or {"rows": []})["rows"]:
                if r.get("i") not in keep:
                    continue
                j0 = _jd(r["t0"])
                j1 = min(_jd(r.get("t1") or r["t0"]), j0 + 1)  # catalogue durations over a day are cut, as on the page
                if j1 < jd0 or j0 > jd1:
                    continue
                hits.append((j0, j1, r))
        hits.sort(key=lambda h: h[0])
        out = []
        for j0, j1, r in hits:
            mid = (j0 + j1) / 2
            xs, ys, far = earth_polygon(r, mid)
            if x_arcsec is not None:
                if not (_inside(x_arcsec, y_arcsec, xs, ys) or
                        (radius_arcsec and _edge_distance(x_arcsec, y_arcsec, xs, ys) <= radius_arcsec)):
                    continue
            out.append((j0, j1, mid, r, xs, ys, far))
        total = len(out)
        obs = [self._record(*o, include_images) for o in out[:max_results]]
        return {
            "range_utc": [iso(jd0), iso(jd1)],
            "point_arcsec": None if x_arcsec is None else [x_arcsec, y_arcsec, radius_arcsec],
            "total": total, "returned": len(obs), "observations": obs,
            "frame_note": "field_earth_view is helioprojective arcsec as seen from Earth (x west, y north of Sun "
                          "centre). Solar Orbiter fields are recorded from Solar Orbiter and carried to Earth's "
                          "view through the solar surface; recorded_field keeps them as recorded.",
            "sources": idx.get("sources"),
        }

    @staticmethod
    def _record(j0, j1, mid, r, xs, ys, far, include_images):
        px, py = xs[:-1] or xs, ys[:-1] or ys
        cx, cy = (max(px) + min(px)) / 2, (max(py) + min(py)) / 2
        w, h = max(px) - min(px), max(py) - min(py)
        name, fac = INSTRUMENTS.get(r["i"], (r["i"], r["i"]))
        t_mid = iso(mid)
        rec = {
            "instrument": r["i"], "instrument_name": name, "facility": fac, "id": r["id"],
            "start_utc": iso(j0), "end_utc": iso(j1), "description": r.get("n"),
            "field_earth_view": {"center_x_arcsec": round(cx, 1), "center_y_arcsec": round(cy, 1),
                                 "width_arcsec": round(w, 1), "height_arcsec": round(h, 1),
                                 "polygon_x_arcsec": xs, "polygon_y_arcsec": ys, "far_side": far},
            "data_link": r.get("u"),
            "sky_view_link": sky_link(mid, zoom=1.6),
        }
        if "sx" in r:
            rec["slit_jaw_field_earth_view"] = {"polygon_x_arcsec": r["sx"], "polygon_y_arcsec": r["sy"]}
        if r.get("f") == "S":
            rec["recorded_field"] = {"frame": "Solar Orbiter helioprojective", "polygon_x_arcsec": r["x"],
                                     "polygon_y_arcsec": r["y"],
                                     "observer_hgs_lon_deg": r["o"][0], "observer_hgs_lat_deg": r["o"][1],
                                     "observer_r_au": r["o"][2]}
        if include_images and not far:
            rec["sdo_images_png"] = image_urls(t_mid, cx, cy, w, h)
        return rec

    def coordinated(self, start=None, end=None, facilities=None, max_results=50):
        """Groups of observations by different facilities that overlap in time and on the Sun.

        Parameters
        ----------
        start, end : str or float, optional
            UTC range. Default: one year from ``start`` (now if not given).
        facilities : str or list of str, optional
            Keep groups that include all of these facilities (``dkist``, ``iris``, ``eis``,
            ``solo``, ``rocket``).
        max_results : int, optional
            Most groups returned, earliest first (default 50).

        Returns
        -------
        dict
            ``range_utc``, ``total``, ``returned`` and ``groups`` (``start_utc``, ``hours``, the shared
            point ``x_arcsec`` and ``y_arcsec`` as seen from Earth, ``r_over_rsun``, ``facilities``,
            ``observations`` per instrument, ``first_id`` and a sky-view link).

        Examples
        --------
        >>> g = Observations().coordinated("2013-07-17", "2013-07-18", "eis,iris")
        >>> g["groups"][0]["facilities"]
        ['eis', 'iris']
        """
        jd0 = parse_time(start)
        jd1 = parse_time(end) if end is not None else jd0 + 365
        if jd1 < jd0:
            raise ValueError("end is before start")
        want = set()
        if facilities:
            for f in (facilities.split(",") if isinstance(facilities, str) else facilities):
                f = {"rockets": "rocket", "hinode": "eis"}.get(f.strip().lower(), f.strip().lower())
                if f not in FACILITIES:
                    raise ValueError(f"unknown facility {f!r}; use {', '.join(FACILITIES)}")
                want.add(f)
        data = self.store.json("data/obs/coordinated.json") or {"columns": [], "rows": []}
        cols = data["columns"]
        groups = []
        for row in data["rows"]:
            g = dict(zip(cols, row))
            t = parse_time(g["start"])
            if t > jd1 or t + g["hours"] / 24 < jd0:
                continue
            facs = g["facilities"].split("+")
            if not want <= set(facs):
                continue
            mid = g.get("open_mid") or g["start"]
            groups.append({"start_utc": iso(t), "hours": g["hours"], "x_arcsec": g["x"], "y_arcsec": g["y"],
                           "r_over_rsun": g["r_over_rsun"], "facilities": facs, "observations": g["observations"],
                           "first_id": g.get("open"),
                           "sky_view_link": sky_link(parse_time(mid), zoom=1.6)})
        return {"range_utc": [iso(jd0), iso(jd1)], "generated": data.get("generated"), "total": len(groups),
                "returned": min(len(groups), max_results), "groups": groups[:max_results],
                "note": "Use search_observations with the group's time and point for each observation's field, "
                        "archive link and SDO image cutouts."}
