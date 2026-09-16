# My Market (GR, сеть Metro AEBE): поиск (/*?*query=*) закрыт в robots.txt. Обходим продуктовые категории
# https://www.mymarket.gr/<slug> (HTML, карточки товаров; дальше ?page=N из пагинации, пока хватает лимита страниц)
# и подбираем товар по скачанным строкам через local из green. В карточках: JSON для аналитики (имя, цена) и цена за кг/л/шт («Τιμή κιλού»). Цены доставки по умолчанию.
import html, json, re
from collections import deque
from common import allowed, by_search, fetch, row, to_num
from green import local

SITE = "https://www.mymarket.gr/"
CATS = """moschari choirino arni kotopoulo galopoula kimas mpeikon loukanika psaria thalassina solomos tonos-sardeles
avga gala giaourti straggisto kaseri-kitrina-tyria feta-lefka-tyria mozzarella-chaloumi parmezana-regato kremodi-aleifomena
voutyro kremes-galaktos zacharoucho patates-skorda-kremmydia karota-rapanakia-tzintzer lachano-kounoupidi-mprokolo
piperies-melitzanes-kolokythia tomates-tomatinia-aggouria chorta-spanaki-pantzaria fasolakia-mpamies-koukia
myrodika-aromatika-fyta lemonia-laims mila rodia-kydonia ananas-avokanto-exotika-frouta ryzi makaronia fakes fava-revythia
simigdali alevri muesli-vromi psomi-tou-tost elies tomatoeidi xydi elaiolado sporelaio xiroi-karpoi meli zachari kakao
zelatini-aromatika moustarda magioneza ketsap alati aromata piperi""".split()
MAX_PAGES = 60

UNIT = {"κιλού": "kg", "λίτρου": "l", "τεμαχίου": "pc"}
_ITEM = re.compile(r'data-google-analytics-item-param="(\{.*?\})"', re.S)
_MEASURE = re.compile(r'font-semibold">\s*([\d.,]+)\s*€\s*</span>\s*<span>\s*Τιμή\s+(\S+?)\s*</span>', re.S)


def parse(page):
    """HTML категории или JSON {"commands":[{"html": ...}]} - сайт отдаёт то одно, то другое."""
    if page.lstrip().startswith("{"):
        page = "".join(c.get("html") or "" for c in json.loads(page).get("commands", []))
    out = []
    for card in page.split("product--teaser")[1:]:
        m = _ITEM.search(card)
        if not m:
            continue
        p = json.loads(html.unescape(m.group(1)))
        if not p.get("price") or not p.get("name"):
            continue
        href = re.search(r'href="(https://www\.mymarket\.gr/[^"]+)"', card)
        r = row(p["name"], to_num(p["price"]), url=href.group(1) if href else None)
        mu = _MEASURE.search(card)
        if mu and UNIT.get(mu.group(2)):
            r["ppu"], r["unit"] = to_num(mu.group(1)), UNIT[mu.group(2)]
        out.append(r)
    return out


def pages(page, slug):
    return sorted({int(n) for n in re.findall(r'href="' + re.escape(SITE + slug) + r'\?page=(\d+)"', page)} - {1})


def collect(cc, chain, ing, words):
    rows, queue, seen = [], deque((c, SITE + c) for c in CATS), set()
    while queue and len(seen) < MAX_PAGES:
        slug, url = queue.popleft()
        if url in seen or not allowed(url):
            continue
        seen.add(url)
        try:
            page = fetch(url, lang="el")
        except Exception as e:
            print(f"  mymarket {slug}: {type(e).__name__} {e}"[:120], flush=True)
            continue
        rows += parse(page)
        if "?" not in url:  # следующие страницы - в конец очереди, после первых страниц всех категорий
            queue += [(slug, f"{SITE}{slug}?page={n}") for n in pages(page, slug)]
    if not rows:
        raise RuntimeError("категории My Market не отдали товаров")
    uniq = list({r["url"] or r["name"]: r for r in rows}.values())
    return by_search(lambda q: local(uniq, q), ing, words, "el", chain["id"])


if __name__ == "__main__":
    card = ('{"commands":[{"html":"<div class=\\"not-prose product--teaser\\"><a href=\\"https://www.mymarket.gr/noynoy-gala\\" '
            'data-google-analytics-item-param=\\"{&quot;name&quot;:&quot;\\u039d\\u039f\\u03a5\\u039d\\u039f\\u03a5 '
            '\\u0393\\u03ac\\u03bb\\u03b1 1lt&quot;,&quot;price&quot;:&quot;1.98&quot;}\\">x</a>'
            '<div class=\\"measure-label-wrapper\\"><span class=\\"font-semibold\\">1,98\\u20ac</span> '
            '<span>\\u03a4\\u03b9\\u03bc\\u03ae \\u03bb\\u03af\\u03c4\\u03c1\\u03bf\\u03c5</span></div></div>"}]}')
    r = parse(card)[0]
    assert parse(json.loads(card)["commands"][0]["html"]) == [r]
    assert r["price"] == 1.98 and r["ppu"] == 1.98 and r["unit"] == "l", r
    assert pages('<a href="https://www.mymarket.gr/moschari?page=2">2</a><a href="https://www.mymarket.gr/moschari?page=3">', "moschari") == [2, 3]
    print("mymarket self-check ok")
