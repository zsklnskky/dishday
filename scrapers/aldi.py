# Aldi Süd (DE) и сайты группы на той же платформе: GB, HU, CH, SI (Hofer). Открытый JSON поиска сайта, цены «в магазине».
import urllib.parse
from common import by_search, get_json, row

SITES = {"DE": ("api.aldi-sued.de", "www.aldi-sued.de", "EUR"), "GB": ("api.aldi.co.uk", "www.aldi.co.uk", "GBP"),
         "HU": ("api.aldi.hu", "www.aldi.hu", "HUF"), "CH": ("api.aldi-suisse.ch", "www.aldi-suisse.ch", "CHF"),
         "SI": ("api.hofer.si", "www.hofer.si", "EUR")}


def collect(cc, chain, ing, words):
    api, site, cur = SITES[cc]

    def search(q):
        d = get_json(f"https://{api}/v3/product-search?currency={cur}&serviceType=walk-in&q={urllib.parse.quote(q)}&limit=30&offset=0&sort=relevance")
        out = []
        for p in d.get("data", []):
            pr = p.get("price") or {}
            if not pr.get("amountRelevant"):
                continue
            # суммы в минимальных единицах валюты (центы, пенсы, филлеры)
            out.append(row(p["name"], pr["amountRelevant"] / 100, p.get("sellingSize") or "",
                           url=f"https://{site}/product/{p['urlSlugText']}-{p['sku']}"))
        return out

    return by_search(search, ing, words, chain.get("lang") or {"GB": "en", "HU": "hu", "SI": "sl"}.get(cc, "de"), chain["id"])
