# Dia (ES): JSON поиска сайта, есть цена упаковки и цена за единицу (measure_unit). Цены для индекса 28041 (Мадрид) по умолчанию.
import urllib.parse
from common import by_search, get_json, row

UNIT = {"KILO": "kg", "KILOGRAMO": "kg", "LITRO": "l", "UNIDAD": "pc", "DOCENA": None}


def collect(cc, chain, ing, words):
    def search(q):
        d = get_json("https://www.dia.es/api/v1/search-back/search/reduced?page=1&q=" + urllib.parse.quote(q), lang="es")
        out = []
        for it in d.get("search_items", []):
            pr = it.get("prices") or {}
            if not pr.get("price"):
                continue
            r = row(it["display_name"], pr["price"], url="https://www.dia.es" + it.get("url", ""))
            u = UNIT.get(pr.get("measure_unit"))
            if u and pr.get("price_per_unit"):
                r["ppu"], r["unit"] = pr["price_per_unit"], u
                r["size"] = round(pr["price"] / pr["price_per_unit"], 3)
            out.append(r)
        return out

    return by_search(search, ing, words, "es", chain["id"])
