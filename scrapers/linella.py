# Linella (MD): страницы категорий отдают карточки товаров прямо в HTML (поиск на сайте рисуется скриптом,
# поэтому идём по категориям). Цена в леях за упаковку: __static - обычная, __new - по акции (__old зачёркнута).
# Вес/объём стоит в конце названия ("Lapte UHT 2.5%, 900ml").
import html, re
from common import by_catalog, fetch, row

CATS = ["carne", "carne_de_pui", "carne_tocata", "mezeluri", "carnati", "peste_proaspat", "congelate_din_peste",
        "fructe_de_mare", "lapte", "chefir", "iaurturi", "smantana", "branza_proaspata", "branzeturi", "cascaval",
        "crema_de_branza", "unt_i_margarina", "oua", "legume", "fructe", "legume_congelate", "ciuperci",
        "salate_i_verdeturi", "orez", "hrisca", "paste", "crupe-si-boboase", "linte", "naut_", "couscous", "arpacas",
        "crupe_de_gris", "malai", "cereale_i_fulgi_de_ovaz", "faina", "zahar", "otet_i_ulei", "masline_",
        "mazare", "fasole", "miere_i_gem_i_dulceturi", "nuci",
        "maioneza__ketchup__sosuri", "seminte", "paine", "sare", "frisca_i_lapte_condensat"]
# ponytail: консервы и специи из списка убраны - "Rosii tocate" ловилось как фарш, "Usturoi granulat" как чеснок,
# а покрытых ими позиций ING в румынском словаре нет.
ITEM = re.compile(r'<a href="([^"]+)" class="products-catalog-content__name">(.*?)</a>.*?'
                  r'price-products-catalog-content__(?:static|new)">\s*([\d.,]+)', re.S)


def parse(page):
    out = []
    for card in page.split("products-catalog-content__item")[1:]:
        m = ITEM.search(card)
        if m:
            out.append(row(html.unescape(m.group(2)).strip(), float(m.group(3).replace(",", ".")),
                           url="https://linella.md" + m.group(1).split("?")[0]))
    return out


def collect(cc, chain, ing, words):
    rows = []
    for c in CATS:
        try:
            rows += parse(fetch("https://linella.md/ro/catalog/" + c, lang="ro"))
        except Exception as e:
            print(f"  linella {c}: {type(e).__name__} {e}"[:120], flush=True)
    return by_catalog(rows, ing, words, "ro")


if __name__ == "__main__":
    page = ('<div class="products-catalog-content__item" data-SKU="1">'
            '<a href="/ro/catalog/lapte/ferma_lapte?from=CATALOGUE" class="products-catalog-content__name">'
            'ФЕРМА Lapte UHT 2.5%, 900ml</a><div class="price-products-catalog-content__main">'
            '<span class="price-products-catalog-content__static"> 25.79 </span></div></div>'
            '<div class="products-catalog-content__item" data-SKU="2">'
            '<a href="/ro/catalog/oua/oua_l" class="products-catalog-content__name">GUSTOVO Oua de gaina brune L 10 buc</a>'
            '<span class="price-products-catalog-content__old"> 55.00 </span>'
            '<span class="price-products-catalog-content__new"> 48.29 </span></div>')
    a, b = parse(page)
    assert (a["price"], a["size"], a["unit"]) == (25.79, 0.9, "l")
    assert (b["price"], b["size"], b["unit"]) == (48.29, 10, "pc")
    print("linella self-check ok")
