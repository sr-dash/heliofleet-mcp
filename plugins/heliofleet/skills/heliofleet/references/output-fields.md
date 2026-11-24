# heliofleet-mcp output fields

All distances are au unless the name says otherwise; angles are degrees; times are UTC.

## position, fleet (`bodies[]`)

| Field | Meaning |
| --- | --- |
| `r_au` | distance from Sun centre |
| `hgs_lon_deg`, `hgs_lat_deg` | Stonyhurst heliographic (HEEQ) longitude (west positive from the Sun–Earth line) and latitude |
| `carrington_lon_deg` | Carrington longitude as seen from Earth (Earth's light time, as SunPy `observer="earth"`) |
| `ecliptic_j2000_au` | heliocentric ecliptic J2000 vector (x toward the vernal equinox) |
| `hee_au` | Heliocentric Earth Ecliptic vector (x toward Earth, z ecliptic north) |
| `sep_from_earth_deg` | Sun-centred angle from Earth |
| `dist_to_earth_au` | distance to Earth |
| `light_time_s` | light travel time from Sun centre |
| `footpoint_hgs_lon_deg` | Stonyhurst longitude of the nominal Parker-spiral footpoint (default wind 400 km/s) |
| `status` | `ok`, `lost`, `approx`, `prelaunch`, `ended` or `nodata` |
| `link` | HelioFleet map at that moment |

`fleet` also lists `not_shown` (bodies without a position, with the reason).

## trajectory

`columns` names the entries of each `rows[]` list: `time_utc`, `status`, `r_au`, `hgs_lon_deg`,
`hgs_lat_deg`, `carrington_lon_deg`, `hee_x_au`, `hee_y_au`, `hee_z_au`, `sep_from_earth_deg`,
`dist_to_earth_au`, `light_time_s` and (not for planets) `footpoint_hgs_lon_deg`, as in `position`.
Rows outside the ephemeris keep `time_utc` and `status` with null coordinates. `extremes` gives the
closest and farthest points from the Sun and the closest approach to Earth among the samples; report
them at the sampling step. `link` opens the map with the orbit trail over the range.

## geometry (`observers[]`)

| Field | FITS keyword | Meaning |
| --- | --- | --- |
| `light_time_s` | | light travel time from Sun centre to the observer |
| `offset_vs_earth_s` | | light time minus Earth's; negative means the observer sees events earlier |
| `rsun_arcsec` | RSUN_OBS | apparent solar radius |
| `b0_deg` | HGLT_OBS | heliographic latitude of disk centre |
| `hgs_lon_deg` | HGLN_OBS | Stonyhurst longitude of disk centre |
| `l0_deg` | CRLN_OBS | Carrington longitude of disk centre, observer's own light time |
| `km_per_arcsec` | | size on the Sun of one arcsecond at disk centre |
| `scale_vs_earth` | | how much larger a disk-centre feature looks than from Earth |
| `sky_link` | | HelioFleet sky view from that observer |

## align (`windows[]`)

| Field | Meaning |
| --- | --- |
| `start_utc`, `end_utc` | first and last sample inside the tolerance |
| `duration_days` | `end - start` |
| `best_time_utc`, `best_value_deg` | sample with the smallest value: separation (radial, connection), offset from 90° (quadrature) or angle from Sun centre seen from Earth (conjunction) |
| `a_at_best`, `b_at_best` | `r_au`, Stonyhurst lon/lat of each body at the best time |
| `side` | quadrature only: west (ahead of Earth) or east (trailing) |
| `touches_range_edge` | the window may continue beyond the searched range |
| `link` | HelioFleet page that reruns the search at the best time |

Top level: `query`, `definition`, `step_hours` (1 with Parker, else 6), `samples`, `resolution_note`.

## observations (`observations[]`)

| Field | Meaning |
| --- | --- |
| `instrument`, `instrument_name`, `facility` | e.g. `iris`, `IRIS`, `iris`; facilities: dkist, iris, eis, solo, rocket |
| `id`, `description` | dataset or study identifier and programme description from the archive |
| `start_utc`, `end_utc` | time range (catalogue durations over a day are cut to a day) |
| `field_earth_view` | helioprojective arcsec seen from Earth: centre, width, height, closed polygon, `far_side` |
| `recorded_field` | Solar Orbiter only: the field as recorded from Solar Orbiter, with its position |
| `slit_jaw_field_earth_view` | IRIS only: the slit-jaw field |
| `data_link` | archive page of the dataset, where the source gives one |
| `sdo_images_png` | Helioviewer PNG cutouts (AIA 171, AIA 193, HMI) around the field at mid-time |
| `sky_view_link` | HelioFleet sky view at mid-time |

Top level: `total` (all matches) and `returned` (at most `--max`). `coordinated` returns `groups[]`
with `start_utc`, `hours`, the shared point `x_arcsec`, `y_arcsec`, `r_over_rsun`, `facilities`,
`observations` (count per instrument), `first_id` and `sky_view_link`.

## events (`events[]`)

`kind` (perihelion, alignment, quadrature, conjunction, eclipse), `time_utc`, `end_utc`, `title`,
`detail`, `bodies`, `values`, `link`. The calendar lists events from 30 days before its monthly build
to the end of the ephemerides; for past dates use `align`. With `--space-weather`, `space_weather`
adds DONKI flares (M1+), CMEs (500 km/s+) and storms (G1+).

## connection (`connections[]`)

| Field | Meaning |
| --- | --- |
| `wind_used_km_s` | wind speed of the spiral (nearest grid speed to `--wind`) |
| `source_surface_point_deg` | where the Parker spiral meets the source surface (Carrington lon/lat) |
| `footpoint_deg` | photospheric end of the PFSS field line from that point (Carrington lon/lat) |
| `expansion_factor_fs` | magnetic expansion factor between photosphere and source surface |
| `dchb_deg` | angular distance of the footpoint from the nearest coronal-hole boundary |
| `wsa_speed_km_s` | WSA-type wind-speed estimate (indicative) |

Top level: `date`, `daily_product`, `map_time_utc`, `model` (magnetogram, source-surface radius),
`carrington_rotation`, `earth_L0_deg`, `earth_B0_deg`, `caveat`, `links`. Without a daily product for
the date, the result has a `note` and `links` instead.

## spaceweather, field

`spaceweather`: one day's model wind speed and sector at Earth, next sector boundary, −1 to +7 day
outlook, alert level and the measured L1 wind, with `units`, `about`, `caveat` and `links`.

`field`: magnetogram, PFSS settings, `open_flux_Mx`, field-line count, Earth's L0/B0 and
`solar_cycle` (open flux and area, current-sheet tilt and polar fields of the nearest Carrington
rotation, available for any date since 2010).
