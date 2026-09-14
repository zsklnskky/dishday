# Магнит (RU): страницы категорий отдают schema.org OfferCatalog. Поиск закрыт robots.txt - только категории.
# Цена магазина по умолчанию (shopCode 992301, Краснодар). Первые ~25 товаров категории.
import json, re
from common import by_catalog, fetch, row

CATS = ["64201-testmmmyaso_i_ptitsa", "64245-testmmptitsa", "64247-testmmmyaso", "114429-govyadina_copy", "64203-testmmryba",
        "114415-moreprodukty_copy_1", "63983-testmmmoloko_maslo_yaytsa", "63991-testmmsyry", "64063-testmmkislomolochnye_napitki",
        "114462-smetana_copy", "64041-testmmmaslo_i_margarin", "63921-testmmovoshchi_griby_zelen", "63905-testmmovoshchi_i_frukty",
        "64473-testmmzamorozka_ovoshchi_i_yagody", "64123-testmmkrupy_i_sukhie_zavtraki", "117416-krupy_copy", "114259-makarony_copy",
        "114439-muka_copy", "64121-testmmbakaleya", "64129-testmmsakhar_sol_i_spetsii", "107240-podsolnechnoe_maslo_copy",
        "114445-olivkovoe_copy", "64199-testmmkonservy", "64719-testmmsukhofrukty_i_orekhi"]


def collect(cc, chain, ing, words):
    rows = []
    for c in CATS:
        url = "https://magnit.ru/catalog/" + c
        m = re.search(r'id="offer-catalog-jsonld">(.*?)</script>', fetch(url, lang="ru"), re.S)
        for it in (json.loads(m.group(1)).get("itemListElement", []) if m else []):
            r = row(it["name"], it["price"], url=it.get("url") or url)
            if not r["size"]:
                # ponytail: без фасовки в названии у Магнита весовой товар, цена за кг; окно pick() отсекает промахи
                r.update(size=1.0, unit="kg", ppu=float(it["price"]))
            rows.append(r)
    return by_catalog(rows, ing, words, "ru")
