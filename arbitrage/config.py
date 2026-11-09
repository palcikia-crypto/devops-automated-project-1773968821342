"""Настройки арбитражного сканера (Skinport -> Steam)."""
import os


def env(name, default, cast=str):
    v = os.environ.get(name)
    if v is None or v == "":
        return default
    if cast is bool:
        return v.lower() in ("1", "true", "yes", "on")
    try:
        return cast(v)
    except ValueError:
        return default


SKINPORT_URL = "https://api.skinport.com/v1/items"
SKINPORT_TIMEOUT = env("SKINPORT_TIMEOUT", 25, int)

STEAM_OVERVIEW_URL = "https://steamcommunity.com/market/priceoverview/"
STEAM_TTL = env("STEAM_TTL", 6 * 3600, int)
STEAM_TIMEOUT = env("STEAM_TIMEOUT", 15, int)
STEAM_CURRENCY = env("STEAM_CURRENCY", 3, int)     # 3 = EUR
STEAM_MAX_FAILS = env("STEAM_MAX_FAILS", 5, int)

STEAM_FEE = env("STEAM_FEE", 0.15, float)     # продавец получает price/1.15
SKINPORT_FEE = env("SKINPORT_FEE", 0.0, float)  # комиссия покупателя (обычно 0)

MIN_ROI = env("MIN_ROI", 10.0, float)
MIN_PROFIT = env("MIN_PROFIT", 0.5, float)
MIN_VOL = env("MIN_VOL", 20, int)
PRICE_MIN = env("PRICE_MIN", 0.15, float)
PRICE_MAX = env("PRICE_MAX", 5000.0, float)
DEALS_LIMIT = env("DEALS_LIMIT", 500, int)

PRIORITY_ITEMS = [
    "CS:GO Weapon Case 2",
    "MP9 | Starlight Protector (Field-Tested)",
    "Operation Breakout Weapon Case",
    "CS:GO Weapon Case 3",
]
