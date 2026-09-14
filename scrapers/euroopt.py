# Евроопт (BY): поиск edostavka.by, товары в __NEXT_DATA__. measurePrice - цена за кг/л, у весовых basePrice уже за кг.
import json, re, urllib.parse
from common import by_search, fetch, row


def parse(page):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page, re.S)
    d = json.loads(m.group(1)) if m else {}
    out = []
    for p in ((d.get("props") or {}).get("pageProps") or {}).get("listing", {}).get("products") or []:
        pr = p.get("price") or {}
        price = float(pr.get("basePrice") or 0)
        if not price:
            continue
        r = row(p.get("productName") or "", price, url=f"https://edostavka.by/product/{p.get('productId', '')}")
        try:
            measure = float(str(pr.get("measurePrice") or "0").replace(",", "."))
        except ValueError:
            measure = 0
        if p.get("soldByWeight") and not measure:
            r.update(ppu=price, unit="kg", size=r["size"] or 1.0)
        elif measure and r["unit"] in ("kg", "l"):
            r["ppu"] = measure
        out.append(r)
    return out


def collect(cc, chain, ing, words):
    return by_search(lambda q: parse(fetch("https://edostavka.by/search?query=" + urllib.parse.quote(q), lang="ru")),
                     ing, words, "ru", chain["id"])
