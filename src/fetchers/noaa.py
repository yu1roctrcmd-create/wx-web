"""
Fetches METAR, TAF, SIGMET, PIREP from NOAA Aviation Weather Center API.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import requests

from src.config import ALL_AIRPORTS, ALL_FIRS, NOAA_API_BASE, METAR_HOURS, PIREP_HOURS

log = logging.getLogger(__name__)

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "WeatherBriefingBot/1.0"})
_TIMEOUT = 30


# ── helpers ───────────────────────────────────────────────────────────────────

def _get(endpoint: str, params: dict) -> list | dict:
    url = f"{NOAA_API_BASE}/{endpoint}"
    try:
        r = _SESSION.get(url, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        log.warning("NOAA fetch failed [%s]: %s", endpoint, exc)
        return []


# ── public API ────────────────────────────────────────────────────────────────

def fetch_metars(airports: list[str] | None = None) -> list[dict]:
    """Return list of latest METAR dicts for given airports."""
    ids = ",".join(airports or ALL_AIRPORTS)
    data = _get("metar", {"ids": ids, "format": "json", "hours": METAR_HOURS})
    return data if isinstance(data, list) else []


def fetch_tafs(airports: list[str] | None = None) -> list[dict]:
    """Return list of TAF dicts."""
    ids = ",".join(airports or ALL_AIRPORTS)
    data = _get("taf", {"ids": ids, "format": "json"})
    return data if isinstance(data, list) else []


def fetch_sigmets(firs: set[str] | None = None) -> list[dict]:
    """Return international SIGMETs, optionally filtered to relevant FIRs."""
    data = _get("isigmet", {"format": "json"})
    if not isinstance(data, list):
        return []

    filter_firs = firs or ALL_FIRS
    filtered = []
    for s in data:
        fir_id = (s.get("firId") or "").upper()
        # Keep if FIR matches, or if rawSigmet mentions a relevant FIR
        raw = (s.get("rawSigmet") or "").upper()
        if fir_id in filter_firs or any(f in raw for f in filter_firs):
            filtered.append(s)

    # Sort by hazard type for readability
    return sorted(filtered, key=lambda x: x.get("hazard", ""))


def fetch_windtemp_alaska() -> str:
    """Fetch FD wind/temp aloft for Alaska (6-hour forecast). Returns raw FD text."""
    url = f"{NOAA_API_BASE}/windtemp"
    params = {"region": "alaska", "fcst": "6", "level": "low"}
    try:
        r = _SESSION.get(url, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception as exc:
        log.warning("Wind/temp fetch failed [alaska]: %s", exc)
        return ""


def fetch_pireps() -> list[dict]:
    """Return PIREPs for East Asia / North Pacific bounding box."""
    # Broad box covering all 5 routes: Japan → SE Asia, Japan → Alaska
    bbox = "0,100,70,180"
    data = _get("pirep", {"bbox": bbox, "format": "json", "hours": PIREP_HOURS})
    return data if isinstance(data, list) else []


def fetch_all(routes: dict) -> dict:
    """Fetch everything needed for the briefing and return as a single dict."""
    log.info("Fetching METAR/TAF/SIGMET/PIREP…")

    metars_raw = fetch_metars()
    tafs_raw = fetch_tafs()
    sigmets = fetch_sigmets()
    pireps = fetch_pireps()

    # Index by ICAO for easy lookup
    metars: dict[str, dict] = {m["icaoId"]: m for m in metars_raw if "icaoId" in m}
    tafs:   dict[str, dict] = {t["icaoId"]: t for t in tafs_raw  if "icaoId" in t}

    # Attach per-route SIGMET list
    route_data: dict[str, dict] = {}
    for key, route in routes.items():
        firs = set(route["firs"])
        route_sigmets = [
            s for s in sigmets
            if (s.get("firId") or "").upper() in firs
        ]
        airports = [route["departure"], route["destination"]] + route["alternates"]
        route_data[key] = {
            "name":     route["name"],
            "airports": airports,
            "metars":   {ap: metars.get(ap) for ap in airports},
            "tafs":     {ap: tafs.get(ap)   for ap in airports},
            "sigmets":  route_sigmets,
        }

    return {
        "generated_at": datetime.now(timezone.utc),
        "routes":       route_data,
        "all_sigmets":  sigmets,
        "pireps":       pireps,
    }
