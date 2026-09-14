# Conad (IT, сеть №1 по доле): поиск spesaonline.conad.it отдаёт карточки в HTML - название, фасовка, цена за кг/л и цена.
# Цены магазина по умолчанию (без выбора адреса).
import html, re, urllib.parse
from common import by_search, fetch, row, to_num

UNIT = {"kg": "kg", "l": "l", "pz": "pc"}


def parse(page):
    out = []
    for card in page.split('class="card-middle')[1:]:
        name = re.search(r"<h3>(.*?)</h3>", card, re.S)
        href = re.search(r'href="(/p/[^"]+)"', card)
        qty = re.search(r'class="product-quantity">\s*([^<]+?)\s*<', card)
        kg = re.search(r'class="product-price-kg[^"]*">\s*([\d.,]+)\s*€\s*/\s*(\w+)', card)
        price = re.search(r'class="product-price[^"-]*[^"]*product-price[^"]*">\s*([\d.,]+)\s*€|class="product-price[^"]*">\s*([\d.,]+)\s*€', card)
        if not (name and price):
            continue
        r = row(html.unescape(name.group(1).strip()), to_num(price.group(1) or price.group(2)), qty.group(1) if qty else "",
                url="https://spesaonline.conad.it" + href.group(1) if href else None)
        if kg and UNIT.get(kg.group(2).lower()):
            r["ppu"], r["unit"] = to_num(kg.group(1)), UNIT[kg.group(2).lower()]
        out.append(r)
    return out


def collect(cc, chain, ing, words):
    return by_search(lambda q: parse(fetch("https://spesaonline.conad.it/search?query=" + urllib.parse.quote(q), lang="it")),
                     ing, words, "it", chain["id"])


if __name__ == "__main__":
    card = ('class="card-middle"><a href="/p/latte-1-l--262867"><h3>Latte UHT Parzialmente Scremato 1 L Conad</h3></a>'
            '<b class="product-quantity"> 1 L </b><div class="product-price-kg "> 0,89 € / L </div>'
            '<div class="product-price-red product-price f-roboto uk-margin-auto-left"> 0,89€ </div>')
    r = parse(card)[0]
    assert r["price"] == 0.89 and r["ppu"] == 0.89 and r["unit"] == "l" and r["size"] == 1.0, r
    print("conad self-check ok")
