"""HelioFleet page links that reproduce a view (parameters as in js/app.js and js/sky.js)."""

from __future__ import annotations

from urllib.parse import urlencode

from .timeutil import iso_minute

SITE = "https://sr-dash.github.io/heliofleet/"
TABS = ("coords", "geom", "align", "vis", "series", "anim")
PAGE_KINDS = ("radial", "quadrature", "connection")  # kinds the page's alignment tool knows


def _clean(v):
    if isinstance(v, (list, tuple, set)):
        return ",".join(str(x) for x in v)
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def map_link(jd: float, *, tab: str | None = None, align: dict | None = None, spot: dict | None = None,
             frame: str | None = None, view: str | None = None, zoom: float | None = None,
             trail: float | None = None, wind: float | None = None, planets: bool | None = None,
             spirals: bool | None = None, hide=None, fov=None, cme: bool | None = None,
             lang: str | None = None, theme: str | None = None, section: str | None = None,
             site: str = SITE) -> str:
    """Link to the HelioFleet map.

    align: {kind, a, b, tol, from, to} with dates YYYY-MM-DD (the page reruns it).
    spot: {sys: 'c'|'s', lon, lat} (Carrington or Stonyhurst degrees).
    """
    q: dict[str, str] = {"t": f"{iso_minute(jd)}Z"}
    if frame and frame != "hee":
        q["frame"] = frame
    if view and view != "top":
        q["view"] = view
    if zoom is not None:
        q["zoom"] = _clean(float(zoom))
    if trail is not None:
        q["trail"] = _clean(trail)
    if planets is False:
        q["planets"] = "0"
    if spirals:
        q["spirals"] = "1"
    if wind is not None and float(wind) != 400:
        q["wind"] = _clean(wind)
    if hide:
        q["hide"] = _clean(hide)
    if cme is False:
        q["cme"] = "0"
    if fov:
        q["fov"] = _clean(fov)
    for k, v in (("theme", theme), ("lang", lang)):
        if v:
            q[k] = v
    if spot:
        q["spot"] = ",".join([spot["sys"][0], _clean(float(spot["lon"])), _clean(float(spot["lat"]))])
    if align and align.get("kind") in PAGE_KINDS:
        tab = "align"
        q["align"] = ",".join([align["kind"], align["a"], align.get("b") or "earth", _clean(float(align["tol"])),
                               align["from"], align["to"]])
    if tab and tab != "coords":
        if tab not in TABS:
            raise ValueError(f"tab must be one of {TABS}")
        q["tab"] = tab
    if tab and not section:
        section = "tools"
    url = site + "?" + urlencode(q, safe=",:")
    return url + (f"#{section}" if section else "")


def sky_link(jd: float, observer: str = "earth", *, zoom: float | None = None, fov=None, img: str | None = None,
             lang: str | None = None, site: str = SITE) -> str:
    """Link to the sky view (plane of the sky seen from Earth or a spacecraft)."""
    q: dict[str, str] = {"t": f"{iso_minute(jd)}Z"}
    if observer != "earth":
        q["obs"] = observer
    if zoom is not None:
        q["zoom"] = _clean(float(zoom))
    if fov:
        q["fov"] = _clean(fov)
    if img:
        q["img"] = img
    if lang:
        q["lang"] = lang
    return site + "sky.html?" + urlencode(q, safe=",:")
