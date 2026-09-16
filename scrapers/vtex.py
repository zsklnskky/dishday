# Витрины на платформе VTEX: открытый каталог /api/catalog_system/pub/products/search?ft=<запрос>.
# Цена - Price первого продавца, фасовка из названия товара («Lapte integral 1 l»), у весовых - measurementUnit.
# Диапазон товаров задаётся _from/_to, поэтому ответ приходит с кодом 206 (частичное содержимое).
import urllib.parse
from common import by_search, get_json, row

HOSTS = {  # id сети -> (хост, язык)
    "auchan_ro": ("www.auchan.ro", "ro"),
}


def parse(d, host):
    out = []
    for p in d:
        for it in p.get("items") or []:
            off = ((it.get("sellers") or [{}])[0].get("commertialOffer") or {})
            price = off.get("Price")
            if not price or not off.get("AvailableQuantity"):
                continue
            r = row(it.get("nameComplete") or p.get("productName") or "", price,
                    url=f"https://{host}/{p.get('linkText', '')}/p")
            mu, mult = (it.get("measurementUnit") or "").lower(), it.get("unitMultiplier") or 0
            if mu in ("kg", "l") and mult > 0:  # весовой товар: цена за unitMultiplier единиц
                r.update(ppu=round(price / mult, 3), unit=mu, size=mult)
            out.append(r)
            break  # у товара берём первый вариант, остальные - те же цены в другой фасовке
    return out


def collect(cc, chain, ing, words):
    host, lang = HOSTS[chain["id"]]

    def search(q):
        url = (f"https://{host}/api/catalog_system/pub/products/search"
               f"?ft={urllib.parse.quote(q)}&_from=0&_to=23")
        return parse(get_json(url, lang=lang), host)

    return by_search(search, ing, words, chain.get("lang") or lang, chain["id"])


if __name__ == "__main__":
    d = [{"productName": "Lapte integral Albalact 1 l", "linkText": "lapte-albalact",
          "items": [{"nameComplete": "Lapte integral Albalact, 3.5% grasime, 1 l", "measurementUnit": "un",
                     "unitMultiplier": 1.0, "sellers": [{"commertialOffer": {"Price": 10.49, "AvailableQuantity": 100}}]}]},
         {"productName": "Rosii", "linkText": "rosii",
          "items": [{"nameComplete": "Rosii vrac", "measurementUnit": "kg", "unitMultiplier": 0.5,
                     "sellers": [{"commertialOffer": {"Price": 6.0, "AvailableQuantity": 20}}]}]},
         {"productName": "Epuizat", "linkText": "x",
          "items": [{"nameComplete": "Epuizat", "sellers": [{"commertialOffer": {"Price": 5.0, "AvailableQuantity": 0}}]}]}]
    r = parse(d, "www.auchan.ro")
    assert len(r) == 2, r
    assert r[0]["size"] == 1.0 and r[0]["unit"] == "l" and r[0]["price"] == 10.49
    assert r[1]["ppu"] == 12.0 and r[1]["unit"] == "kg"  # 0,5 кг за 6 лей
    print("vtex self-check ok")
