# ВкусВилл (RU): robots.txt закрывает */?* - поиск и пагинация (?PAGEN) недоступны. Берём первые страницы
# продуктовых подкатегорий /goods/<раздел>/<подраздел>/ (по 24 карточки с ценой в HTML) и подбираем товар по ним
# через local из green. Регион сайта по умолчанию.
import html, re
from common import allowed, by_search, fetch, row
from green import local

SITE = "https://vkusvill.ru/goods/"
CATS = {"myaso-ptitsa": "kuritsa okorochok farsh govyadina-i-telyatina svinina indeyka myaso-dlya-zapekaniya steyki",
        "kolbasa-sosiski-delikatesy": "bekon-i-salo sosiski-i-sardelki myasnye-sneki-i-kolbaski",
        "ryba-ikra-i-moreprodukty": "treska semga forel krevetki kalmar ryba-i-moreprodukty-okhlazhdennye ryba-zamorozhennaya",
        "molochnye-produkty-yaytso": "yaytso moloko-slivki-sgushchyenka kefir-i-kislomolochnye-produkty yogurty smetana tvorog maslo-slivochnoe slivki-33",
        "syry": "tverdye-i-polutverdye mocarella parmezan brynza suluguni feta-motsarella-i-drugie-myagkie tvorozhnye-i-plavlenye-syry tofu-i-postnye-syry",
        "ovoshchi-frukty-yagody-zelen": "ovoshchi molodye-ovoshchi griby-shampinony griby frukty zelen-i-salaty zamorozhennye-ovoshchi-i-frukty orekhi-i-sukhofrukty",
        "krupy-makarony-muka": "krupy makarony makarony-vitki dlya-pasty gorokh-krupa muka-i-ingredienty-dlya-vypechki sukhie-zavtraki-khlopya-i-myusli",
        "masla-sousy-spetsii-sakhar-i-sol": "rastitelnye-masla sousy-i-uksus spetsii sakhar-zameniteli-i-siropy",
        "konservy-myed-i-varene": "tomatnaya-pasta myed goroshek-kukuruza-fasol",
        "orekhi-chipsy-i-sneki": "orekhi sukhofrukty semechki-i-semena"}


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
    rows = []
    for top, subs in CATS.items():
        for sub in subs.split():
            url = f"{SITE}{top}/{sub}/"
            if not allowed(url):
                continue
            try:
                rows += parse(fetch(url, lang="ru"))
            except Exception as e:
                print(f"  vkusvill {sub}: {type(e).__name__} {e}"[:120], flush=True)
    if not rows:
        raise RuntimeError("категории ВкусВилл не отдали товаров")
    uniq = {r["url"] or r["name"]: r for r in rows}  # товар бывает в нескольких подразделах
    return by_search(lambda q: local(list(uniq.values()), q), ing, words, "ru", chain["id"])


if __name__ == "__main__":
    page = ('<div class="ProductCard js-product-cart"><a href="/goods/file-grudki-488/" title="Филе грудки цыпленка-бройлера">'
            '<span class="js-datalayer-catalog-list-price hidden">645</span><span><span>645</span></span>/кг</div>'
            '<div class="ProductCard x"><a href="/goods/moloko-1/" title="Молоко 2,5%, 900 мл">'
            '<span class="js-datalayer-catalog-list-price hidden">99.5</span><span><span>99</span></span>/шт</div>')
    a, b = parse(page)
    assert (a["ppu"], a["unit"], a["url"]) == (645.0, "kg", "https://vkusvill.ru/goods/file-grudki-488/"), a
    assert (b["price"], b["size"], b["unit"], b["ppu"]) == (99.5, .9, "l", None), b
    print("vkusvill self-check ok")
