# ВкусВилл (RU): поиск отдаёт карточки с ценой в HTML, robots.txt /search/ не закрывает. Регион сайта по умолчанию.
import html, re, urllib.parse
from common import by_search, fetch, row


def parse(page):
    out = []
    for card in page.split('class="ProductCard ')[1:]:
        t = re.search(r'title="([^"]+)"', card)
        p = re.search(r'js-datalayer-catalog-list-price hidden">([\d.,]+)<', card)
        u = re.search(r"</span></span>(/[^<\s]+)", card)
        h = re.search(r'href="(/goods/[^"]+)"', card)
        if not (t and p):
            continue
        r = row(html.unescape(t.group(1)), float(p.group(1).replace(",", ".")), url="https://vkusvill.ru" + h.group(1) if h else None)
        if u and u.group(1) == "/кг":
            r.update(ppu=r["price"], unit="kg", size=r["size"] or 1.0)
        out.append(r)
    return out


def collect(cc, chain, ing, words):
    return by_search(lambda q: parse(fetch("https://vkusvill.ru/search/?type=products&q=" + urllib.parse.quote(q), lang="ru")),
                     ing, words, "ru", chain["id"])
