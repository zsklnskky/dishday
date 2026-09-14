# Разведка: какие каталоги сетей отвечают с серверов GitHub и что разрешает robots.txt.
# Ничего не обходит: один GET на адрес, честный User-Agent, пауза. Итог - таблица в лог.
# Запуск: python scrapers/probe.py
import re, sys, time, urllib.parse
import common
from common import allowed, fetch

C = [  # (страна, сеть, адрес)
    ("BY", "euroopt", "https://edostavka.by/search?query=молоко"),
    ("RU", "magnit", "https://magnit.ru/catalog/63983-testmmmoloko_maslo_yaytsa"),
    ("RU", "vkusvill", "https://vkusvill.ru/search/?type=products&q=молоко"),
    ("RU", "lenta", "https://lenta.com/search/?searchText=молоко"),
    ("RU", "perekrestok", "https://www.perekrestok.ru/cat/search?search=молоко"),
    ("RU", "metro", "https://online.metro-cc.ru/search?q=молоко"),
    ("RU", "okey", "https://www.okeydostavka.ru/spb/search?q=молоко"),
    ("RU", "globus", "https://online.globus.ru/search/?q=молоко"),
    ("DE", "kaufland", "https://filiale.kaufland.de/angebote/uebersicht.html"),
    ("DE", "rewe", "https://shop.rewe.de/api/products?search=milch"),
    ("DE", "aldi_sued", "https://api.aldi-sued.de/v3/product-search?currency=EUR&serviceType=walk-in&q=milch&limit=12&offset=0&sort=relevance"),
    ("DE", "aldi_nord", "https://www.aldi-nord.de/sortiment/kuehlung-tiefkuehlung/milch-sahne-butter.html"),
    ("DE", "lidl", "https://www.lidl.de/q/api/search?q=milch&assortment=DE&locale=de_DE&version=v2.0.0"),
    ("DE", "edeka", "https://www.edeka.de/eh/angebote.jsp"),
    ("DE", "netto", "https://www.netto-online.de/milch"),
    ("DE", "penny", "https://www.penny.de/angebote"),
    ("GB", "sainsburys", "https://www.sainsburys.co.uk/groceries-api/gol-services/product/v1/product?filter[keyword]=milk&page_number=1&page_size=24"),
    ("GB", "aldi_gb", "https://api.aldi.co.uk/v3/product-search?currency=GBP&serviceType=walk-in&q=milk&limit=12&offset=0&sort=relevance"),
    ("GB", "tesco", "https://www.tesco.com/groceries/en-GB/search?query=milk"),
    ("GB", "asda", "https://www.asda.com/groceries/search/milk"),
    ("GB", "morrisons", "https://groceries.morrisons.com/search?q=milk"),
    ("GB", "ocado", "https://www.ocado.com/search?entry=milk"),
    ("FR", "carrefour", "https://www.carrefour.fr/s?q=lait"),
    ("FR", "leclerc", "https://www.e.leclerc/recherche?q=lait"),
    ("FR", "auchan", "https://www.auchan.fr/recherche?text=lait"),
    ("FR", "intermarche", "https://www.intermarche.com/recherche/lait"),
    ("FR", "lidl_fr", "https://www.lidl.fr/q/api/search?q=lait&assortment=FR&locale=fr_FR&version=v2.0.0"),
    ("ES", "mercadona", "https://tienda.mercadona.es/api/categories/"),
    ("ES", "dia", "https://www.dia.es/api/v1/search-back/search/reduced?q=leche&page=1"),
    ("ES", "carrefour_es", "https://www.carrefour.es/search-api/query/v1/search?query=leche&scope=desktop&lang=es&rows=24&start=0&origin=default&f.op=OR"),
    ("ES", "alcampo", "https://www.compraonline.alcampo.es/api/v5/products/search?term=leche"),
    ("ES", "eroski", "https://supermercado.eroski.es/es/search/results/?q=leche"),
    ("ES", "consum", "https://tienda.consum.es/api/rest/V1.0/catalog/product?q=leche&limit=20"),
    ("IT", "carrefour_it", "https://www.carrefour.it/spesa-online/search?q=latte"),
    ("IT", "conad", "https://spesaonline.conad.it/search?query=latte"),
    ("IT", "esselunga", "https://spesaonline.esselunga.it/commerce/nav/supermercato/store/ricerca/latte"),
    ("IT", "coop_it", "https://www.easycoop.com/search?q=latte"),
    ("PL", "kaufland_pl", "https://www.kaufland.pl/"),
    ("PL", "auchan_pl", "https://zakupy.auchan.pl/api/v2/cache/products?keyword=mleko&page=1&hitsPerPage=24"),
    ("PL", "carrefour_pl", "https://www.carrefour.pl/szukaj?q=mleko"),
    ("PL", "biedronka", "https://zakupy.biedronka.pl/search?text=mleko"),
    ("PL", "frisco", "https://www.frisco.pl/app/commerce/api/v1/offer/products/query?purpose=Listing&pageIndex=1&search=mleko&pageSize=24"),
    ("NL", "ah", "https://www.ah.nl/zoeken/api/products/search?query=melk&size=24"),
    ("NL", "jumbo", "https://www.jumbo.com/producten/?searchTerms=melk"),
    ("NL", "dirk", "https://www.dirk.nl/zoeken/producten/melk"),
    ("NL", "plus", "https://www.plus.nl/zoekresultaten?SearchTerm=melk"),
    ("RO", "kaufland_ro", "https://www.kaufland.ro/"),
    ("RO", "auchan_ro", "https://www.auchan.ro/api/catalog_system/pub/products/search?ft=lapte&_from=0&_to=23"),
    ("RO", "carrefour_ro", "https://carrefour.ro/catalogsearch/result/?q=lapte"),
    ("RO", "mega_image", "https://www.mega-image.ro/search?q=lapte"),
    ("RO", "freshful", "https://www.freshful.ro/api/v2/shop/search?q=lapte"),
    ("CZ", "kaufland_cz", "https://www.kaufland.cz/"),
    ("CZ", "rohlik", "https://www.rohlik.cz/api/v1/products/search?search=mleko&limit=24"),
    ("CZ", "tesco_cz", "https://nakup.itesco.cz/groceries/cs-CZ/search?query=mleko"),
    ("CZ", "albert", "https://www.albert.cz/search?q=mleko"),
    ("CZ", "billa_cz", "https://shop.billa.cz/api/search/full?searchTerm=mleko&storeId=00-10&pageSize=24"),
    ("PT", "continente", "https://www.continente.pt/pesquisa/?q=leite"),
    ("PT", "pingodoce", "https://www.pingodoce.pt/pesquisa/?q=leite"),
    ("PT", "auchan_pt", "https://www.auchan.pt/pt/pesquisa?q=leite"),
    ("PT", "mercadona_pt", "https://tienda.mercadona.pt/api/categories/"),
    ("SE", "willys", "https://www.willys.se/search?q=mj%C3%B6lk&size=24"),
    ("SE", "hemkop", "https://www.hemkop.se/search?q=mj%C3%B6lk&size=24"),
    ("SE", "ica", "https://handlaprivatkund.ica.se/stores/1004222/api/v5/products/search?term=mj%C3%B6lk"),
    ("SE", "coop_se", "https://www.coop.se/handla/sok/?q=mj%C3%B6lk"),
    ("SE", "citygross", "https://www.citygross.se/api/v1/esales/search?Q=mj%C3%B6lk&size=24"),
    ("BE", "delhaize", "https://www.delhaize.be/fr/search?q=lait"),
    ("BE", "colruyt", "https://www.colruyt.be/fr/produits?searchTerm=lait"),
    ("BE", "carrefour_be", "https://www.carrefour.be/fr/search?q=lait"),
    ("AT", "billa", "https://shop.billa.at/api/search/full?searchTerm=milch&storeId=00-10&pageSize=24"),
    ("AT", "spar_at", "https://search-spar.spar-ics.com/fact-finder/rest/v4/search/products_lmos_at?query=milch&q=milch&page=1&hitsPerPage=24"),
    ("AT", "penny_at", "https://www.penny.at/api/products?page=0&pageSize=24"),
    ("AT", "hofer", "https://www.roksh.at/hofer/"),
    ("HU", "auchan_hu", "https://online.auchan.hu/api/v2/cache/products?keyword=tej&page=1&hitsPerPage=24"),
    ("HU", "tesco_hu", "https://bevasarlas.tesco.hu/groceries/hu-HU/search?query=tej"),
    ("HU", "spar_hu", "https://online.spar.hu/kereses?q=tej"),
    ("HU", "kifli", "https://www.kifli.hu/api/v1/products/search?search=tej&limit=24"),
    ("GR", "sklavenitis", "https://www.sklavenitis.gr/apotelesmata-anazitisis/?Query=%CE%B3%CE%AC%CE%BB%CE%B1"),
    ("GR", "ab", "https://www.ab.gr/search?q=%CE%B3%CE%AC%CE%BB%CE%B1"),
    ("GR", "mymarket", "https://www.mymarket.gr/search?query=%CE%B3%CE%AC%CE%BB%CE%B1"),
    ("GR", "masoutis", "https://www.masoutis.gr/categories/search?item=%CE%B3%CE%AC%CE%BB%CE%B1"),
    ("LT", "barbora_lt", "https://barbora.lt/paieska?q=pienas"),
    ("LT", "rimi_lt", "https://www.rimi.lt/e-parduotuve/lt/paieska?query=pienas"),
    ("LV", "barbora_lv", "https://barbora.lv/meklet?q=piens"),
    ("LV", "rimi_lv", "https://www.rimi.lv/e-veikals/lv/meklesana?query=piens"),
    ("EE", "rimi_ee", "https://www.rimi.ee/epood/ee/otsing?query=piim"),
    ("EE", "selver", "https://www.selver.ee/search?q=piim"),
    ("EE", "coop_ee", "https://api.ecoop.ee/supermarket/products?search=piim"),
    ("EE", "prisma_ee", "https://www.prismamarket.ee/search?q=piim"),
    ("EE", "barbora_ee", "https://barbora.ee/otsing?q=piim"),
    ("KZ", "magnum", "https://magnum.kz/catalog?search=молоко"),
    ("KZ", "arbuz", "https://arbuz.kz/ru/almaty/search?query=молоко"),
    ("KZ", "small", "https://smallmarket.kz/"),
    ("UA", "silpo", "https://sf-ecom-api.silpo.ua/v1/uk/branches/00000000-0000-0000-0000-000000000000/products?limit=24&offset=0&search=молоко"),
    ("UA", "atb", "https://www.atbmarket.com/sch?query=молоко"),
    ("UA", "zakaz_novus", "https://stores-api.zakaz.ua/stores/48201070/products/search/?q=молоко"),
    ("UA", "fora", "https://fora.ua/search?q=молоко"),
    ("RS", "maxi", "https://www.maxi.rs/search?q=mleko"),
    ("RS", "idea", "https://www.idea.rs/online/v2/search?q=mleko"),
    ("GE", "carrefour_ge", "https://www.carrefour.ge/"),
    ("GE", "goodwill", "https://goodwill.ge/"),
    ("AM", "yerevan_city", "https://www.yerevan-city.am/"),
    ("AM", "sas", "https://www.sas.am/"),
    ("MD", "linella", "https://linella.md/"),
    ("MD", "kaufland_md", "https://www.kaufland.md/"),
    ("PL", "kaufland_pl2", "https://www.kaufland.pl/oferta/przeglad.html"),
    ("CZ", "kaufland_cz2", "https://prodejny.kaufland.cz/aktualni-nabidka/prehled.html"),
    ("SK", "kaufland_sk", "https://predajne.kaufland.sk/aktualna-ponuka/prehlad.html"),
    ("HR", "kaufland_hr", "https://www.kaufland.hr/"),
    ("BG", "kaufland_bg", "https://www.kaufland.bg/"),
    ("SI", "mercator", "https://trgovina.mercator.si/market/iskanje?q=mleko"),
    ("HR", "konzum", "https://www.konzum.hr/web/search?q=mlijeko"),
    ("RS", "maxi_api", "https://www.maxi.rs/search?q=mleko"),
    ("ME", "voli", "https://voli.me/pretraga?q=mlijeko"),
    ("BA", "bingo", "https://www.bingotuzla.ba/"),
    ("MD", "linella_s", "https://linella.md/ro/search?q=lapte"),
    ("AM", "sas_s", "https://www.sas.am/search/?q=milk"),
    ("RO", "mega_image2", "https://www.mega-image.ro/search?q=lapte"),
    ("RO", "carrefour_ro2", "https://carrefour.ro/catalogsearch/result/?q=lapte"),
    ("SE", "ica2", "https://handlaprivatkund.ica.se/"),
    ("FR", "lidl_fr_off", "https://www.lidl.fr/"),
    ("XX", "openprices","https://prices.openfoodfacts.org/api/v1/prices?size=3&location__osm_address_country_code=FR"),
]


def main():
    only = sys.argv[1:]
    for cc, chain, url in C:
        if only and cc not in only:
            continue
        rob = allowed(url)
        try:
            status, body, ctype = fetch(url, raw=True)
        except Exception as e:
            status, body, ctype = type(e).__name__, "", ""
        # подсказки: сколько похожих на цену чисел, есть ли встроенный JSON, ссылки на акции Kaufland
        prices = len(re.findall(r"\d+[.,]\d{2}\s*(?:€|zł|lei|Kč|kr|£|₽|₴|₸|Ft|\"|,)", body))
        hints = [h for h in ("__NEXT_DATA__", "application/ld+json", "__NUXT__", "window.__INITIAL_STATE__", "captcha", "cf-chl", "datadome", "Access Denied") if h in body]
        links = sorted(set(re.findall(r'href="([^"]*(?:angebote|oferta|oferte|nabidka|akcie|ponude)[^"]*)"', body)))[:4]
        rs = common.ROBOTS_STATUS.get(urllib.parse.urlsplit(common.iri(url)).netloc)
        print(f"{cc} | {chain} | robots={'ok' if rob else 'NO'}({rs}) | {status} | {len(body)}b | {ctype[:30]} | prices~{prices} | {','.join(hints)} | {' '.join(links)} | {url[:90]}", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    main()
