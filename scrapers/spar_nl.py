# SPAR (NL): страница поиска spar.nl отдаёт готовые плитки товаров. Цена и бренд - в data-ga-product-data
# (JSON для аналитики), фасовка - строкой под названием ("1 Liter"). Цены интернет-магазина.
import html, json, re, urllib.parse
from common import by_search, fetch, row

FULL = (("liter", "l"), ("stuks", "st"), ("stuk", "st"), ("gram", "g"), ("kilo", "kg"))


def parse(page):
    out = []
    for block in page.split('id="product-tile-')[1:]:
        g = re.search(r'data-ga-product-data="([^"]*)"', block)
        size = re.search(r'spar-paragraph__14-400[^>]*>\s*([^<]{1,25}?)\s*<', block)
        href = re.search(r'href="(/[^"]+)"', block)
        if not g:
            continue
        d = json.loads(html.unescape(g.group(1)))
        name, brand = d.get("ProductName") or "", d.get("Brand") or ""
        if brand:  # бренд впереди названия мешает common.head() найти сам продукт
            name = re.sub(r"^" + re.escape(brand) + r"\s+", "", name, flags=re.I)
        s = (size.group(1) if size else "").lower()
        for a, b in FULL:
            s = s.replace(a, b)
        if d.get("Price"):
            out.append(row(name, d["Price"], s, url="https://www.spar.nl" + href.group(1) if href else None))
    return out


def collect(cc, chain, ing, words):
    return by_search(lambda q: parse(fetch("https://www.spar.nl/zoek/?fq=" + urllib.parse.quote(q), lang="nl")),
                     ing, words, "nl", chain["id"])


if __name__ == "__main__":
    tile = ('id="product-tile-57414" data-productid="57414"><a href="/melkan-karnemelk-3293254/" '
            'data-ga-product-data="{&quot;ProductName&quot;:&quot;Melkan karnemelk&quot;,&quot;Price&quot;:1.19,'
            '&quot;Brand&quot;:&quot;Melkan&quot;}">x</a><p>Melkan karnemelk</p>'
            '<span class="spar-paragraph__14-400">1 Liter</span>')
    r = parse(tile)[0]
    assert r["name"] == "karnemelk 1 l" and r["price"] == 1.19 and r["size"] == 1.0 and r["unit"] == "l", r
    print("spar_nl self-check ok")
