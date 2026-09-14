# Axfood (SE): Willys и Hemköp, поиск сайта отдаёт JSON с ценой и сравнительной ценой (kr/kg, kr/l, kr/st).
import urllib.parse
from common import by_search, get_json, row, to_num

SITES = {"willys": "www.willys.se", "hemkop": "www.hemkop.se"}
UNIT = {"kg": "kg", "l": "l", "st": "pc"}


def collect(cc, chain, ing, words):
    site = SITES[chain["id"]]

    def search(q):
        d = get_json(f"https://{site}/search?size=30&q=" + urllib.parse.quote(q), lang="sv")
        out = []
        for p in d.get("results") or []:
            if not p.get("priceValue"):
                continue
            r = row(p.get("name", ""), p["priceValue"], p.get("displayVolume") or p.get("productLine2") or "",
                    url=f"https://{site}/produkt/{p.get('code', '')}")
            u = UNIT.get((p.get("comparePriceUnit") or "").lower())
            if u and p.get("comparePrice"):
                r["ppu"], r["unit"] = to_num(p["comparePrice"]), u
            out.append(r)
        return out

    return by_search(search, ing, words, "sv", chain["id"])
