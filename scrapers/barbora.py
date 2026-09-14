# Barbora - интернет-магазин Maxima (LT, LV, EE). Страница поиска содержит window.b_productList с ценой и ценой за единицу.
import json, re, urllib.parse
from common import by_search, fetch, row

SITES = {"LT": ("barbora.lt", "paieska", "produktai", "lt"), "LV": ("barbora.lv", "meklet", "produkti", "lv"),
         "EE": ("barbora.ee", "otsing", "toode", "et")}
UNIT = {"kg": "kg", "l": "l", "vnt.": "pc", "gab.": "pc", "tk": "pc"}


def parse(page, host, prod):
    m = re.search(r"window\.b_productList\s*=\s*(\[.*?\]);", page, re.S)
    out = []
    for p in json.loads(m.group(1)) if m else []:
        if not p.get("price"):
            continue
        r = row(p.get("title", ""), p["price"], url=f"https://{host}/{prod}/{p.get('Url', '')}")
        u = UNIT.get((p.get("comparative_unit") or "").lower())
        if u and p.get("comparative_unit_price"):
            r["ppu"], r["unit"] = p["comparative_unit_price"], u
        out.append(r)
    return out


def collect(cc, chain, ing, words):
    host, path, prod, lang = SITES[cc]
    return by_search(lambda q: parse(fetch(f"https://{host}/{path}?q=" + urllib.parse.quote(q), lang=lang), host, prod),
                     ing, words, lang, chain["id"])


if __name__ == "__main__":
    page = 'window.b_productList = [{"title":"Pienas 2,5 %, 1 l","price":0.94,"comparative_unit":"l","comparative_unit_price":0.94,"Url":"pienas"}];'
    r = parse(page, "barbora.lt", "produktai")[0]
    assert r["ppu"] == 0.94 and r["unit"] == "l" and r["size"] == 1.0
    print("barbora self-check ok")
