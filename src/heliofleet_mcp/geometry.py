"""Fleet positions, viewing geometry and alignment search on HelioFleet data.

Mirrors js/scene.js (positions and status), js/tools.js (coordinate and
viewing-geometry tables, alignment search) and scripts/build_calendar.py
(solar conjunctions), so the numbers match what the page shows.
"""

from __future__ import annotations

import math

from .catalog import BODIES, PLANETS, SKY_OBSERVERS, SPACECRAFT, resolve
from .data import Store
from .frames import (ARCSEC, AU_KM, C_KM_S, R_SUN_KM, angle_between, footpoint_lon, heliographic, norm,
                     sub, to_hee, wrap180)
from .links import map_link, sky_link
from .timeutil import date_str, iso, parse_time

ALIGN_KINDS = {
    "radial": {"needs_b": True, "tol": 5.0,
               "help": "Sun-centred angle between the two bodies within the tolerance."},
    "quadrature": {"needs_b": False, "tol": 5.0,
                   "help": "Body 90 deg from Earth as seen from the Sun, within the tolerance."},
    "conjunction": {"needs_b": False, "tol": 2.0,
                    "help": "Body behind the Sun as seen from Earth, within the tolerance of Sun centre."},
    "connection": {"needs_b": True, "tol": 10.0,
                   "help": "Parker-spiral footpoints of both bodies within the tolerance in longitude."},
}
MAX_RANGE_DAYS = 3660


def _r(v, d):
    return None if v is None else round(v, d)


class Fleet:
    def __init__(self, store: Store | None = None):
        self.store = store or Store()

    # ---------- positions (js/scene.js) ----------

    def earth(self, jd):
        return self.store.position("earth", jd)

    def helio(self, key, jd):
        b = BODIES[key]
        if not b.get("derived"):
            return self.store.position(key, jd)
        g = self.store.position(b["geo"], jd)
        e = self.store.position("earth", jd)
        if g is None or e is None:
            return None
        return (e[0] + g[0] / AU_KM, e[1] + g[1] / AU_KM, e[2] + g[2] / AU_KM)

    def status(self, key, jd, p):
        b = BODIES[key]
        if b.get("launch") and jd < parse_time(b["launch"]):
            return "prelaunch"
        if b.get("ended") and jd > parse_time(b["ended"]):
            return "ended"
        if p is None:
            return "approx" if b.get("fallback") else "nodata"
        if b.get("lost") and jd > parse_time(b["lost"]):
            return "lost"
        return "ok"

    def at(self, key, jd, earth=None):
        """(status, heliocentric position in au or None), with the map's fallbacks."""
        if earth is None:
            earth = self.earth(jd)
        if key == "earth":
            return ("ok", earth) if earth else ("nodata", None)
        if BODIES[key]["kind"] == "planet":
            p = self.store.position(key, jd)
            return ("ok", p) if p else ("nodata", None)
        p = self.helio(key, jd)
        st = self.status(key, jd, p)
        if st in ("prelaunch", "ended", "nodata"):
            return st, None
        return st, (earth if st == "approx" else p)

    # ---------- coordinate rows (js/tools.js row) ----------

    def body_row(self, key, jd, earth, wind=400.0):
        st, p = self.at(key, jd, earth)
        out = {"body": key, "name": BODIES[key]["name"], "time_utc": iso(jd), "status": st}
        if p is None:
            return out
        g = heliographic(p, earth, jd)
        is_earth = key == "earth"
        planet = BODIES[key]["kind"] == "planet" and not is_earth
        h = to_hee(p, earth)
        out.update({
            "r_au": _r(g["dist"], 6),
            "hgs_lon_deg": _r(g["lon"], 4),
            "hgs_lat_deg": _r(g["lat"], 4),
            "carrington_lon_deg": _r(g["carr"], 4),
            "ecliptic_j2000_au": [_r(v, 8) for v in p],
            "hee_au": [_r(v, 8) for v in h],
            "sep_from_earth_deg": 0.0 if is_earth else _r(angle_between(p, earth), 4),
            "dist_to_earth_au": 0.0 if is_earth else _r(norm(sub(p, earth)), 6),
            "light_time_s": _r(g["dist"] * AU_KM / C_KM_S, 2),
        })
        if not planet:
            out["footpoint_hgs_lon_deg"] = _r(footpoint_lon(g["lon"], g["dist"], wind), 3)
        return out

    def position(self, body, time=None, wind=400.0):
        key = resolve(body)
        jd = parse_time(time)
        earth = self._earth_or_raise(jd)
        row = self.body_row(key, jd, earth, wind)
        if "r_au" not in row:
            row["note"] = _status_note(row["status"], key, self.store)
        if row["status"] == "approx":
            row["note"] = "Past the end of its ephemeris; shown at Earth's position as on the map."
        row["link"] = map_link(jd, wind=wind if wind != 400 else None)
        return row

    def fleet_state(self, time=None, include_planets=True, wind=400.0):
        jd = parse_time(time)
        earth = self._earth_or_raise(jd)
        keys = ["earth", *SPACECRAFT, *(PLANETS if include_planets else [])]
        rows, missing = [], []
        for k in keys:
            row = self.body_row(k, jd, earth, wind)
            if "r_au" in row:
                rows.append(row)
            else:
                missing.append({"body": k, "status": row["status"]})
        return {
            "time_utc": iso(jd),
            "frame_notes": FRAME_NOTES,
            "solar_wind_km_s": wind,
            "bodies": rows,
            "not_shown": missing,
            "link": map_link(jd, wind=wind if wind != 400 else None, planets=include_planets),
            "data": self.data_info(),
        }

    # ---------- viewing geometry (js/tools.js geometryRows) ----------

    def viewing_geometry(self, observer="all", time=None):
        jd = parse_time(time)
        e = self._earth_or_raise(jd)
        d_e = norm(e)
        if observer in (None, "", "all"):
            keys = ["earth", *SPACECRAFT]
        else:
            keys = [resolve(observer)]
            if BODIES[keys[0]]["kind"] == "planet" and keys[0] != "earth":
                raise ValueError("viewing geometry is for Earth and spacecraft")
        rows = []
        for k in keys:
            st, p = self.at(k, jd, e)
            if p is None:
                if len(keys) == 1:
                    raise ValueError(f"{k}: {_status_note(st, k, self.store)}")
                continue
            g = heliographic(p, e, jd, norm(p))
            km = g["dist"] * AU_KM
            row = {
                "body": k, "name": BODIES[k]["name"], "time_utc": iso(jd), "status": st,
                "r_au": _r(g["dist"], 6),
                "light_time_s": _r(km / C_KM_S, 2),
                "offset_vs_earth_s": _r((g["dist"] - d_e) * AU_KM / C_KM_S, 2),
                "rsun_arcsec": _r(math.asin(R_SUN_KM / km) / ARCSEC, 2),
                "b0_deg": _r(g["lat"], 4),
                "hgs_lon_deg": _r(g["lon"], 4),
                "l0_deg": _r(g["carr"], 4),
                "km_per_arcsec": _r((km - R_SUN_KM) * math.tan(ARCSEC), 2),
                "scale_vs_earth": _r((d_e * AU_KM - R_SUN_KM) / (km - R_SUN_KM), 4),
            }
            if k in SKY_OBSERVERS:
                row["sky_link"] = sky_link(jd, k)
            rows.append(row)
        return {
            "time_utc": iso(jd),
            "columns": GEOMETRY_COLUMNS,
            "observers": rows,
            "link": map_link(jd, tab="geom"),
        }

    # ---------- alignment search (js/tools.js findAlignments) ----------

    def find_alignments(self, kind="radial", a="psp", b=None, tolerance_deg=None, start=None, end=None,
                        wind=400.0, max_windows=None, step_hours=None):
        kind = kind.lower()
        if kind not in ALIGN_KINDS:
            raise ValueError(f"kind must be one of {', '.join(ALIGN_KINDS)}")
        spec = ALIGN_KINDS[kind]
        ka = resolve(a)
        kb = resolve(b) if (spec["needs_b"] and b) else ("earth" if spec["needs_b"] else None)
        if spec["needs_b"] and ka == kb:
            raise ValueError("a and b must differ")
        if kind in ("quadrature", "conjunction") and ka == "earth":
            raise ValueError(f"{kind} needs a body other than Earth")
        tol = float(tolerance_deg) if tolerance_deg is not None else spec["tol"]
        m = self.store.manifest()
        jd0 = parse_time(start)
        jd1 = parse_time(end) if end is not None else min(jd0 + 365, m["timeline"]["end"])
        if jd1 <= jd0:
            raise ValueError("end must be after start")
        if jd1 - jd0 > MAX_RANGE_DAYS:
            raise ValueError(f"range is limited to {MAX_RANGE_DAYS} days")
        bodies = [ka] + ([kb] if spec["needs_b"] else [])
        step = (step_hours / 24) if step_hours else (1 / 24 if "psp" in bodies else 0.25)

        def metric(t):
            earth = self.earth(t)
            if earth is None:
                return None
            pa = self.at(ka, t, earth)[1]
            if pa is None:
                return None
            if kind == "quadrature":
                return abs(angle_between(pa, earth) - 90)
            if kind == "conjunction":
                to_sun = tuple(-c for c in earth)
                to_sc = sub(pa, earth)
                return angle_between(to_sun, to_sc) if norm(to_sc) > norm(earth) else None
            pb = self.at(kb, t, earth)[1]
            if pb is None:
                return None
            if kind == "radial":
                return angle_between(pa, pb)
            ga, gb = heliographic(pa, earth, t), heliographic(pb, earth, t)
            return abs(wrap180(footpoint_lon(ga["lon"], ga["dist"], wind) - footpoint_lon(gb["lon"], gb["dist"], wind)))

        windows, cur, samples = [], None, 0
        n = int((jd1 - jd0) / step + 1e-9) + 1
        for i in range(n):
            t = jd0 + i * step
            v = metric(t)
            if v is not None:
                samples += 1
            if v is not None and v <= tol:
                if cur is None:
                    cur = {"start": t, "end": t, "best": t, "value": v}
                cur["end"] = t
                if v < cur["value"]:
                    cur["best"], cur["value"] = t, v
            elif cur is not None:
                windows.append(cur)
                cur = None
                if max_windows and len(windows) >= max_windows:
                    break
        if cur is not None and not (max_windows and len(windows) >= max_windows):
            windows.append(cur)

        align_q = {"kind": kind, "a": ka, "b": kb or "earth", "tol": tol, "from": date_str(jd0), "to": date_str(jd1)}
        out_windows = []
        for w in windows:
            e = self.earth(w["best"])
            pa = self.at(ka, w["best"], e)[1]
            ga = heliographic(pa, e, w["best"])
            item = {
                "start_utc": iso(w["start"]), "end_utc": iso(w["end"]),
                "duration_days": round(w["end"] - w["start"], 3),
                "best_time_utc": iso(w["best"]), "best_value_deg": round(w["value"], 3),
                "a_at_best": {"body": ka, "r_au": _r(ga["dist"], 4), "hgs_lon_deg": _r(ga["lon"], 3),
                              "hgs_lat_deg": _r(ga["lat"], 3)},
                "touches_range_edge": w["start"] <= jd0 + 1e-9 or w["end"] >= jd0 + (n - 1) * step - 1e-9,
            }
            if kb and spec["needs_b"]:
                pb = self.at(kb, w["best"], e)[1]
                gb = heliographic(pb, e, w["best"])
                item["b_at_best"] = {"body": kb, "r_au": _r(gb["dist"], 4), "hgs_lon_deg": _r(gb["lon"], 3),
                                     "hgs_lat_deg": _r(gb["lat"], 3)}
            if kind == "quadrature":
                ahead = (-e[1] * pa[0] + e[0] * pa[1]) > 0
                item["side"] = "west, ahead of Earth" if ahead else "east, trailing Earth"
            item["link"] = map_link(w["best"], align=align_q, wind=wind if kind == "connection" else None)
            out_windows.append(item)

        res = {
            "query": {"kind": kind, "a": ka, "b": kb if spec["needs_b"] else None, "tolerance_deg": tol,
                      "start_utc": iso(jd0), "end_utc": iso(jd1),
                      **({"solar_wind_km_s": wind} if kind == "connection" else {})},
            "definition": spec["help"],
            "step_hours": round(step * 24, 3),
            "samples": samples,
            "windows": out_windows,
            "best_value_meaning": "smallest separation (radial, connection), offset from 90 deg (quadrature) "
                                  "or angle from Sun centre seen from Earth (conjunction) in the window",
            "resolution_note": f"Window edges and best times are at the {step * 24:g}-hour sample grid, as on the page.",
            "link": map_link(jd0, align=align_q, wind=wind if kind == "connection" else None),
        }
        if max_windows:
            res["query"]["max_windows"] = max_windows
        if samples == 0:
            res["note"] = "No ephemeris covers these bodies in this range."
        return res

    # ---------- events ----------

    def upcoming_events(self, start=None, end=None, kind=None, body=None, include_space_weather=False):
        jd0 = parse_time(start)
        jd1 = parse_time(end) if end is not None else jd0 + 365
        up = self.store.json("data/upcoming.json") or {"events": []}
        keyb = resolve(body) if body else None
        kinds = {k.strip().lower() for k in kind.split(",")} if kind else None
        out = []
        for ev in up["events"]:
            t_end = ev.get("end") or ev["t"]
            if t_end < jd0 or ev["t"] > jd1:
                continue
            if kinds and ev["kind"] not in kinds:
                continue
            if keyb and keyb not in ev.get("bodies", []):
                continue
            out.append({
                "kind": ev["kind"], "time_utc": iso(ev["t"]),
                "end_utc": iso(ev["end"]) if ev.get("end") else None,
                "title": ev["title"], "detail": ev["detail"], "bodies": ev.get("bodies", []),
                "values": ev.get("v"), "link": map_link(ev["t"]),
            })
        res = {
            "range_utc": [iso(jd0), iso(jd1)],
            "generated": up.get("generated"),
            "events": out,
            "coverage_note": "The calendar lists events from 30 days before its build date to the end of the "
                             "ephemerides (perihelia of Parker and Solar Orbiter; alignments within 3 deg; "
                             "quadratures within 1 deg; conjunctions within 2 deg; total eclipses). "
                             "Use find_alignments for other pairs, tolerances or past dates.",
            "calendar_ics": "https://sr-dash.github.io/heliofleet/calendar.ics",
        }
        if include_space_weather:
            ev = self.store.json("data/events.json") or {}
            sw = []
            for group in ("flares", "cmes", "storms"):
                for e in ev.get(group, []):
                    t = parse_time(e["t"])
                    if jd0 <= t <= jd1:
                        sw.append({"type": group[:-1], **e, "heliofleet_link": map_link(t)})
            res["space_weather"] = {"source": ev.get("source"), "criteria": ev.get("criteria"), "events": sw}
        return res

    # ---------- links and status ----------

    def link(self, time=None, page="map", *, tab=None, observer="earth", frame=None, view=None, zoom=None,
             hide=None, spirals=None, solar_wind_km_s=None, spot_system=None, spot_lon=None, spot_lat=None,
             align_kind=None, align_a=None, align_b=None, align_tolerance_deg=None, align_from=None,
             align_to=None):
        """A HelioFleet map or sky-view URL that reproduces a view."""
        jd = parse_time(time)
        if page == "sky":
            return {"link": sky_link(jd, resolve(observer), zoom=zoom)}
        if page != "map":
            raise ValueError("page must be map or sky")
        spot = None
        if spot_system and spot_lon is not None and spot_lat is not None:
            spot = {"sys": spot_system, "lon": spot_lon, "lat": spot_lat}
            tab = tab or "vis"
        align = None
        if align_kind:
            if not (align_a and align_from and align_to):
                raise ValueError("an alignment link needs align_a, align_from and align_to")
            align = {"kind": align_kind, "a": resolve(align_a), "b": resolve(align_b) if align_b else "earth",
                     "tol": align_tolerance_deg or ALIGN_KINDS[align_kind]["tol"],
                     "from": date_str(parse_time(align_from)), "to": date_str(parse_time(align_to))}
        url = map_link(jd, tab=tab, align=align, spot=spot, frame=frame, view=view, zoom=zoom,
                       hide=[resolve(h) for h in hide] if hide else None, spirals=spirals, wind=solar_wind_km_s)
        return {"link": url}

    def data_status(self):
        """Loaded data release, where it came from, and each body's ephemeris span."""
        m = self.store.manifest()
        return {**self.data_info(),
                "bodies": {k: {"start_utc": iso(v["start"]), "end_utc": iso(v["end"]), "step_days": v["step"],
                               "units": v["units"], "center": v["center"]} for k, v in m["bodies"].items()},
                "link": "https://sr-dash.github.io/heliofleet/methods.html"}

    # ---------- misc ----------

    def data_info(self):
        m = self.store.manifest()
        return {"generated": m.get("generated"), "next_update": m.get("next_update"),
                "source": m.get("source"), "loaded_from": self.store.origin}

    def _earth_or_raise(self, jd):
        e = self.earth(jd)
        if e is None:
            m = self.store.manifest()["timeline"]
            raise ValueError(f"time outside the ephemerides ({iso(m['start'])} to {iso(m['end'])})")
        return e


def _status_note(st, key, store):
    info = store.info(BODIES[key].get("geo") if BODIES[key].get("derived") else key) or {}
    span = f" (data {iso(info['start'])} to {iso(info['end'])})" if info else ""
    return {
        "prelaunch": "Not launched yet at this time.",
        "ended": "Mission ended before this time.",
        "nodata": f"No ephemeris at this time{span}.",
    }.get(st, st)


FRAME_NOTES = {
    "ecliptic_j2000_au": "heliocentric ICRF ecliptic J2000 (x toward the vernal equinox), au",
    "hee_au": "Heliocentric Earth Ecliptic (x toward Earth, z ecliptic north), au",
    "hgs_lon_deg / hgs_lat_deg": "Stonyhurst heliographic (HEEQ), longitude west positive from the Sun-Earth line",
    "carrington_lon_deg": "Carrington longitude as seen from Earth (one Sun-Earth light time in the past), "
                          "as SunPy HeliographicCarrington(observer='earth')",
    "footpoint_hgs_lon_deg": "Stonyhurst longitude of the nominal Parker-spiral footpoint at the given wind speed",
    "status": "ok, lost (prediction after loss of contact) or approx (shown at Earth)",
}

GEOMETRY_COLUMNS = {
    "light_time_s": "light travel time from Sun centre to the observer (s)",
    "offset_vs_earth_s": "light time minus Earth's (s); negative means it sees solar events earlier than Earth",
    "rsun_arcsec": "apparent solar radius (arcsec), as RSUN_OBS",
    "b0_deg": "heliographic latitude of the disk centre, as HGLT_OBS",
    "hgs_lon_deg": "Stonyhurst longitude of the disk centre, as HGLN_OBS",
    "l0_deg": "Carrington longitude of the disk centre with the observer's own light time, as CRLN_OBS",
    "km_per_arcsec": "size on the Sun of one arcsecond at disk centre (km)",
    "scale_vs_earth": "how much larger a disk-centre feature looks than from Earth",
}
