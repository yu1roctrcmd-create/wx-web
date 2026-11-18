#!/usr/bin/env python3
"""
Lightweight wx-web data exporter.

Fetches only what the wx-web viewer actually consumes — VAAC advisories
(Tokyo/Alaska/London/Toulouse),
FD wind/temp (Alaska) and METAR/TAF — and writes /tmp/metar_latest.json.

No Playwright / Chromium / PDF / email. Designed to run every 30 min so the
VAAC panel stays fresh even when the heavy briefing workflow is throttled by
GitHub's scheduler.

Usage:
    python wx_data.py
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

import requests

from src.config import ROUTES
from src.fetchers.noaa import fetch_all, fetch_windtemp_alaska
from src.fetchers.vaac import (
    fetch_tokyo_vaac,
    fetch_alaska_vaac,
    fetch_tokyo_vaac_active,
    fetch_london_vaac,
    fetch_toulouse_vaac,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

OUT_PATH = "/tmp/metar_latest.json"


def _vaac_entry(e: dict) -> dict:
    # Drop the non-serialisable PIL Image object.
    return {k: v for k, v in e.items() if k != "image"}


_AWC = "https://aviationweather.gov/api/data"


def fetch_ice_sigmets() -> list[dict]:
    """Icing SIGMETs worldwide (international + US domestic) normalised for the viewer.

    The AWC JSON API has no CORS, so it must be fetched here. Altitudes are in feet.
    """
    out: list[dict] = []
    for ep, hz in (("isigmet", "ice"), ("airsigmet", "ice")):
        try:
            r = requests.get(f"{_AWC}/{ep}", params={"format": "json", "hazard": hz},
                             headers={"User-Agent": "WeatherBriefingBot/1.0"}, timeout=30)
            r.raise_for_status()
            rows = r.json() if r.text.strip() else []
        except Exception as exc:  # noqa: BLE001
            log.warning("%s fetch failed: %s", ep, exc)
            continue
        for e in rows or []:
            if str(e.get("hazard", "")).upper() != "ICE":
                continue
            coords = e.get("coords") or []
            if not isinstance(coords, list) or len(coords) < 3:
                continue
            base = e.get("base", e.get("altitudeLow1"))
            top = e.get("top", e.get("altitudeHi1", e.get("altitudeHi2")))
            def _ts(v):
                if isinstance(v, (int, float)): return int(v)
                try: return int(datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp())
                except Exception: return None
            out.append({
                "id": f"{e.get('firName') or e.get('icaoId') or ep} {e.get('seriesId') or e.get('alphaChar') or ''}".strip(),
                "src": ep,
                "qual": e.get("qualifier") or ("SEV" if str(e.get("severity", "")) in ("4", "5") else ""),
                "base": base, "top": top,
                "from": _ts(e.get("validTimeFrom")), "to": _ts(e.get("validTimeTo")),
                "dir": e.get("dir"), "spd": e.get("spd"),
                "coords": [[c["lat"], c["lon"]] for c in coords if "lat" in c and "lon" in c],
                "raw": (e.get("rawSigmet") or e.get("rawAirSigmet") or "")[:700],
            })
    log.info("ICE SIGMET: %d", len(out))
    return out


def export() -> str:
    now = datetime.now(timezone.utc)
    log.info("=== wx-data (lightweight) started  %s UTC ===",
             now.strftime("%Y-%m-%d %H:%M"))

    weather      = fetch_all(ROUTES)
    windtemp_raw = fetch_windtemp_alaska()
    tokyo_vaac   = fetch_tokyo_vaac()
    alaska_vaac  = fetch_alaska_vaac()
    tokyo_active = fetch_tokyo_vaac_active()
    london_vaac  = fetch_london_vaac()
    tls_vaac     = fetch_toulouse_vaac()
    ice_sigmets  = fetch_ice_sigmets()

    out: dict = {
        "updated_utc": now.strftime("%Y-%m-%dT%H:%MZ"),
        "metar": {},
        "taf": {},
        "atis": {},   # ATIS needs Playwright; refreshed by the heavy workflow
        "windtemp_alaska": windtemp_raw,
        "ice_sigmets": ice_sigmets,
        "vaac_active": tokyo_active,   # red-triangle volcanoes from indexj.html TOP
        "vaac_tokyo":  [_vaac_entry(e) for e in (tokyo_vaac  or [])],
        "vaac_alaska": [_vaac_entry(e) for e in (alaska_vaac or [])],
        "vaac_london":   london_vaac or [],     # Met Office (primary source)
        "vaac_toulouse": tls_vaac or [],        # Meteo-France (primary source)
    }
    for route_data in weather.get("routes", {}).values():
        for icao, m in route_data.get("metars", {}).items():
            if m and icao not in out["metar"]:
                out["metar"][icao] = m.get("rawOb") or m.get("rawObservation") or ""
        for icao, t in route_data.get("tafs", {}).items():
            if t and icao not in out["taf"]:
                out["taf"][icao] = t.get("rawTAF") or ""

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    log.info("wx-data written: %s  (%d METAR, %d TAF, VAAC active=%d tokyo=%d alaska=%d london=%d toulouse=%d)",
             OUT_PATH, len(out["metar"]), len(out["taf"]),
             len(out["vaac_active"]), len(out["vaac_tokyo"]), len(out["vaac_alaska"]),
             len(out["vaac_london"]), len(out["vaac_toulouse"]))
    return OUT_PATH


if __name__ == "__main__":
    export()
