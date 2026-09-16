# Voli (ME, сеть №1): страницы категорий отдают карточки Vue с JSON товара (:product="{...}") - имя, цена, фасовка.
# Поиск на сайте запрос игнорирует (отдаёт случайные товары), поэтому берём каталог продуктовых категорий.
import html, json, re
from common import by_catalog, fetch, row

# конечные (не родительские) категории: родительские отдают лишь витрину из 8 товаров
CATS = (22, 23, 24, 26, 28, 30, 31, 32, 33, 34,          # молоко, йогурт, сметана, яйца, масло, сыры
        159, 160, 161, 162, 163, 49, 167,                # свинина, говядина, курица, баранина, индейка, рыба
        181, 51,                                          # тунец, мясные и рыбные консервы
        146, 147, 149, 150, 153, 155, 248, 106,           # фрукты, овощи, грибы, орехи, соусы и пелати, оливки, зелень, заморож. овощи
        82, 86,                                           # тосты, хлеб
        75, 76, 77, 78, 79, 80, 81,                       # макароны, оливковое масло, рис, подсолнечное масло, мука, сахар и соль, уксус
        100, 101, 102, 103, 46, 74)                       # смеси специй, специи, паприка, перец, мёд, соя
URL = "https://voli.me/kategorije/%d"
_CARD = re.compile(r':product="(\{.*?\})"')


def cards(page, url):
    out = []
    for s in _CARD.findall(page):
        p = json.loads(html.unescape(s))
        price = p.get("special_price") or p.get("regular_price")
        if not price or not p.get("name"):
            continue
        out.append(row(p["name"], float(price), f'{p.get("neto_quantity") or ""} {p.get("quantity_unit") or ""}', url=url))
    return out


def collect(cc, chain, ing, words):
    rows = []
    for c in CATS:
        url = URL % c
        try:
            rows += cards(fetch(url, lang="sr"), url)
        except Exception as e:
            print(f"  voli {c}: {type(e).__name__} {e}"[:140], flush=True)
    if not rows:
        raise RuntimeError("категории Voli не отдали товаров")
    return by_catalog(rows, ing, words, "sr")


if __name__ == "__main__":
    page = (':product="{&quot;name&quot;:&quot;Mlijeko kravica 2.8% 1 l Imlek&quot;,&quot;regular_price&quot;:&quot;1.19&quot;,'
            '&quot;special_price&quot;:null,&quot;neto_quantity&quot;:1,&quot;quantity_unit&quot;:&quot;l&quot;}"')
    r = cards(page, "u")[0]
    assert r["price"] == 1.19 and r["size"] == 1.0 and r["unit"] == "l", r
    print("voli self-check ok")
