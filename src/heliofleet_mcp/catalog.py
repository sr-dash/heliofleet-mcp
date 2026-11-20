"""Bodies HelioFleet draws, with the fields the geometry needs (from js/catalog.js)."""

SPACECRAFT = ["sdo", "soho", "aditya", "ace", "wind", "dscovr", "imap", "swfo", "cgo",
              "solo", "psp", "bepi", "sta", "stb", "maven"]
PLANETS = ["mercury", "venus", "mars"]
SKY_OBSERVERS = ["earth", "solo", "psp", "bepi", "sta", "stb", "maven"]

# geo: geocentric series; derived: heliocentric position = Earth + geocentric.
# fallback: shown at Earth past the end of its ephemeris.
BODIES = {
    "earth": {"name": "Earth", "kind": "planet", "hid": "399"},
    "sdo": {"name": "Solar Dynamics Observatory", "short": "SDO", "kind": "sc", "hid": "-136395",
            "launch": "2010-02-11T15:23Z", "near": True, "fallback": "earth"},
    "soho": {"name": "SOHO", "short": "SOHO", "kind": "sc", "hid": "-21", "launch": "1995-12-02T08:08Z",
             "near": True, "geo": "soho_geo", "derived": True},
    "aditya": {"name": "Aditya-L1", "short": "Aditya-L1", "kind": "sc", "hid": "-156",
               "launch": "2023-09-02T06:20Z", "near": True, "geo": "aditya_geo"},
    "ace": {"name": "Advanced Composition Explorer", "short": "ACE", "kind": "sc", "hid": "-92",
            "launch": "1997-08-25T14:39Z", "near": True, "geo": "ace_geo", "derived": True},
    "wind": {"name": "Wind", "short": "Wind", "kind": "sc", "hid": "-8", "launch": "1994-11-01T09:31Z",
             "near": True, "geo": "wind_geo", "derived": True},
    "dscovr": {"name": "Deep Space Climate Observatory", "short": "DSCOVR", "kind": "sc", "hid": "-78",
               "launch": "2015-02-11T23:03Z", "near": True, "geo": "dscovr_geo", "derived": True},
    "imap": {"name": "Interstellar Mapping and Acceleration Probe", "short": "IMAP", "kind": "sc",
             "hid": "-43", "launch": "2025-09-24T11:30Z", "near": True, "geo": "imap_geo", "derived": True},
    "swfo": {"name": "SOLAR-1 (SWFO-L1)", "short": "SOLAR-1", "kind": "sc", "hid": "-231",
             "launch": "2025-09-24T11:30Z", "near": True, "geo": "swfo_geo", "derived": True},
    "cgo": {"name": "Carruthers Geocorona Observatory", "short": "Carruthers", "kind": "sc", "hid": "-171",
            "launch": "2025-09-24T11:30Z", "near": True, "geo": "cgo_geo", "derived": True},
    "solo": {"name": "Solar Orbiter", "short": "Solar Orbiter", "kind": "sc", "hid": "-144",
             "launch": "2020-02-10T04:03Z"},
    "psp": {"name": "Parker Solar Probe", "short": "Parker", "kind": "sc", "hid": "-96",
            "launch": "2018-08-12T07:31Z"},
    "bepi": {"name": "BepiColombo", "short": "BepiColombo", "kind": "sc", "hid": "-121",
             "launch": "2018-10-20T01:45Z"},
    "sta": {"name": "STEREO-A", "short": "STEREO-A", "kind": "sc", "hid": "-234", "launch": "2006-10-26T00:52Z"},
    "stb": {"name": "STEREO-B", "short": "STEREO-B", "kind": "sc", "hid": "-235", "launch": "2006-10-26T00:52Z",
            "lost": "2014-10-01T00:00Z", "ended": "2018-10-17T00:00Z"},
    "maven": {"name": "MAVEN", "short": "MAVEN", "kind": "sc", "hid": "-202", "launch": "2013-11-18T18:28Z",
              "lost": "2025-12-06T00:00Z"},
    "mercury": {"name": "Mercury", "kind": "planet", "hid": "199"},
    "venus": {"name": "Venus", "kind": "planet", "hid": "299"},
    "mars": {"name": "Mars", "kind": "planet", "hid": "499"},
}

ALIASES = {
    "parker": "psp", "parker solar probe": "psp", "spp": "psp",
    "solar orbiter": "solo", "solarorbiter": "solo", "so": "solo",
    "stereo-a": "sta", "stereo a": "sta", "stereoa": "sta", "ahead": "sta",
    "stereo-b": "stb", "stereo b": "stb", "stereob": "stb", "behind": "stb",
    "bepicolombo": "bepi", "aditya-l1": "aditya", "aditya l1": "aditya",
    "solar-1": "swfo", "solar1": "swfo", "swfo-l1": "swfo", "carruthers": "cgo",
    "deep space climate observatory": "dscovr", "solar dynamics observatory": "sdo",
}


def resolve(name: str) -> str:
    """Body key from a key, short name or common alias (case-insensitive)."""
    k = name.strip().lower()
    if k in BODIES:
        return k
    if k in ALIASES:
        return ALIASES[k]
    for key, b in BODIES.items():
        if k in (b["name"].lower(), b.get("short", "").lower()):
            return key
    raise ValueError(f"unknown body {name!r}; known: {', '.join(BODIES)}")
