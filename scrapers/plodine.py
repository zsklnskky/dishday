# Plodine (HR): полного интернет-каталога нет, берём страницы акций недели (карточки в HTML: название, бренд, фасовка, цена).
# Полный дневной прайс (cjenici_*.zip) весит ~65 МБ - слишком тяжело для ежедневного сбора. Только акции.
import html, re
from common import by_catalog, fetch, row, to_num

HOME = "https://www.plodine.hr/"
_PAGES = re.compile(r"https://www\.plodine\.hr/akcije/\d+/[\w/-]+")
_TXT = lambda cls, c: (m := re.search(rf'class="card__{cls}">\s*(.*?)\s*<', c, re.S)) and html.unescape(m.group(1)) or ""


def parse(page, url):
    out = {}
    for card in page.split('<article class="card')[1:]:
        price = re.search(r'class="regular">\s*<strong>\s*([\d.,]+)\s*</strong>', card)
        pid = re.search(r'data-list-add="(\d+)"', card)
        if price and _TXT("title", card):
            name = " ".join(filter(None, (_TXT("title", card), _TXT("description", card))))
            out[pid.group(1) if pid else name] = row(name, to_num(price.group(1)), _TXT("quantity", card), url=url)
    return out


def collect(cc, chain, ing, words):
    rows = {}
    for url in sorted(set(_PAGES.findall(fetch(HOME, lang="hr")))):
        rows.update(parse(fetch(url, lang="hr"), url))
    return by_catalog(list(rows.values()), ing, words, "hr")


if __name__ == "__main__":
    card = ('<article class="card card--01"><a href="#" data-list-add="75400"></a><h2 class="card__title">Orah jezgra</h2>'
            '<p class="card__description">Oho!</p> <p class="card__quantity">500 g</p><p class="regular"> <strong>3,49</strong> € </p>'
            '<p class="discount"><span>prije</span>4,99 €</p></article>')
    r = parse(card, "u")["75400"]
    assert r["name"] == "Orah jezgra Oho! 500 g" and r["price"] == 3.49 and r["size"] == 0.5 and r["unit"] == "kg", r
    print("plodine self-check ok")
