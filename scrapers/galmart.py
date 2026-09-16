# Galmart (KZ): JSON-поиск сайта /api/v2/catalog/goods/ (в robots.txt закрыт только /catalog/search). Город по умолчанию.
# У весовых (unit "кг") price - за кг, unit_price - за фасовку unit_value кг. Берём обычную цену: old_price, если идёт акция.
import json, urllib.parse
from common import by_search, fetch, row

SITE = "https://galmart.kz"


def parse(text):
    out = []
    for g in json.loads(text).get("data") or []:
        title = (g.get("title") or "").strip()
        title = title.capitalize() if title.isupper() else title  # «МОЛОКО ОВС» иначе целиком сочтётся брендом
        price = float(g.get("old_price") or g.get("price") or 0)
        if not price or not g.get("available", True):
            continue
        if g.get("unit") == "кг":
            size = float(g.get("unit_value") or 1)
            r = row(title, price * size, url=f"{SITE}/product/{g.get('id')}")
            r.update(ppu=price, unit="kg", size=size)
        else:
            r = row(title, price, url=f"{SITE}/product/{g.get('id')}")
        out.append(r)
    return out


def collect(cc, chain, ing, words):
    url = SITE + "/api/v2/catalog/goods/?page=1&limit=24&ordering=popular&search="
    return by_search(lambda q: parse(fetch(url + urllib.parse.quote(q), lang="ru")), ing, words, "ru", chain["id"])


if __name__ == "__main__":
    sample = json.dumps({"data": [
        {"id": 1, "title": "Картофель, вес, Казахстан", "unit": "кг", "unit_value": 1.5, "price": 275.0, "old_price": None, "available": True},
        {"id": 2, "title": "МОЛОКО ДЕПОВСКОЕ 2,5% 1000МЛ", "unit": "шт", "unit_value": 1.0, "price": 600.0, "old_price": 680.0, "available": True},
        {"id": 3, "title": "Нет в наличии 1 л", "unit": "шт", "price": 100.0, "available": False}]})
    a, b = parse(sample)
    assert a["ppu"] == 275 and a["unit"] == "kg" and a["size"] == 1.5 and a["price"] == 412.5
    assert b["name"].startswith("Молоко деповское") and b["price"] == 680 and b["size"] == 1.0 and b["unit"] == "l"
    print("galmart self-check ok")
