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
    """Link to the HelioFleet map that reproduces a view.

    Parameters left at None (or at the page's default) are omitted from the URL.

    Parameters
    ----------
    jd : float
        Moment shown (Julian date, UT), written as ``t=`` to the minute.
    tab : str, optional
        Research tab under the map: ``coords``, ``geom``, ``align``, ``vis``, ``series`` or ``anim``.
    align : dict, optional
        Alignment search the page reruns on opening: ``{"kind", "a", "b", "tol", "from", "to"}`` with
        dates as ``YYYY-MM-DD``. Only the kinds the page knows (radial, quadrature, connection) are linked.
    spot : dict, optional
        Marked surface point ``{"sys": "c" or "s", "lon", "lat"}`` (Carrington or Stonyhurst degrees).
    frame : str, optional
        ``hee`` (Earth-fixed, default) or ``hae`` (inertial).
    view : str, optional
        ``top`` (default) or ``side``.
    zoom : float, optional
        Map zoom (au).
    trail : float, optional
        Trail length (days).
    wind : float, optional
        Solar-wind speed for the Parker spirals (km/s); 400 is the default and is omitted.
    planets, spirals, cme : bool, optional
        Show planets (``False`` hides them), Parker spirals (``True``) and CME fronts (``False`` hides them).
    hide, fov : sequence of str, optional
        Body keys to hide, and instrument fields of view to draw.
    lang, theme : str, optional
        Interface language (``en``, ``hi``, ``es``) and colour theme.
    section : str, optional
        Page section to open (``map``, ``coverage``, ``tools``); ``tools`` when a tab is set.
    site : str, optional
        Site root, for a mirror or a local copy.

    Returns
    -------
    str
        The URL.

    Raises
    ------
    ValueError
        For an unknown tab.

    Examples
    --------
    >>> map_link(2451545.0)
    'https://sr-dash.github.io/heliofleet/?t=2000-01-01T12:00Z'
    >>> map_link(2451545.0, tab="geom")
    'https://sr-dash.github.io/heliofleet/?t=2000-01-01T12:00Z&tab=geom#tools'
    >>> url = map_link(2460676.5, align={"kind": "radial", "a": "solo", "b": "psp", "tol": 5,
    ...                                  "from": "2025-01-01", "to": "2025-12-31"})
    >>> url.split("?")[1]
    't=2025-01-01T00:00Z&align=radial,solo,psp,5,2025-01-01,2025-12-31&tab=align#tools'
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
    """Link to HelioFleet's sky view: the plane of the sky seen from Earth or a spacecraft.

    Parameters
    ----------
    jd : float
        Moment shown (Julian date, UT).
    observer : str, optional
        ``earth`` (default), ``solo``, ``psp``, ``bepi``, ``sta``, ``stb`` or ``maven``.
    zoom : float, optional
        Field of view (solar radii).
    fov : sequence of str, optional
        Instrument fields of view to draw.
    img : str, optional
        SDO image under the observations: ``aia171``, ``aia193`` or ``hmi``.
    lang : str, optional
        Interface language (``en``, ``hi``, ``es``).
    site : str, optional
        Site root, for a mirror or a local copy.

    Returns
    -------
    str
        The URL.

    Examples
    --------
    >>> sky_link(2451545.0, "solo", zoom=10)
    'https://sr-dash.github.io/heliofleet/sky.html?t=2000-01-01T12:00Z&obs=solo&zoom=10'
    """
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
