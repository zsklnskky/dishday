# Tuš (SI): сайт показывает только товары в акции. Поиск tus.si/?s=&post_type=product отдаёт карточки в HTML,
# имя, цена и адрес - в data-gtm4wp_*. Акция «Mojih 10» - личная скидка по карте, для неё берём обычную цену («Redna cena»).
import html, re, urllib.parse
from common import by_search, fetch, row, to_num

_GTM = re.compile(r'data-gtm4wp_product_name="([^"]*)" data-gtm4wp_product_price="([\d.]+)".*?data-gtm4wp_product_url="([^"]*)"', re.S)


def parse(page):
    out = []
    for card in page.split('class="card card-product')[1:]:
        m = _GTM.search(card)
        if not m:
            continue
        price = float(m.group(2))
        regular = re.search(r"Redna cena:\s*([\d.,]+)", card)
        if "m10-activate" in card and regular:
            price = to_num(regular.group(1))
        out.append(row(html.unescape(m.group(1)), price, url=m.group(3)))
    return out


def collect(cc, chain, ing, words):
    url = "https://www.tus.si/?post_type=product&s="
    return by_search(lambda q: parse(fetch(url + urllib.parse.quote(q), lang="sl")), ing, words, "sl", chain["id"])


if __name__ == "__main__":
    card = ('<div class="card card-product product"><a class="btn green m10-activate">x</a><span class="price">0,99 € </span>'
            '<label>Redna cena: 1,29 € </label><span class="gtm4wp_productdata" data-gtm4wp_product_id="1" '
            'data-gtm4wp_product_name="Planinsko mleko Tuš, 3,5 % m. m., 1 l" data-gtm4wp_product_price="0.99" '
            'data-gtm4wp_product_cat="" data-gtm4wp_product_url="https://www.tus.si/izdelki/mleko/"></span>'
            '<div class="card card-product product"><span class="gtm4wp_productdata" data-gtm4wp_product_name="Maslo Tuš, 250 g" '
            'data-gtm4wp_product_price="2.49" data-gtm4wp_product_url="u"></span>')
    a, b = parse(card)
    assert a["price"] == 1.29 and a["size"] == 1.0 and a["unit"] == "l" and a["url"].endswith("/mleko/"), a
    assert b["price"] == 2.49 and b["size"] == 0.25 and b["unit"] == "kg", b
    print("tus self-check ok")
