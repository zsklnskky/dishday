# Auchan (PT): поиск auchan.pt, у каждой плитки товара атрибут data-gtm с названием (с фасовкой) и ценой. Цены онлайн-магазина.
import html, json, re, urllib.parse
from common import by_search, fetch, row


def parse(page):
    out = []
    for m in re.finditer(r'data-urls="([^"]*)"\s+data-gtm="([^"]*)"', page):
        try:
            urls, g = json.loads(html.unescape(m.group(1))), json.loads(html.unescape(m.group(2)))
        except ValueError:
            continue
        if g.get("price"):
            out.append(row(g["name"].title(), float(g["price"]), url=urls.get("absoluteProductUrl")))
    return out


def collect(cc, chain, ing, words):
    return by_search(lambda q: parse(fetch("https://www.auchan.pt/pt/pesquisa?q=" + urllib.parse.quote(q), lang="pt")),
                     ing, words, "pt", chain["id"])


if __name__ == "__main__":
    t = 'data-urls="{&quot;absoluteProductUrl&quot;:&quot;https://www.auchan.pt/p/1.html&quot;}" data-gtm="{&quot;name&quot;:&quot;LEITE UHT AUCHAN MEIO GORDO 1L&quot;,&quot;price&quot;:&quot;0.85&quot;}"'
    r = parse(t)[0]
    assert r["price"] == 0.85 and r["size"] == 1.0 and r["unit"] == "l" and r["url"].endswith("1.html"), r
    print("auchan_pt self-check ok")
