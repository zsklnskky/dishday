# SAS (AM) - крупнейшая сеть супермаркетов Армении. Поиск отдаёт готовый HTML: цена упаковки в price__text,
# цена за литр/кг - в card__kg-price ("1 320 դր./1լ"). Фасовку берём из названия (армянские մլ/գ/կգ/հատ).
import html, re, urllib.parse
from common import by_search, fetch, row, to_num

CARD = re.compile(r'class="product__name hidden-sm">([^<]+)<.*?(?:class="price__text">(.*?)<span)'
                  r'(?:.*?class="card__kg-price">(.*?)<span class="price__currency">\s*([^<]+?)\s*</span>)?', re.S)
SIZE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(կգ|գր|գ|մլ|լ|հատ)")


def parse(page):
    out = []
    for card in page.split('class="product-wrap')[1:]:
        m = CARD.search(card)
        if not m or not (m.group(2) or "").strip():
            continue
        name = html.unescape(m.group(1)).strip()
        r = row(name, to_num(m.group(2)), url=None)
        s = SIZE.search(name.replace("\xa0", " "))
        if s:
            v, u = float(s.group(1).replace(",", ".")), s.group(2)
            r["size"], r["unit"] = v * (.001 if u in ("գ", "գր", "մլ") else 1), {"կգ": "kg", "գ": "kg", "գր": "kg", "լ": "l", "մլ": "l", "հատ": "pc"}[u]
        if m.group(3):
            u = m.group(4)
            unit = "kg" if "կգ" in u else "l" if "լ" in u else "pc" if "հատ" in u else None
            if unit:
                r["ppu"], r["unit"] = to_num(m.group(3)), unit
        out.append(r)
    return out


def collect(cc, chain, ing, words):
    return by_search(lambda q: parse(fetch("https://www.sas.am/search?q=" + urllib.parse.quote(q), lang="hy")),
                     ing, words, "hy", chain["id"])


if __name__ == "__main__":
    card = ('class="product-wrap"><div class="product__name hidden-sm">Կաթ «Դիլի» 750մլ, յուղայնությունը` 3.2%</div>'
            '<span class="price__text">990 <span class="price__currency">դր.</span></span>'
            '<span class="card__kg-price">1&nbsp;320<span class="price__currency">դր./1լ</span></span>')
    r = parse(card)[0]
    assert r["price"] == 990 and r["ppu"] == 1320 and r["unit"] == "l" and r["size"] == 0.75, r
    print("sas self-check ok")
