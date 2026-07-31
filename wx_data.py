#!/usr/bin/env python3
"""
Lightweight wx-web data exporter.

Fetches only what the wx-web viewer actually consumes — VAAC advisories,
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

from src.config import ROUTES
from src.fetchers.noaa import fetch_all, fetch_windtemp_alaska
from src.fetchers.vaac import (
    fetch_tokyo_vaac,
    fetch_alaska_vaac,
    fetch_tokyo_vaac_active,
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


def export() -> str:
    now = datetime.now(timezone.utc)
    log.info("=== wx-data (lightweight) started  %s UTC ===",
             now.strftime("%Y-%m-%d %H:%M"))

    weather      = fetch_all(ROUTES)
    windtemp_raw = fetch_windtemp_alaska()
    tokyo_vaac   = fetch_tokyo_vaac()
    alaska_vaac  = fetch_alaska_vaac()
    tokyo_active = fetch_tokyo_vaac_active()

    out: dict = {
        "updated_utc": now.strftime("%Y-%m-%dT%H:%MZ"),
        "metar": {},
        "taf": {},
        "atis": {},   # ATIS needs Playwright; refreshed by the heavy workflow
        "windtemp_alaska": windtemp_raw,
        "vaac_active": tokyo_active,   # red-triangle volcanoes from indexj.html TOP
        "vaac_tokyo":  [_vaac_entry(e) for e in (tokyo_vaac  or [])],
        "vaac_alaska": [_vaac_entry(e) for e in (alaska_vaac or [])],
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

    log.info("wx-data written: %s  (%d METAR, %d TAF, VAAC active=%d tokyo=%d alaska=%d)",
             OUT_PATH, len(out["metar"]), len(out["taf"]),
             len(out["vaac_active"]), len(out["vaac_tokyo"]), len(out["vaac_alaska"]))
    return OUT_PATH


if __name__ == "__main__":
    export()
