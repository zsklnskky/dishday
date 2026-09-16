# Евроопт (BY): edostavka.by. Поиск (?query=) и листание (?page=) закрыты в robots.txt, поэтому берём дерево
# категорий со страницы /categories, обходим конечные продуктовые категории /category/<id> без параметров
# (товары в __NEXT_DATA__) и ищем по ним сами, как в green.py. measurePrice - цена за кг/л, у весовых basePrice уже за кг.
import json, re
from common import allowed, by_search, fetch, row
from green import local

SITE = "https://edostavka.by"
FOOD = {5138, 5194, 5131, 5185, 5258, 5034, 5199, 5091, 4996}  # овощи, молоко, мясо, рыба, заморозка, крупы, масло, орехи, здоровое
SKIP = re.compile(r"морожен|десерт|сырк|каш|коктейл|чипс|сухарик|попкорн|пицц|пельмен|мант|вареник|наггетс|лёд|хлеб|багет|сдоб|"
                  r"круассан|мюсли|бульон|суп|пюре|напитк|майонез|кетчуп|хрен|аксессуар|бад|протеин|добавк|смузи|печенье|"
                  r"кондитер|клетчатк|урбеч|семена|заменител|закваск|дрожж|крахмал|желатин|паштет|снеки|ягод|фрукт|арбуз|дын|"
                  r"ананас|апельсин|банан|виноград|грейпфрут|груш|киви|лимон|манго|мандарин|персик|яблок|авокадо|икра|"
                  r"клецк|консерв|квашен|солен|семечк|васаби|полуфабрикат|готов|специ|сушен", re.I)  # подмены: соленья, клецки, сушёный чеснок


def data(page):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page, re.S)
    return ((json.loads(m.group(1)) if m else {}).get("props") or {}).get("pageProps") or {}


def leaves(page):
    """Id конечных категорий продуктовых разделов, без повторов и без явно ненужных (мороженое, снеки...)."""
    out = []

    def walk(c):
        kids = c.get("categories") or []
        for k in kids:
            walk(k)
        if not kids and not SKIP.search(c.get("categoryListName") or "") and c["categoryListId"] not in out:
            out.append(c["categoryListId"])
    for top in data(page).get("categories") or []:
        if top.get("categoryListId") in FOOD:
            walk(top)
    return out


def parse(page):
    out = []
    # ponytail: только первая страница категории (?page= запрещён); конечные категории обычно в неё влезают
    for p in (data(page).get("listing") or {}).get("products") or []:
        pr = p.get("price") or {}
        price = float(pr.get("basePrice") or 0)
        if not price:
            continue
        r = row(p.get("productName") or "", price, p.get("packagingInfo") or "", url=f"{SITE}/product/{p.get('productId', '')}")
        nums = re.findall(r"\d+(?:[.,]\d+)?", str(pr.get("measurePrice") or ""))  # "Цена за 1 кг. 16,07" -> последнее число
        measure = float(nums[-1].replace(",", ".")) if nums else 0
        if p.get("soldByWeight") and not measure:
            r.update(ppu=price, unit="kg", size=r["size"] or 1.0)
        elif measure and r["unit"] in ("kg", "l"):
            r["ppu"] = measure
        out.append(r)
    return out


def collect(cc, chain, ing, words):
    urls = [u for u in (f"{SITE}/category/{i}" for i in leaves(fetch(SITE + "/categories", lang="ru"))) if allowed(u)]
    rows = []
    for u in urls:
        for attempt in (1, 2):  # сайт иногда рвёт TLS, один повтор
            try:
                rows += parse(fetch(u, lang="ru"))
                break
            except PermissionError:
                raise
            except Exception as e:  # одна битая категория не роняет сеть
                if attempt == 2:
                    print(f"  {chain['id']} {u}: {type(e).__name__} {e}"[:160], flush=True)
    return by_search(lambda q: first(local(rows, q), q), ing, words, "ru", chain["id"])


def first(rows, q):
    """Если есть товары, чьё название начинается с первого слова запроса, берём только их: «Свекла», а не «Сахар свекловичный»."""
    own = [r for r in rows if r["name"].lower().startswith(q.lower().split()[0][:-1])]
    return own or rows


if __name__ == "__main__":
    def page(pp):
        return '<script id="__NEXT_DATA__" type="application/json">' + json.dumps({"props": {"pageProps": pp}}) + "</script>"
    tree = [{"categoryListId": 5194, "categoryListName": "Молоко, яйца", "categories": [
                {"categoryListId": 5145, "categoryListName": "Яйца", "categories": [
                    {"categoryListId": 1, "categoryListName": "Яйца куриные", "categories": []},
                    {"categoryListId": 2, "categoryListName": "Мороженое, десерты", "categories": []}]}]},
            {"categoryListId": 5258, "categoryListName": "Замороженные", "categories": [
                {"categoryListId": 1, "categoryListName": "Яйца куриные", "categories": []}]},
            {"categoryListId": 5215, "categoryListName": "Зоотовары", "categories": [{"categoryListId": 3, "categoryListName": "Корм", "categories": []}]}]
    assert leaves(page({"categories": tree})) == [1]
    prods = [{"productId": 7, "productName": "Молоко Савушкин 2,5%, 900 мл", "soldByWeight": False, "price": {"basePrice": 2.19, "measurePrice": "Цена за 1 л. 2,43"}},
             {"productId": 8, "productName": "Картофель ранний", "soldByWeight": True, "price": {"basePrice": 1.49, "measurePrice": "0"}},
             {"productId": 9, "productName": "Без цены", "price": {"basePrice": 0}},
             {"productId": 10, "productName": "Яйца куриные С1, ", "packagingInfo": "10 шт", "price": {"basePrice": 3.15, "measurePrice": "0"}}]
    rows = parse(page({"listing": {"products": prods}}))
    assert len(rows) == 3 and rows[2]["size"] == 10 and rows[2]["unit"] == "pc" and rows[0]["ppu"] == 2.43 and rows[0]["size"] == .9 and rows[0]["url"] == SITE + "/product/7"
    assert rows[1]["ppu"] == 1.49 and rows[1]["unit"] == "kg" and rows[1]["size"] == 1.0
    beet = [{"name": "Сахар свекловичный 1 кг"}, {"name": "Свекла 1 кг"}]
    assert first(local(beet, "свекла"), "свекла") == [beet[1]] and first(beet[:1], "свекла") == beet[:1]
    print("euroopt self-check ok")
