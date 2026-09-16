# Dirk (NL, сеть Detailresult): поиск dirk.nl. Данные страницы лежат в payload Nuxt (<script id="__NUXT_DATA__">) -
# это плоский массив, где поля товара хранят индексы в нём же. Берём название, бренд, фасовку и priceToShow.
# Бренд из названия убираем: он стоит первым словом и мешает common.head() увидеть сам продукт. Цены онлайн-магазина.
import json, re, urllib.parse
from common import by_search, fetch, row

FULL = (("liter", "l"), ("stuks", "st"), ("stuk", "st"), ("gram", "g"), ("kilo", "kg"))


def parse(page):
    m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', page, re.S)
    if not m:
        return []
    a = json.loads(m.group(1))
    get = lambda i: a[i] if isinstance(i, int) and 0 <= i < len(a) else None
    out = []
    for o in a:
        if not (isinstance(o, dict) and "headerText" in o and "packaging" in o and "price" in o):
            continue
        name, brand, pk, pr = get(o["headerText"]), get(o.get("brand")), get(o["packaging"]), get(o["price"])
        price = get(pr.get("priceToShow")) if isinstance(pr, dict) else None
        if not (isinstance(name, str) and isinstance(price, (int, float)) and price > 0):
            continue
        if isinstance(brand, str) and brand:
            name = re.sub(r"^" + re.escape(brand) + r"\s+", "", name, flags=re.I)
        size = (pk if isinstance(pk, str) else "").lower()
        for x, y in FULL:
            size = size.replace(x, y)
        url = get(o.get("url"))
        out.append(row(name, price, size, url="https://www.dirk.nl" + url if isinstance(url, str) else None))
    return out


def collect(cc, chain, ing, words):
    return by_search(lambda q: parse(fetch("https://www.dirk.nl/zoeken/producten/" + urllib.parse.quote(q), lang="nl")),
                     ing, words, "nl", chain["id"])


if __name__ == "__main__":
    arr = [{"headerText": 1, "packaging": 2, "brand": 3, "url": 4, "price": 5},
           "Zuivelmeester Halfvolle melk", "2 liter", "Zuivelmeester", "/p/101229", {"priceToShow": 6}, 1.65]
    r = parse('<script type="application/json" id="__NUXT_DATA__">%s</script>' % json.dumps(arr))[0]
    assert r["name"] == "Halfvolle melk 2 l" and r["price"] == 1.65 and r["size"] == 2.0 and r["unit"] == "l", r
    print("dirk self-check ok")
