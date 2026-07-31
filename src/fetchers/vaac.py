"""
Fetches Volcanic Ash Advisory (VAA) / VAGFN graphics from:
  - Tokyo  VAAC (JMA):       https://ds.data.jma.go.jp/svd/vaac/data/vaac_list.html
  - Alaska VAAC (NOAA/AAWU): https://api.weather.gov/products/types/VAA

Image URL resolution:
  Tokyo : opennarro() onclick links  → VAGFN/YYYY/Images/{id}_QH21_01.png
  Alaska: WMO header NN              → fcstgraphics/PFXD{NN}PAWU.png  (static current)
"""
from __future__ import annotations

import logging
import re
from io import BytesIO
from typing import Optional

import requests
from PIL import Image as PILImage

log = logging.getLogger(__name__)

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "WeatherBriefingBot/1.0"})
_TIMEOUT = 30

_TOKYO_BASE     = "https://ds.data.jma.go.jp/svd/vaac/data"
_TOKYO_LIST_URL = f"{_TOKYO_BASE}/vaac_list.html"
_TOKYO_TXT_BASE = f"{_TOKYO_BASE}/TextData"
_TOKYO_IMG_BASE = f"{_TOKYO_BASE}/VAGFN"

_ALASKA_VAA_API     = "https://api.weather.gov/products/types/VAA"
_ALASKA_STATIC_TMPL = "https://www.weather.gov/images/aawu/fcstgraphics/PFXD{NN}PAWU.png"


# ── helpers ───────────────────────────────────────────────────────────────────

def _fetch_image(url: str) -> Optional[PILImage.Image]:
    """Download image; return RGB PIL Image or None on any error."""
    try:
        r = _SESSION.get(url, timeout=_TIMEOUT)
        r.raise_for_status()
        img = PILImage.open(BytesIO(r.content))
        img.load()
        return img.convert("RGB")
    except Exception:
        return None


def _parse_psn(text: str) -> Optional[str]:
    """Extract PSN line from VAA text, e.g. 'N5817 W15458'."""
    m = re.search(r'PSN\s*:\s*([NS]\d+\s+[EW]\d+)', text, re.IGNORECASE)
    return m.group(1).strip() if m else None


def _parse_volcano_name(text: str) -> Optional[str]:
    """
    Extract volcano name only (stop at digits/ID codes).
    Handles: 'VOLCANO: MAYON 273030' → 'Mayon'
    """
    m = re.search(
        r'VOLCANO(?:\s+NAME)?[:\s]+([A-Z][A-Z \-]+?)(?:\s+\d|\s*\n|\s*\r|$)',
        text, re.IGNORECASE | re.MULTILINE,
    )
    if m:
        return m.group(1).strip().title()
    return None


# ── Tokyo VAAC ────────────────────────────────────────────────────────────────

def fetch_tokyo_vaac(n: int = 4) -> list[dict]:
    """
    Parse Tokyo VAAC list page.  Uses opennarro() onclick links (not text
    advisory links) because only a subset of text advisories have VAGFN images.

    Returns up to *n* entries with VAGFN images, plus text info.

    Each result dict:
        {
          "id":       "20260310_27303000_0289",
          "year":     "2026",
          "volcano":  str | None,
          "psn":      str | None,   # e.g. "N1315 E12341"
          "issued":   "20260310",
          "image":    PIL.Image | None,
          "text_url": str,
        }
    """
    try:
        r = _SESSION.get(_TOKYO_LIST_URL, timeout=_TIMEOUT)
        r.raise_for_status()
        html = r.text
    except Exception as exc:
        log.warning("Tokyo VAAC list fetch failed: %s", exc)
        return []

    # Parse VAGFN HTML links from opennarro() onclick
    # e.g.  opennarro('VAGFN/2026/html/20260310_27303000_0289_QH21.html')
    vagfn_links = re.findall(
        r"opennarro\(['\"]VAGFN/(\d{4})/html/(\d{8}_\d+_\d+)_QH21\.html['\"]",
        html,
    )

    # Parse SAT links: openplant('Sat/2026/html/{adv_id}_Sat.html')
    sat_ids: dict[str, str] = {  # adv_id → year
        adv_id: year
        for year, adv_id in re.findall(
            r"openplant\(['\"]Sat/(\d{4})/html/(\d{8}_\d+_\d+)_Sat\.html['\"]",
            html,
        )
    }

    seen: set[str] = set()
    seen_volcano: set[str] = set()   # deduplicate by volcano ID (keep latest only)
    results: list[dict] = []

    for year, adv_id in vagfn_links:
        if adv_id in seen or len(results) >= n:
            break
        seen.add(adv_id)

        # adv_id format: YYYYMMDD_VVVVVVVV_NNNN (e.g. 20260330_27303000_0407)
        # The 2nd segment is the volcano ID; list is newest-first so skip older ones.
        parts = adv_id.split("_")
        vol_id = parts[1] if len(parts) >= 2 else adv_id
        if vol_id in seen_volcano:
            continue
        seen_volcano.add(vol_id)

        img_url  = f"{_TOKYO_IMG_BASE}/{year}/Images/{adv_id}_QH21_01.png"
        text_url = f"{_TOKYO_TXT_BASE}/{year}/{adv_id}_Text.html"

        image = _fetch_image(img_url)

        # Fetch SAT IR image URL if this advisory has a satellite image
        sat_img_url = None
        if adv_id in sat_ids:
            sat_year = sat_ids[adv_id]
            sat_js_url = f"{_TOKYO_BASE}/Sat/{sat_year}/Script/{adv_id}_ir.js"
            try:
                rs = _SESSION.get(sat_js_url, timeout=_TIMEOUT)
                rs.raise_for_status()
                m_sat = re.search(r'new ImageInfo\("([^"]+)"', rs.text)
                if m_sat:
                    sat_img_url = f"{_TOKYO_BASE}/Sat/{sat_year}/Images/{m_sat.group(1)}"
            except Exception:
                pass

        # Fetch text for volcano name / PSN / raw text
        volcano, psn, raw_text = None, None, ""
        try:
            rt = _SESSION.get(text_url, timeout=_TIMEOUT)
            rt.raise_for_status()
            txt = rt.text
            volcano  = _parse_volcano_name(txt)
            psn      = _parse_psn(txt)
            # Extract raw text between HTML comments
            m = re.search(
                r'<!-- VAA Text Start -->(.*?)<!-- VAA Text End -->',
                txt, re.DOTALL
            )
            if m:
                raw_text = re.sub(r'<[Bb][Rr]\s*/?>', '\n', m.group(1)).strip()
        except Exception:
            pass

        log.info(
            "Tokyo VAAC [%s] volcano=%s psn=%s image=%s",
            adv_id, volcano or "?", psn or "?", "OK" if image else "not found",
        )
        results.append({
            "id":          adv_id,
            "year":        year,
            "volcano":     volcano,
            "psn":         psn,
            "issued":      adv_id[:8],   # YYYYMMDD
            "image":       image,
            "text":        raw_text,
            "img_url":     img_url,
            "sat_img_url": sat_img_url,
            "text_url":    text_url,
        })

    log.info("Tokyo VAAC: %d entry/image(s) fetched", len(results))
    return results


# ── Alaska VAAC ───────────────────────────────────────────────────────────────

def fetch_alaska_vaac(n: int = 3) -> list[dict]:
    """
    Fetch the latest *n* Alaska VAAC advisories via NOAA API.

    Image URL: https://www.weather.gov/images/aawu/fcstgraphics/PFXD{NN}PAWU.png
    This is the static "current" graphic per WMO header series — no datetime
    needed; always reflects the most recently issued advisory.

    Each result dict:
        {
          "text":    str,
          "issued":  str (ISO-8601),
          "volcano": str | None,
          "psn":     str | None,   # e.g. "N5817 W15458"
          "image":   PIL.Image | None,
        }
    """
    try:
        r = _SESSION.get(_ALASKA_VAA_API, timeout=_TIMEOUT)
        r.raise_for_status()
        graph = r.json().get("@graph", [])
    except Exception as exc:
        log.warning("Alaska VAAC API fetch failed: %s", exc)
        return []

    # De-duplicate by WMO header (keep most recent per series)
    seen_wmo: set[str] = set()
    results: list[dict] = []

    for prod in graph:
        if len(results) >= n:
            break
        wmo     = prod.get("wmoCollectiveId", "")
        issued  = prod.get("issuanceTime", "")
        prod_url = prod.get("@id", "")

        # Avoid duplicate WMO series
        wmo_key = wmo[:6]
        if wmo_key in seen_wmo:
            continue
        seen_wmo.add(wmo_key)

        text    = ""
        volcano = None
        psn     = None
        image   = None

        # Fetch full product text
        try:
            r2 = _SESSION.get(prod_url, timeout=_TIMEOUT)
            r2.raise_for_status()
            text    = r2.json().get("productText", "")
            volcano = _parse_volcano_name(text)
            psn     = _parse_psn(text)
        except Exception as exc:
            log.warning("Alaska VAAC product text fetch failed: %s", exc)

        # Static VAG image URL: PFXD{NN}PAWU.png
        nn_m = re.search(r'FVAK(\d{2})', wmo + " " + text)
        if nn_m:
            nn  = nn_m.group(1)
            url = _ALASKA_STATIC_TMPL.format(NN=nn)
            image = _fetch_image(url)
            if image:
                log.info("Alaska VAAC image OK: %s", url)

        log.info(
            "Alaska VAAC [%s] volcano=%s psn=%s image=%s",
            issued[:16], volcano or "?", psn or "?", "OK" if image else "not found",
        )
        results.append({
            "text":    text,
            "issued":  issued,
            "volcano": volcano,
            "psn":     psn,
            "image":   image,
        })

    log.info("Alaska VAAC: %d advisory/image(s) fetched", len(results))
    return results


# ── Tokyo VAAC: Active volcanoes (red triangles on indexj.html TOP map) ─────────
_TOKYO_INDEX_BASE = "https://www.data.jma.go.jp/vaac/data"
_TOKYO_INDEX_URL  = f"{_TOKYO_INDEX_BASE}/indexj.html"


def _psn_to_latlon(body: str) -> tuple[float, float] | tuple[None, None]:
    """Parse 'PSN: N5436 E16016' (deg+min) into decimal (lat, lon)."""
    m = re.search(r"PSN:\s*([NS])(\d{2})(\d{2})\s+([EW])(\d{3})(\d{2})", body)
    if not m:
        return None, None
    ns, la_d, la_m, ew, lo_d, lo_m = m.groups()
    lat = (int(la_d) + int(la_m) / 60) * (1 if ns == "N" else -1)
    lon = (int(lo_d) + int(lo_m) / 60) * (1 if ew == "E" else -1)
    return round(lat, 3), round(lon, 3)


def fetch_tokyo_vaac_active() -> list[dict]:
    """
    Parse the Active-volcano table on the Tokyo VAAC top page (indexj.html).
    These are the red-triangle volcanoes currently under a Volcanic Ash
    Advisory. Returns newest-first, one entry per table row:

        {
          "volcano":     "KRASHENINNIKOV",
          "advisory_nr": "2026/4",
          "obs_time":    "2026-07-12 05:20Z",
          "issued_time": "2026-07-12 05:50Z",
          "text_url":    "https://www.data.jma.go.jp/vaac/data/TextData/...",
          "lat": 54.6, "lon": 160.267,
          "text": "<full VAA text>",
        }
    """
    try:
        r = _SESSION.get(_TOKYO_INDEX_URL, timeout=_TIMEOUT)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"   # header declares ISO-8859-1
        html = r.text
    except Exception as exc:
        log.warning("Tokyo VAAC indexj.html fetch failed: %s", exc)
        return []

    rows = re.findall(
        r'<tr class="mtx" id=tr\d+>'
        r'<td><a href="([^"]+)">([^<]+)</a></td>'
        r'<td>([^<]*)</td><td>([^<]*)</td><td>([^<]*)</td>',
        html,
    )

    results: list[dict] = []
    for href, volcano_jp, adv_nr, obs_time, issued_time in rows:
        text_url = href if href.startswith("http") else f"{_TOKYO_INDEX_BASE}/{href}"
        body = ""
        lat = lon = None
        volcano_en = volcano_jp.strip()
        try:
            tr = _SESSION.get(text_url, timeout=_TIMEOUT)
            tr.raise_for_status()
            m = re.search(r"<!-- VAA Text Start -->(.*?)<!-- VAA Text End -->",
                          tr.text, re.S)
            if m:
                body = re.sub(r"<[Bb][Rr]\s*/?>", "\n", m.group(1)).strip()
                lat, lon = _psn_to_latlon(body)
                vm = re.search(r"VOLCANO:\s*([A-Z][A-Za-z0-9\s_-]+?)\s+\d{4,}", body)
                if vm:
                    volcano_en = vm.group(1).strip()
        except Exception as exc:
            log.warning("Tokyo VAAC text fetch failed (%s): %s", volcano_jp, exc)

        results.append({
            "volcano":     volcano_en,          # English (for aviation)
            "volcano_jp":  volcano_jp.strip(),  # Japanese
            "advisory_nr": adv_nr.strip(),
            "obs_time":    obs_time.strip(),
            "issued_time": issued_time.strip(),
            "text_url":    text_url,
            "lat":         lat,
            "lon":         lon,
            "text":        body,
        })

    log.info("Tokyo VAAC active: %d volcano(es)", len(results))
    return results
