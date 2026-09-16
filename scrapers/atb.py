# АТБ (UA): поиск /sch закрыт в robots.txt, разрешены /catalog/* - обходим продуктовые категории (по 36 карточек,
# дальше ?page=N из пагинации) и подбираем товар по скачанным строкам через local из green. Текущая цена - <data value> в product-price__top
# (product-price__bottom - старая цена до скидки). Единица в product-price__unit: /кг - цена уже за килограмм,
# /шт - цена упаковки, её размер стоит в названии ("Молоко 0,9 кг Своя Лінія").
import html, re
from common import allowed, by_search, fetch, row
from green import local

SITE = "https://www.atbmarket.com"
CATS = ("maso", "344-m-yaso-okholodzhene", "421-m-yasni-napivfabrikati", "kovbasa", "377-sosiski-sardel-ki", "riba",
        "353-riba-i-moreprodukti", "moreprodukti", "381-yaytsya-kuryachi-perepelini", "398-moloko", "316-kislomolochni-napoi",
        "349-yogurti", "329-smetana", "379-sir-kislomolochniy", "433-siri-tverdi", "402-siri-m-yaki", "siri",
        "414-maslo-i-margarin", "399-vershki", "289-ovochi", "288-frukti-yagodi", "298-gribi", "390-zelen",
        "452-ovochi-ta-frukti-svizhozamorozheni", "395-krupi", "348-makaronni-virobi", "341-boroshno", "312-tsukor",
        "olia-ta-ocet", "365-sousi-ketchupi", "305-pripravi-ta-marinadi", "446-gorikhi-sukhofrukti", "dzem-pasta-med",
        "415-yapons-ka-kukhnya", "416-vasabi-imbir-otset", "378-sukhi-snidanki", "386-kashi")
MAX_PAGES = 60

CARD = re.compile(r'catalog-item__title[^>]*>\s*<a href="([^"]+)"[^>]*>(.*?)</a>.*?'
                  r'<data value="([\d.]+)" class="product-price__top".*?product-price__unit">/(\w+)<', re.S)


def parse(page):
    out = []
    for card in page.split("<article")[1:]:
        m = CARD.search(card)
        if not m:
            continue
        r = row(html.unescape(re.sub(r"<[^>]+>", " ", m.group(2))).strip(), float(m.group(3)),
                url="https://www.atbmarket.com" + m.group(1))
        if m.group(4) == "кг":
            r.update(ppu=float(m.group(3)), unit="kg", size=r["size"] or 1.0)
        out.append(r)
    return out


def pages(page, cat):
    """Номера следующих страниц категории из пагинации."""
    return sorted({int(n) for n in re.findall(r'href="/catalog/' + re.escape(cat) + r'\?page=(\d+)"', page)} - {1})


def collect(cc, chain, ing, words):
    rows, left = [], MAX_PAGES
    for c in CATS:
        urls = [f"{SITE}/catalog/{c}"]
        while urls and left > 0:
            url, left = urls.pop(0), left - 1
            if not allowed(url):
                continue
            try:
                page = fetch(url, lang="uk")
            except Exception as e:
                print(f"  atb {c}: {type(e).__name__} {e}"[:120], flush=True)
                break
            rows += parse(page)
            if "?" not in url:
                urls += [f"{SITE}/catalog/{c}?page={n}" for n in pages(page, c)]
    if not rows:
        raise RuntimeError("категории АТБ не отдали товаров")
    return by_search(lambda q: local(rows, q), ing, words, "uk", chain["id"])


if __name__ == "__main__":
    page = ('<article class="catalog-item"><div class="catalog-item__title wbh-55">'
            '<a href="/product/moloko">Молоко 0,9 кг Своя Лінія ультрапастеризоване 1% </a></div>'
            '<div class="catalog-item__bottom"><div class="catalog-item__product-price product-price">'
            '<data value="37.80" class="product-price__top"><span>37.<span>80</span></span>'
            '<abbr title="Гривня">грн<span class="product-price__unit">/шт</span></abbr></data>'
            '<data value="45.20" class="product-price__bottom"></data></div></div></article>'
            '<article class="catalog-item"><div class="catalog-item__title">'
            '<a href="/product/kartopla">Картопля мита вагова</a></div>'
            '<data value="26.90" class="product-price__top"><abbr>грн<span class="product-price__unit">/кг</span></abbr></data></article>')
    a, b = parse(page)
    assert (a["price"], a["size"], a["unit"], a["ppu"]) == (37.8, 0.9, "kg", None)
    assert (b["ppu"], b["unit"]) == (26.9, "kg")
    nav = '<a href="/catalog/395-krupi?">1</a><a href="/catalog/395-krupi?page=2">2</a><a href="/catalog/395-krupi?page=2">&gt;</a>'
    assert pages(nav, "395-krupi") == [2]
    print("atb self-check ok")
