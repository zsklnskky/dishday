# Konzum (HR, сеть №1): поиск konzum.hr/web/search?search[term]= отдаёт карточки в HTML.
# Имя и цена - в data-ga-*, цена за кг/л/шт - «Cijena za j.m.». Цены интернет-магазина без выбора магазина.
import html, re, urllib.parse
from common import by_search, fetch, row, to_num

UNIT = {"kg": "kg", "l": "l", "kom": "pc"}
_GA = re.compile(r'data-ga-name="([^"]+)"\s+data-ga-price="([^"]+)"')
_JM = re.compile(r"Cijena za j\.m\.:\s*<strong>\s*([\d.,]+)\s*€/(\w+)")


def parse(page):
    out = []
    for card in page.split('<article class="product-item')[1:]:
        ga = _GA.search(card)
        if not ga:
            continue
        href = re.search(r'href="(/web/products/[^"]+)"', card)
        r = row(html.unescape(ga.group(1)), to_num(ga.group(2)), url="https://www.konzum.hr" + href.group(1) if href else None)
        jm = _JM.search(card)
        if jm and UNIT.get(jm.group(2)):
            r["ppu"], r["unit"] = to_num(jm.group(1)), UNIT[jm.group(2)]
        out.append(r)
    return out


def collect(cc, chain, ing, words):
    url = "https://www.konzum.hr/web/search?per_page=100&search%5Bterm%5D="
    return by_search(lambda q: parse(fetch(url + urllib.parse.quote(q), lang="hr")), ing, words, "hr", chain["id"])


if __name__ == "__main__":
    card = ('<article class="product-item product-default "> <div data-ga-type="productImpression" data-ga-id="02233999" '
            'data-ga-name="K Plus Trajno mlijeko 2,8% m.m. 1 l" data-ga-price="0,65 €" data-ga-brand="x"></div>'
            '<a class="link-to-product" href="/web/products/mlijeko-k-plus-trajno-2-8-1l">'
            '<div> Cijena za j.m.: <strong>0,65 €/l</strong> </div></article>')
    r = parse(card)[0]
    assert r["price"] == 0.65 and r["ppu"] == 0.65 and r["unit"] == "l" and r["size"] == 1.0, r
    assert r["url"].endswith("/web/products/mlijeko-k-plus-trajno-2-8-1l")
    print("konzum self-check ok")
