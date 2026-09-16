# Magnum (KZ): публичный API сайта magnum.kz:1337 (Strapi, robots.txt нет). Онлайн-каталога нет, только товары акций
# (~250 наименований по всем городам), поэтому позиций мало и набор меняется каждую неделю. Берём start_price -
# обычную цену до скидки. Названия капсом приводим к обычному виду, «кг» без числа - цена за килограмм.
import json, re
from common import by_search, fetch, row
from green import local

API = "https://magnum.kz:1337/api/products?locale=ru&pagination[pageSize]=500&pagination[page]="


def parse(text):
    d, out = json.loads(text), []
    for x in d.get("data") or []:
        a = x.get("attributes") or {}
        name, price = (a.get("name") or "").strip().capitalize(), a.get("start_price") or a.get("final_price")
        if not (name and price):
            continue
        r = row(name, price, url="https://magnum.kz/catalog")
        if not r["size"] and re.search(r"(?<![\w.])кг(?!\w)", name):
            r.update(ppu=r["price"], unit="kg", size=1.0)
        out.append(r)
    return out, (d.get("meta") or {}).get("pagination", {}).get("pageCount", 1)


def collect(cc, chain, ing, words):
    rows, pages, page = [], 1, 0
    while page < min(pages, 10):
        page += 1
        got, pages = parse(fetch(API + str(page), lang="ru"))
        rows += got
    return by_search(lambda q: local(rows, q), ing, words, "ru", chain["id"])


if __name__ == "__main__":
    sample = json.dumps({"data": [
        {"id": 1, "attributes": {"name": "МОЛОКО «ЛУГОВОЕ ПОЛЕ» 2,5% 900 МЛ", "start_price": 699, "final_price": 499}},
        {"id": 2, "attributes": {"name": "ГОЛЕНЬ КУРИНАЯ КГ", "start_price": 2499, "final_price": 1749}},
        {"id": 3, "attributes": {"name": "МУКА «ДОБРАЯ» 1,9 КГ", "start_price": 719}},
        {"id": 4, "attributes": {"name": "", "start_price": 1}}], "meta": {"pagination": {"pageCount": 3}}})
    (milk, leg, flour), pages = parse(sample)
    assert pages == 3 and milk["name"].startswith("Молоко «луговое") and milk["price"] == 699 and milk["size"] == .9
    assert leg["ppu"] == 2499 and leg["unit"] == "kg" and flour["size"] == 1.9 and not flour["ppu"]
    print("magnum self-check ok")
