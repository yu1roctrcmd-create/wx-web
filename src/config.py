"""
Routes, airports, and application configuration.
"""

# ── Routes ───────────────────────────────────────────────────────────────────
ROUTES: dict[str, dict] = {
    "NRT-ANC": {
        "name": "Narita → Anchorage",
        "departure": "RJAA",
        "destination": "PANC",
        "alternates": ["PAFA", "PAED", "KSEA"],
        # FIRs along route (used to filter SIGMETs)
        "firs": ["RJTG", "KZAK", "PAWU"],
    },
    "NRT-PVG": {
        "name": "Narita → Shanghai Pudong",
        "departure": "RJAA",
        "destination": "ZSPD",
        "alternates": ["ZSSS", "RJFR"],
        "firs": ["RJTG", "ZSHA"],
    },
    "NRT-HKG": {
        "name": "Narita → Hong Kong",
        "departure": "RJAA",
        "destination": "VHHH",
        "alternates": ["RCTP", "ZGSZ"],
        "firs": ["RJTG", "ZSHA", "VHHK"],
    },
    "NRT-SIN": {
        "name": "Narita → Singapore",
        "departure": "RJAA",
        "destination": "WSSS",
        "alternates": ["WMKK", "WIDD"],
        "firs": ["RJTG", "VHHK", "WSJC"],
    },
    # ── Southeast Asia route ──────────────────────────────────────────────────
    "BKK-NRT": {
        "name": "Bangkok Suvarnabhumi → Narita",
        "departure": "VTBS",
        "destination": "RJAA",
        "alternates": [
            "VTBU",   # U-Tapao (Bangkok alternate)
            "VHHH",   # Hong Kong (ETP)
            "RCTP",   # Taipei (ETP)
            "ROAH",   # Naha/Okinawa
            "VVDN",   # Da Nang (ETP)
            "VVLT",   # Lien Khuong/Da Lat (ETP)
        ],
        "firs": ["VTBB", "VVHH", "VHHK", "RJTG"],
    },
    "NRT-TPE": {
        "name": "Narita → Taipei",
        "departure": "RJAA",
        "destination": "RCTP",
        "alternates": ["ROAH", "RCKH"],
        "firs": ["RJTG", "RCAA"],
    },
    # ── New trans-Pacific / North-America routes ──────────────────────────────
    "NRT-LAX": {
        "name": "Narita → Los Angeles",
        "departure": "RJAA",
        "destination": "KLAX",
        "alternates": ["KONT", "KSFO", "KOAK", "KMHR"],
        "firs": ["RJTG", "KZAK", "KZLA"],
    },
    "NRT-DFW": {
        "name": "Narita → Dallas/Fort Worth",
        "departure": "RJAA",
        "destination": "KDFW",
        "alternates": ["KIAH", "KORD"],
        "firs": ["RJTG", "KZAK", "KZFW"],
    },
    "ANC-ORD-JFK": {
        "name": "Anchorage → Chicago O'Hare → New York JFK",
        "departure": "PANC",
        "destination": "KJFK",
        # KORD is the en-route stop; listed first so METAR/TAF is fetched
        "alternates": ["KORD", "KRFD", "KIND", "KDTW", "KMSP", "KSEA", "CYEG"],
        "firs": ["PAWU", "KZSE", "KZAU", "KZNY"],
    },
    # ── New North-Atlantic / European routes ──────────────────────────────────
    "ANC-AMS": {
        "name": "Anchorage → Amsterdam Schiphol",
        "departure": "PANC",
        "destination": "EHAM",
        "alternates": ["EBBR", "EDDF", "EDFH", "EDDL"],
        "firs": ["PAWU", "BIRD", "EGGX", "EHAA"],
    },
    "ANC-FRA": {
        "name": "Anchorage → Frankfurt",
        "departure": "PANC",
        "destination": "EDDF",
        "alternates": ["EDFH", "EDDK", "EDDL", "EBLG", "LSZH", "EHAM"],
        "firs": ["PAWU", "BIRD", "EGGX", "EDGG"],
    },
    "MXP-NRT": {
        "name": "Milan Malpensa → Narita",
        "departure": "LIMC",
        "destination": "RJAA",
        "alternates": ["LSZH", "LIRF", "EDDF", "EDFH", "EHAM"],
        "firs": ["LIMM", "URRR", "RJTG"],
    },
    # ── ETP airports for ANC-AMS/FRA ─────────────────────────────────────────
    "ETP-ANC-EUR": {
        "name": "ETP Airport along ANC-AMS/FRA",
        "departure": "EINN",
        "destination": "EDFH",
        "alternates": [
            "EGLL",   # London Heathrow
            "EGSS",   # London Stansted
            "EBBR",   # Brussels
            "EBLG",   # Liège
            "EDDF",   # Frankfurt
            "EDDK",   # Cologne/Bonn
            "EDDL",   # Düsseldorf
        ],
        "firs": ["EISN", "EGTT", "EBBU", "EDGG"],
    },
    # ── ETP airports for MXP-NRT (west → east) ───────────────────────────────
    "ETP-MXP-NRT": {
        "name": "ETP Airport along MXP-NRT",
        "departure": "EPWA",
        "destination": "UHPP",
        "alternates": [
            "EFHK",   # Helsinki
            "LBBG",   # Burgas
            "LTAC",   # Ankara
            "UBBB",   # Baku
            "UTAA",   # Ashgabat
            "UACC",   # Nur-Sultan
            "UAAA",   # Almaty
            "UZTT",   # Tashkent
            "ZWWW",   # Urumqi
            "ZLXY",   # Xi'an
            "ZBAA",   # Beijing Capital
            "ZBHH",   # Hohhot
            "ZSQD",   # Qingdao
            "ZMCK",   # Ulaanbaatar
            "UUEE",   # Moscow Sheremetyevo
            "UUDD",   # Moscow Domodedovo
            "ULLI",   # St. Petersburg
            "USSS",   # Yekaterinburg
            "UNNT",   # Novosibirsk
            "UNKL",   # Krasnoyarsk
            "UIBB",   # Bratsk
            "UEEE",   # Yakutsk
            "UHHH",   # Khabarovsk
            "UHSS",   # Yuzhno-Sakhalinsk
        ],
        "firs": ["UUUU", "ULLL", "USSS", "UNNN", "UIII", "UHBB"],
    },
}

# Collect all unique airports across all routes
ALL_AIRPORTS: list[str] = []
for r in ROUTES.values():
    for ap in [r["departure"], r["destination"]] + r["alternates"]:
        if ap not in ALL_AIRPORTS:
            ALL_AIRPORTS.append(ap)

# FIR IDs relevant to all routes combined (for SIGMET filtering)
ALL_FIRS: set[str] = set()
for r in ROUTES.values():
    ALL_FIRS.update(r["firs"])

# ── Weather chart URLs ────────────────────────────────────────────────────────
# JMA Aviation charts (公式 airinfo)
# asas は n-kishou.com (NKISHOU_SURFACE_CHARTS) でカバー済みのため除外
JMA_CHARTS: dict[str, str] = {
    "fbjp":        "https://www.data.jma.go.jp/airinfo/data/pict/fbjp/fbjp.png",
    "fbjp_low_e":  "https://www.data.jma.go.jp/airinfo/data/pict/low-level_sigwx/fbtk03.png",
    "fbjp_low_w":  "https://www.data.jma.go.jp/airinfo/data/pict/low-level_sigwx/fbos03.png",
}

# imocwx.com — 高層天気図 (200hPa / 250hPa, 00Z と 12Z)
IMOCWX_CHARTS: dict[str, str] = {
    "upper_200_00z": "https://www.imocwx.com/wxfax/aupa20_00.gif",
    "upper_200_12z": "https://www.imocwx.com/wxfax/aupa20_12.gif",
    "upper_250_00z": "https://www.imocwx.com/wxfax/aupa25_00.gif",
    "upper_250_12z": "https://www.imocwx.com/wxfax/aupa25_12.gif",
}

# ALL charts combined (used by charts.py)
ALL_CHARTS: dict[str, str] = {**JMA_CHARTS, **IMOCWX_CHARTS}

# ── JMA 飛行場時系列予報 ──────────────────────────────────────────────────────
# JMA TAF chart は日本国内空港のみ提供（QMCD98_{ICAO}.png）
# 海外空港は JMA チャートなし → リストから除外してログノイズを削減
JMA_TAF_AIRPORTS: list[str] = [
    "RJAA",  # 成田
    "RJTT",  # 羽田
    "RJFR",  # 北九州
    "RJGG",  # 名古屋（小牧）
    "RJBB",  # 関西
    "RJCC",  # 千歳
    "ROAH",  # 那覇
]

# ── JMA 三十分大気解析 平面図 ─────────────────────────────────────────────────
# FL name → select value (URL code = 100 + value)
# e.g. FL350 → value=35 → WANLF135
MAIJI_FL_LEVELS: dict[str, int] = {
    "FL290": 29,
    "FL330": 33,
    "FL350": 35,
    "FL390": 39,
}

# ── JMA 三十分大気解析 縦断図（ルート別）────────────────────────────────────
# route_key → list of (label, code)
# URL: https://www.data.jma.go.jp/airinfo/data/pict/maiji/WANLC{code}_RJTD_{ts}.PNG
# code = 100 + route_value (e.g. 石垣-東京 v=07 → code=107)
MAIJI_CROSS_ROUTES: dict[str, list] = {
    "NRT-ANC": [
        ("東経145.0°", 150),
        ("東経142.5°", 151),
        ("東経140.0°", 152),
    ],
    "NRT-PVG": [
        ("東京-福岡", 105),
        ("東経130.0°", 156),
        ("東経127.5°", 157),
        ("東経125.0°", 158),
        ("東経122.5°", 159),
    ],
    "NRT-TPE": [
        ("石垣-東京", 107),
    ],
    "BKK-NRT": [
        ("与那国-高松", 108),   # Yonaguni-Takamatsu: Ryukyu approach
        ("石垣-東京",  107),   # Ishigaki-Tokyo: main Japan leg
        ("東経122.5°", 159),   # E122.5°: Taiwan Strait / East China Sea
    ],
}

# ── JMA ひまわり衛星画像（時刻ベース）────────────────────────────────────────
# URL: {HIMAWARI_BASE}/{area}/{area}_{element}_{HHMM}.jpg (10分更新, UTC)
# HHMM はファイル名のタイムスタンプ（観測時刻 − 10分）
HIMAWARI_BASE = "https://www.data.jma.go.jp/mscweb/data/himawari/img"

# {key: (area, element, ラベル)}
HIMAWARI_CHARTS: dict[str, tuple[str, str, str]] = {
    "jpn_ir":    ("jpn", "b13", "日本周辺 赤外線 (Himawari-9 B13)"),
    "jpn_color": ("jpn", "trm", "日本周辺 トゥルーカラー (Himawari-9)"),
    "se_ir":     ("se1", "b13", "東南アジア 赤外線 (Himawari-9 B13)"),
    "se_hrp":    ("r2s", "hrp", "東南アジア 降水ポテンシャル (Himawari-9 HRP)"),
}

# 北米静止衛星 — 常に最新を指す静的URL
SATELLITE_CHARTS: dict[str, str] = {
    "nam_ir": "https://tropic.ssec.wisc.edu/real-time/mosaic/images/moswir.jpg",
}

# ── 地上天気図 ─────────────────────────────────────────────────────────────────
# n-kishou.com (日本気象協会) — JST ファイル名タイムスタンプ
# URL: https://n-kishou.com/ee/image4/lfax/{code}_{YYYYMMDDHHmm}.png
# {key: (code, valid_jst_hours, ラベル)}
NKISHOU_SURFACE_CHARTS: dict[str, tuple[str, list, str]] = {
    "asas":    ("asas",    [3, 9, 15, 21], "地上天気図 実況 (ASAS)"),
    "fsas24":  ("fsas24",  [3, 9, 15, 21], "地上天気図 24h予報 (FSAS24)"),
    "aupq35":  ("aupq35",  [9, 21],        "500hPa 高層天気図 (AUPQ35)"),
    "axjp140": ("axjp140", [9, 21],        "アジア地上天気予報図 AXJP140"),
    "fxjp106": ("fxjp106", [0, 12],        "アジア地上天気予報図 FXJP106"),
    # axjp130 は n-kishou.com に存在しないため除外
}

# 太平洋地上天気図 — 常に最新を指す静的URL
SURFACE_CHARTS_STATIC: dict[str, str] = {
    "pac_sfc": "https://ocean.weather.gov/P_sfc_full_ocean_color.png",
}

# ── 欧州・北大西洋 気象図 ─────────────────────────────────────────────────────
# {key: (url, label)}  — fetched by fetch_euro_charts() in charts.py
EURO_CHARTS: dict[str, tuple[str, str]] = {
    "euro_sfc_ana":  (
        "https://www.dwd.de/DWD/wetter/wv_spez/hobbymet/wetterkarten/bwk_bodendruck_na_ana.png",
        "欧州地上天気図 実況 (DWD)",
    ),
    "euro_sfc_36h":  (
        "https://www.dwd.de/DWD/wetter/wv_spez/hobbymet/wetterkarten/ico_tkboden_na_036.png",
        "欧州地上天気図 36h予報 (DWD)",
    ),
    "euro_sfc_wz":   (
        "https://www.wetterzentrale.de/maps/DWDEU_0.png",
        "欧州地上天気図 (WetterZentrale/DWD)",
    ),
    "natl_sfc":      (
        "https://ocean.weather.gov/A_sfc_full_ocean_color.png",
        "北大西洋地上天気図 (NOAA OPC)",
    ),
    "euro_sigwx":    (
        "https://aviationweather.gov/data/products/fax/F24_sigwx_mid_eur.gif",
        "欧州航空悪天予想図 SIGWX (AWC F24)",
    ),
    "eurasia_sfc":   (
        "https://meteoinfo.ru/hmc-input/mapsynop/Analiz.png",
        "ユーラシア地上天気図 (Meteoinfo Russia)",
    ),
    "euro_sat_wv":   (
        "https://img.allmetsat.com/sat/anim-msg-europe_central-wv.gif",
        "欧州 水蒸気衛星 (MSG/Meteosat WV)",
    ),
    "euro_sat_rgb":  (
        "https://img.allmetsat.com/sat/anim-msg-europe_central-rgb.gif",
        "欧州 カラー衛星 (MSG/Meteosat RGB)",
    ),
}
# PGDE14 SIGWX (Iceland Met Office): URL template — HH = 00/06/12/18
PGDE14_URL_TEMPLATE = "http://www.vedur.is/photos/flugkort/PGDE14_EGRR_{HH}00.png"

# ── NOAA AWC API base ─────────────────────────────────────────────────────────
NOAA_API_BASE = "https://aviationweather.gov/api/data"
METAR_HOURS = 2
PIREP_HOURS = 6

