# Сільпо (UA): открытый JSON витрины sf-ecom-api.silpo.ua, филиал по умолчанию (нулевой uuid).
# weighted=true - price уже за кг; иначе price за упаковку, её размер в displayRatio ("900г", "10шт", "0,3кг").
import urllib.parse
from common import by_search, get_json, pack, row

API = ("https://sf-ecom-api.silpo.ua/v1/uk/branches/00000000-0000-0000-0000-000000000000"
       "/products?limit=40&offset=0&search=")


def parse(d):
    out = []
    for it in d.get("items", []):
        price = it.get("price")
        if not price:
            continue
        r = row(it.get("title") or "", price, url="https://silpo.ua/product/" + (it.get("slug") or ""))
        p = pack(it.get("displayRatio") or "")
        if it.get("weighted"):
            r.update(ppu=float(price), unit="kg", size=1.0)
        elif p:
            r["size"], r["unit"] = p
        out.append(r)
    return out


def collect(cc, chain, ing, words):
    return by_search(lambda q: parse(get_json(API + urllib.parse.quote(q), lang="uk")), ing, words, "uk", chain["id"])


if __name__ == "__main__":
    d = {"items": [{"title": "Молоко «Галичина» «З чистих Карпат» 2,5%", "price": 69.49, "displayRatio": "900г", "weighted": False, "slug": "m"},
                   {"title": "Картопля біла мита", "price": 36.49, "displayRatio": "100г", "weighted": True, "slug": "k"},
                   {"title": "Яйця курячі «Ясенсвіт» С1", "price": 80.84, "displayRatio": "10шт", "weighted": False, "slug": "e"}]}
    m, k, e = parse(d)
    assert (m["size"], m["unit"], m["ppu"]) == (0.9, "kg", None)
    assert (k["ppu"], k["unit"]) == (36.49, "kg")
    assert (e["size"], e["unit"]) == (10, "pc")
    print("silpo self-check ok")
