"""Источники данных: Skinport (каталог) и Steam (priceoverview)."""
import logging

import requests

from config import (SKINPORT_TIMEOUT, SKINPORT_URL, STEAM_OVERVIEW_URL,
                    STEAM_CURRENCY, STEAM_TIMEOUT)

log = logging.getLogger("sources")

_session = requests.Session()
_session.headers.update({
    "User-Agent": "ArbitrageScanner/2.0 (+github.com/davletovaalmira11-creator)",
    "Accept-Encoding": "gzip, br",
    "Accept": "application/json",
})


class RateLimited(Exception):
    pass


def fetch_skinport():
    r = _session.get(SKINPORT_URL,
                     params={"app_id": 730, "currency": "EUR"},
                     timeout=SKINPORT_TIMEOUT)
    r.raise_for_status()
    return r.json()


def parse_price(p):
    """Steam отдаёт строки вида '5,43€' / '€5.43' / '5.43'."""
    if p is None:
        return None
    if isinstance(p, (int, float)):
        return float(p)
    s = str(p)
    for ch in ("€", "$", "\u20bd", "\u00a0"):
        s = s.replace(ch, "")
    s = s.strip()
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def parse_volume(v):
    if v is None:
        return 0
    if isinstance(v, (int, float)):
        return int(v)
    try:
        return int(str(v).replace(",", "").replace("\u00a0", "").split()[0])
    except (ValueError, IndexError):
        return 0


def fetch_steam(name):
    r = _session.get(STEAM_OVERVIEW_URL,
                     params={"appid": 730, "currency": STEAM_CURRENCY,
                             "market_hash_name": name},
                     timeout=STEAM_TIMEOUT)
    if r.status_code == 429:
        raise RateLimited(name)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        return None
    return {"price": parse_price(data.get("lowest_price")),
            "volume": parse_volume(data.get("volume"))}
