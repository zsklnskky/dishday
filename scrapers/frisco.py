# Frisco.pl (PL): онлайн-супермаркет Варшавы и других городов, открытый JSON витрины. Не входит в топ-5 сетей -
# используется как опорный живой источник цен Польши, пока Biedronka/Lidl/Dino/Żabka/Kaufland без открытого каталога.
import urllib.parse
from common import by_search, get_json

UNIT = {"kilogram": "kg", "litre": "l", "liter": "l", "piece": "pc"}


def collect(cc, chain, ing, words):
    def search(q):
        d = get_json("https://www.frisco.pl/app/commerce/api/v1/offer/products/query?purpose=Listing&pageIndex=1&pageSize=30&search="
                     + urllib.parse.quote(q), lang="pl")
        out = []
        for it in d.get("products", []):
            p = it.get("product") or {}
            price = ((p.get("price") or {}).get("price"))
            u, g = UNIT.get((p.get("unitOfMeasure") or "").lower()), p.get("grammage")
            if not price:
                continue
            out.append({"name": (p.get("name") or {}).get("pl", ""), "price": float(price), "size": g if u else None, "unit": u,
                        "ppu": None, "url": f"https://www.frisco.pl/pid,{p.get('id')}"})
        return out

    return by_search(search, ing, words, "pl", chain["id"])
