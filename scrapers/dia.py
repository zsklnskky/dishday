# Dia (ES): поиск (*/search/reduced?*) закрыт в robots.txt, пагинация */pag-* тоже (разрешающие Allow со * мы
# не учитываем). Берём первую страницу продуктовых категорий /<раздел>/<подраздел>/c/L<код>: в ней JSON-LD
# seoProductMarkingData - до 20 товаров с именем, ценой упаковки и адресом. Фасовка из названия ("Zanahoria 1 Kg"),
# подбор по скачанным строкам через local из green. Цены региона сайта по умолчанию.
import json
from common import allowed, by_search, fetch, row
from green import local

SITE = "https://www.dia.es"
CATS = """carnes/cerdo/c/L2014 carnes/pollo/c/L2202 carnes/pavo/c/L2015 carnes/vacuno/c/L2013
carnes/hamburguesas-carne-picada-y-albondigas/c/L2017 carnes/arreglos-y-despieces/c/L2266
charcuteria/bacon/c/L2344 charcuteria/salchichas/c/L2206
pescados-y-mariscos/fresco/c/L2019 pescados-y-mariscos/congelado/c/L2249 pescados-y-mariscos/ahumado-y-salazon/c/L2020
pescados-y-mariscos/marisco-gamba-y-calamar/c/L2253
huevos-leche-y-mantequilla/huevos/c/L2055 huevos-leche-y-mantequilla/leche/c/L2051
huevos-leche-y-mantequilla/mantequilla-y-margarina/c/L2056 huevos-leche-y-mantequilla/nata/c/L2054
yogures-y-postres/yogures-naturales-y-desnatados/c/L2079 yogures-y-postres/kefir-y-postres-vegetales/c/L2085
yogures-y-postres/yogures-griegos/c/L2082
quesos/curado/c/L2007 quesos/semicurado/c/L2345 quesos/tierno/c/L2346 quesos/fresco/c/L2008 quesos/rallado/c/L2347
quesos/especialidades/c/L2011 quesos/untable-y-en-porciones/c/L2010
verduras/patatas-y-zanahorias/c/L2028 verduras/ajos-cebollas-y-puerros/c/L2022
verduras/tomates-pimientos-y-pepinos/c/L2023 verduras/calabacin-calabaza-y-berenjena/c/L2181
verduras/brocoli-coliflor-y-judias-verdes/c/L2024 verduras/setas-y-champinones/c/L2029
verduras/lechugas-y-hojas-verdes/c/L2027 verduras/hierbas-aromaticas/c/L2031 verduras/verduras-congeladas-y-al-vapor/c/L2025
frutas/frutas-de-temporada/c/L2040 frutas/frutas-tropicales/c/L2039
arroz-pastas-y-legumbres/arroz/c/L2042 arroz-pastas-y-legumbres/macarrones-espaguetis-y-pastas-secas/c/L2044
arroz-pastas-y-legumbres/garbanzos-y-alubias/c/L2191 arroz-pastas-y-legumbres/lentejas/c/L2193
arroz-pastas-y-legumbres/quinoa-couscous-y-soja/c/L2043 arroz-pastas-y-legumbres/fideos/c/L2270
bolleria-reposteria-y-azucar/harinas-y-levaduras/c/L2075 bolleria-reposteria-y-azucar/azucar-miel-y-edulcorantes/c/L2060
galletas-cereales-y-mermeladas/cereales-integrales-y-muesli/c/L2321
aceites-salsas-y-especias/aceites/c/L2046 aceites-salsas-y-especias/vinagres-y-alinos/c/L2047
aceites-salsas-y-especias/salsas-de-tomate-y-pasta/c/L2208 aceites-salsas-y-especias/salsas-especiales-y-picantes/c/L2296
aceites-salsas-y-especias/ajo-sal-y-pimienta/c/L2048 aceites-salsas-y-especias/especias-y-hierbas/c/L2294
aperitivos-y-frutos-secos/frutos-secos/c/L2097 aperitivos-y-frutos-secos/frutas-deshidratadas/c/L2041
conservas-caldos-y-cremas/conservas-de-verdura/c/L2092""".split()
KEY = '"seoProductMarkingData":'


def parse(page):
    i = page.find(KEY)
    if i < 0:
        return []
    data, out = json.JSONDecoder().raw_decode(page, i + len(KEY))[0], []
    for el in data.get("itemListElement") or []:
        it = el.get("item") or {}
        price = (it.get("offers") or {}).get("price")
        if price and it.get("name"):
            out.append(row(it["name"], price, url=el.get("url")))
    return out


def collect(cc, chain, ing, words):
    rows = []
    for c in CATS:
        url = f"{SITE}/{c}"
        if not allowed(url):
            continue
        try:
            rows += parse(fetch(url, lang="es"))
        except Exception as e:
            print(f"  dia {c}: {type(e).__name__} {e}"[:120], flush=True)
    if not rows:
        raise RuntimeError("категории Dia не отдали товаров")
    uniq = list({r["url"] or r["name"]: r for r in rows}.values())
    return by_search(lambda q: local(uniq, q), ing, words, "es", chain["id"])


if __name__ == "__main__":
    page = ('..."total_items":9,"seoProductMarkingData":{"@context":"http:\\/\\/schema.org","@type":"ItemList","itemListElement":['
            '{"@type":"ListItem","item":{"@type":"Product","name":"Zanahoria 1 Kg","offers":{"@type":"Offer","price":0.89,'
            '"priceCurrency":"EUR"}},"position":1,"url":"https:\\/\\/www.dia.es\\/verduras\\/p\\/1"},'
            '{"@type":"ListItem","item":{"@type":"Product","name":"Patatas de guarnici\\u00f3n 1 Kg","offers":{"price":1.99}},'
            '"url":"u2"},{"@type":"ListItem","item":{"name":"Sin precio","offers":{}}}]},"x":1')
    a, b = parse(page)
    assert (a["price"], a["size"], a["unit"], a["url"]) == (.89, 1.0, "kg", "https://www.dia.es/verduras/p/1"), a
    assert b["name"] == "Patatas de guarnición 1 Kg" and b["price"] == 1.99
    assert parse("<html></html>") == []
    print("dia self-check ok")
