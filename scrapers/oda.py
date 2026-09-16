# Oda (NO) - крупнейший онлайн-супермаркет Норвегии. Страница поиска отдаёт React-разметку,
# внутри которой лежат карточки товаров JSON-ом: цена упаковки и цена за литр/кг/штуку от самого магазина.
import re, urllib.parse
from common import by_search, fetch, row

UNIT = {"kg": "kg", "l": "l", "stk": "pc"}
P = re.compile(r'"fullName":"(.*?)".{0,500}?"absoluteUrl":"(.*?)","grossPrice":"([\d.]+)",'
               r'"grossUnitPrice":"([\d.]+)","unitPriceQuantityAbbreviation":"(\w+)"', re.S)


def parse(page):
    page = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), page.replace('\\"', '"'))
    out = []
    for name, url, price, ppu, unit in P.findall(page):
        r = row(name, price, url="https://oda.com" + url)
        if UNIT.get(unit):
            r["ppu"], r["unit"] = float(ppu), UNIT[unit]
        out.append(r)
    return out


def collect(cc, chain, ing, words):
    return by_search(lambda q: parse(fetch("https://oda.com/no/search/?q=" + urllib.parse.quote(q), lang="nb")),
                     ing, words, "no", chain["id"])


if __name__ == "__main__":
    page = (r'\"attributes\":{\"id\":12079,\"fullName\":\"Tine Lettmelk 0,5% fett, 1,75 l\",\"brand\":\"TINE\",'
            r'\"absoluteUrl\":\"/no/products/12079-tine/\",\"grossPrice\":\"29.90\",\"grossUnitPrice\":\"17.09\",'
            r'\"unitPriceQuantityAbbreviation\":\"l\",\"unitPriceQuantityName\":\"liter\"}')
    r = parse(page)[0]
    assert r["price"] == 29.9 and r["ppu"] == 17.09 and r["unit"] == "l" and r["size"] == 1.75, r
    print("oda self-check ok")
