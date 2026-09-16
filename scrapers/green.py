# Green (BY): green-dostavka.by. Поиск /search/ закрыт в robots.txt, поэтому берём категории второго уровня
# продуктовых разделов (в __NEXT_DATA__ по 10 товаров на подкатегорию) и ищем по ним сами, как поиск сайта.
# Цены в копейках, весовой товар - за кг.
import json, re
from common import by_search, fetch, row

SITE = "https://green-dostavka.by"
FOOD = ("molochnye-produkty-syr-yajca", "myaso-ptica-myasnaya-gastronomiya", "ovoshi-frukty-griby-zelen-yagody",
        "ryba-ikra-moreprodukty", "makarony-krupy-muka", "masla-specii-sahar", "hlebobulochnye-izdeliya", "konservaciya-i-sousy")


def state(page):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page, re.S)
    return json.loads(m.group(1))["props"]["initialState"] if m else ""


def parse(page):
    s, dec, out = state(page), json.JSONDecoder(), []
    for m in re.finditer(r'\{"skip"', s):
        for p in dec.raw_decode(s, m.start())[0].get("items") or []:
            price = ((p.get("storeProduct") or {}).get("price") or 0) / 100
            if not price:
                continue
            r = row(p.get("title") or "", price, "" if p.get("unit") == "weight" else p.get("volume") or "", url=f"{SITE}/product/{p.get('slug', '')}/")
            if p.get("unit") == "weight":  # цена весового товара - за килограмм
                r.update(ppu=price, unit="kg", size=1.0)
            out.append(r)
    return out


def subcats(page):
    paths = set(re.findall(r'\["path","(/catalog/([^/"]+)/[^/"]+/)"\]', state(page)))
    return sorted(p for p, top in paths if top in FOOD)


def local(rows, q):
    """Поиск по скачанным строкам: все слова запроса (по 4 буквы с начала слова), иначе первое слово целиком."""
    ws, low = q.lower().split(), [(r, " " + r["name"].lower()) for r in rows]
    hit = [r for r, n in low if all(re.search(r"(?<!\w)" + re.escape(w[:4]), n) for w in ws)]
    return hit or [r for r, n in low if re.search(r"(?<!\w)" + re.escape(ws[0]) + r"(?!\w)", n)]


def collect(cc, chain, ing, words):
    rows = [r for p in subcats(fetch(SITE + "/catalog/", lang="ru")) for r in parse(fetch(SITE + p, lang="ru"))]
    return by_search(lambda q: local(rows, q), ing, words, "ru", chain["id"])


if __name__ == "__main__":
    items = [{"title": "Картофель ранний свежий вес", "unit": "weight", "volume": "фасовка:0,8-1кг", "slug": "k", "storeProduct": {"price": 79}},
             {"title": "Молоко Местное известное 3,2%", "unit": "piece", "volume": "900мл", "slug": "m", "storeProduct": {"price": 199}},
             {"title": "Без цены", "unit": "piece", "volume": "1л", "storeProduct": None}]
    tree = '["path","/catalog/ovoshi-frukty-griby-zelen-yagody/ovoshi/"],["path","/catalog/avtotovary/avtokosmetika/"],["path","/catalog/ovoshi-frukty-griby-zelen-yagody/ovoshi/kartofel/"]'
    st = json.dumps({"skip": 0, "limit": 10, "items": items}) + tree
    page = '<script id="__NEXT_DATA__" type="application/json">' + json.dumps({"props": {"initialState": st}}) + "</script>"
    rows = parse(page)
    assert len(rows) == 2 and rows[0]["ppu"] == .79 and rows[0]["unit"] == "kg"
    assert rows[1]["price"] == 1.99 and rows[1]["size"] == .9 and rows[1]["unit"] == "l"
    assert subcats(page) == ["/catalog/ovoshi-frukty-griby-zelen-yagody/ovoshi/"]
    eggs = [{"name": n} for n in ("Яйца перепелиные 20 шт", "Яйца куриные С-1 10 шт", "Колбаса сыровяленая", "Сыр Гауда")]
    assert [r["name"] for r in local(eggs, "яйца куриные")] == ["Яйца куриные С-1 10 шт"]
    assert [r["name"] for r in local(eggs, "сыр российский")] == ["Сыр Гауда"]
    print("green self-check ok")
