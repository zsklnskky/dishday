# Consum (ES): открытый JSON каталога tienda.consum.es, цена упаковки и цена за «1 L / 1 Kg».
import urllib.parse
from common import by_search, get_json, row


def collect(cc, chain, ing, words):
    def search(q):
        d = get_json("https://tienda.consum.es/api/rest/V1.0/catalog/product?limit=30&q=" + urllib.parse.quote(q), lang="es")
        out = []
        for p in d.get("products", []):
            pd, prices = p.get("productData") or {}, (p.get("priceData") or {}).get("prices") or []
            if not prices:
                continue
            v = prices[-1]["value"]  # последняя - действующая (акция идёт после PRICE)
            r = row(pd.get("description") or pd.get("name", ""), v["centAmount"], url=pd.get("url"))
            ut = ((p.get("priceData") or {}).get("unitPriceUnitType") or "").lower()
            if v.get("centUnitAmount") and ("kg" in ut or ut.endswith(" l")):
                r["ppu"], r["unit"] = v["centUnitAmount"], "kg" if "kg" in ut else "l"
            out.append(r)
        return out

    return by_search(search, ing, words, "es", chain["id"])
