# REMA 1000 (DK) - сеть №1 по числу магазинов в Дании. Публичный JSON её приложения отдаёт цену упаковки
# и сравнительную цену за литр/кг (compare_unit_price). Поиска в этом API нет: параметр запроса игнорируется,
# ответ один и тот же, поэтому забираем весь каталог постранично (сейчас 39 страниц по 100 товаров)
# и подбираем товары по нему. Названия в базе капсом, фасовка - в поле underline ("1 LTR. / ARLA").
from common import by_catalog, get_json, row

UNIT = {"ltr": "l", "kg": "kg", "stk": "pc"}
PER_PAGE = 100


def parse(d):
    out = []
    for p in d.get("data") or []:
        pr = (p.get("prices") or [{}])[0]
        if not pr.get("price"):
            continue
        # капс мешает найти сам продукт в первых словах названия (common.head отбрасывает слова капсом)
        r = row(p.get("name", "").capitalize(), pr["price"], p.get("underline", ""),
                url=f"https://shop.rema1000.dk/varer/{p.get('id')}")
        u = UNIT.get((pr.get("compare_unit") or "").lower())
        if u and pr.get("compare_unit_price"):
            r["ppu"], r["unit"] = pr["compare_unit_price"], u
        out.append(r)
    return out


def catalog(limit=60):
    rows, page, last = [], 1, 1
    while page <= min(last, limit):
        d = get_json(f"https://api.digital.rema1000.dk/api/v3/products?per_page={PER_PAGE}&page={page}", lang="da")
        rows += parse(d)
        last = d.get("meta", {}).get("pagination", {}).get("last_page") or 1
        page += 1
    return rows


def collect(cc, chain, ing, words):
    return by_catalog(catalog(), ing, words, "da")


if __name__ == "__main__":
    d = {"data": [{"id": 100028, "name": "MINIMÆLK", "underline": "1 LTR. / ARLA",
                   "prices": [{"price": 12.5, "compare_unit": "ltr", "compare_unit_price": 12.5}]}]}
    r = parse(d)[0]
    assert r["price"] == 12.5 and r["ppu"] == 12.5 and r["unit"] == "l" and r["size"] == 1.0, r
    print("rema1000_dk self-check ok")
