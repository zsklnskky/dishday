# SuperValu (IE): открытый JSON витрины storefrontgateway.supervalu.ie - тот же, из которого рисует страницу
# shop.supervalu.ie. Цена упаковки в priceNumeric, фасовка в unitOfSize, готовая цена за литр/кг в pricePerUnit.
# Цены магазина доставки 5550 (магазин по умолчанию).
import re, urllib.parse
from common import by_search, get_json, row

STORE = 5550
UNIT = {"kg": ("kg", 1), "g": ("kg", .001), "l": ("l", 1), "ml": ("l", .001), "cl": ("l", .01),
        "ea": ("pc", 1), "each": ("pc", 1), "pk": ("pc", 1), "pack": ("pc", 1)}


def items(d):
    out = []
    for p in d.get("items", []):
        if not p.get("priceNumeric") or not p.get("available"):
            continue
        r = row(p["name"], p["priceNumeric"], url=f"https://shop.supervalu.ie/sm/delivery/rsid/{STORE}/product/{p['sku']}")
        u = p.get("unitOfSize") or {}
        k = UNIT.get((u.get("abbreviation") or "").lower())
        if k and u.get("size"):
            r["size"], r["unit"] = round(u["size"] * k[1], 4), k[0]
        m = re.search(r"([\d.]+)\s*/\s*(kg|g|l|ml)\b", p.get("pricePerUnit") or "", re.I)
        if m and UNIT[m.group(2).lower()][0] == r["unit"]:  # цена за кг/л уже посчитана магазином
            r["ppu"] = float(m.group(1)) / UNIT[m.group(2).lower()][1]
        out.append(r)
    return out


def collect(cc, chain, ing, words):
    def search(q):
        return items(get_json(f"https://storefrontgateway.supervalu.ie/api/stores/{STORE}/search?q="
                              + urllib.parse.quote(q) + "&take=30", lang="en"))

    return by_search(search, ing, words, "en", chain["id"])


if __name__ == "__main__":
    d = {"items": [{"name": "SuperValu Fresh Irish Whole Milk (2 L)", "sku": "1025460000", "priceNumeric": 2.25,
                    "available": True, "pricePerUnit": "€1.13/l", "unitOfSize": {"abbreviation": "l", "size": 2.0}},
                   {"name": "Ballyfree Large Eggs 6 Pack", "sku": "1", "priceNumeric": 3.0, "available": True,
                    "pricePerUnit": "", "unitOfSize": {"abbreviation": "ea", "size": 6.0}}]}
    a, b = items(d)
    assert a["size"] == 2.0 and a["unit"] == "l" and a["ppu"] == 1.13, a
    assert b["size"] == 6.0 and b["unit"] == "pc" and b["ppu"] is None, b
    print("supervalu self-check ok")
