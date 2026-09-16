# Picard (FR, замороженные продукты): страница поиска picard.fr рисуется на сервере, у каждой плитки атрибут
# data-gtm с названием и ценой. Названия набраны капсом - приводим к обычному регистру, иначе common.head()
# выбрасывает все слова и товар не подбирается. Цены интернет-магазина.
import html, json, re, urllib.parse
from common import by_search, fetch, row


def parse(page):
    out = []
    for m in re.finditer(r'data-pid="[^"]*"\s+data-gtm="([^"]*)"', page):
        try:
            g = json.loads(html.unescape(m.group(1)))
        except ValueError:
            continue
        if g.get("item_name") and g.get("price"):
            out.append(row(g["item_name"].title(), float(g["price"])))
    return out


def collect(cc, chain, ing, words):
    return by_search(lambda q: parse(fetch("https://www.picard.fr/recherche?q=" + urllib.parse.quote(q), lang="fr")),
                     ing, words, "fr", chain["id"])


if __name__ == "__main__":
    t = ('<div class="pi-product-tile" data-pid="000000000000019330" data-gtm="{&quot;item_id&quot;:&quot;19330&quot;,'
         '&quot;item_name&quot;:&quot;600G PETITS POIS EXTRA FINS&quot;,&quot;price&quot;:3.45}">')
    r = parse(t)[0]
    assert r["price"] == 3.45 and r["size"] == 0.6 and r["unit"] == "kg" and r["name"].startswith("600G Petits"), r
    print("picard self-check ok")
