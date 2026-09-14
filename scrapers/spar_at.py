# Spar (AT): открытый поиск FactFinder, которым пользуется spar.at. Цена и «price-per-unit» вида «1.32 €/l».
import json, re, urllib.parse
from common import by_search, fetch, row, to_num

UNIT = {"kg": "kg", "l": "l", "stk": "pc", "stück": "pc"}


def collect(cc, chain, ing, words):
    def search(q):
        qq = urllib.parse.quote(q)
        d = json.loads(fetch(f"https://search-spar.spar-ics.com/fact-finder/rest/v4/search/products_lmos_at?query={qq}&q={qq}&page=1&hitsPerPage=30", lang="de"))
        out = []
        for h in d.get("hits", []):
            v = h.get("masterValues") or {}
            if not v.get("price"):
                continue
            name = " ".join(filter(None, (v.get("title"), v.get("short-description"))))
            r = row(name, v["price"], v.get("short-description-3") or "", url="https://www.spar.at/onlineshop" + (v.get("url") or ""))
            m = re.match(r"([\d.,]+)\s*€\s*/\s*(\w+)", v.get("price-per-unit") or "")
            if m and UNIT.get(m.group(2).lower()):
                r["ppu"], r["unit"] = to_num(m.group(1)), UNIT[m.group(2).lower()]
            out.append(r)
        return out

    return by_search(search, ing, words, "de", chain["id"])
