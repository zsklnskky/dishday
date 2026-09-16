# Kaufland: страница акций недели отдаёт JSON предложений с ценой за кг/л (basePrice). Только акции, филиал по умолчанию.
import html, json, re
from common import by_catalog, fetch, pack

PAGES = {"DE": ("https://filiale.kaufland.de/angebote/uebersicht.html", "de"),
         "RO": ("https://www.kaufland.ro/oferte/oferte-saptamanale/saptamana-curenta.html", "ro"),
         "MD": ("https://www.kaufland.md/ro/oferte/prezentare-generala-oferte.html", "ro"),
         "SK": ("https://predajne.kaufland.sk/aktualna-ponuka/prehlad.html", "sk"),
         "BG": ("https://www.kaufland.bg/aktualni-predlozheniya/ot-ponedelnik.html", "bg")}
_BASE = re.compile(r"1\s*(kg|l)\s*=?\s*([\d.,]+)", re.I)


def offers(page, url):
    rows = []
    for m in re.finditer(r'\{"offerId":.*?"formattedPrice":"[^"]*"\}', page):
        try:
            o = json.loads(m.group(0))
        except ValueError:
            continue
        title = html.unescape(" ".join(filter(None, (o.get("detailTitle") or o.get("title"), o.get("subtitle"))))).replace(" ", " ")
        price = o.get("price")
        if not price:
            continue
        bp = _BASE.search(o.get("basePrice") or "")
        unit = (o.get("unit") or "").lower()
        if bp:
            u, ppu = bp.group(1).lower(), float(bp.group(2).replace(",", "."))
        elif unit.endswith(" kg") or unit.endswith(" l"):
            u, ppu = unit.split()[-1], float(price)
        else:
            p = pack(title + " " + unit)
            if not p:
                continue
            u, ppu = p[1], float(price) / p[0]
        rows.append({"name": " ".join(title.split()), "price": float(price), "size": round(float(price) / ppu, 3) if ppu else None,
                     "unit": u, "ppu": ppu, "url": url})
    return rows


def collect(cc, chain, ing, words):
    url, lang = PAGES[cc]
    return by_catalog(offers(fetch(url, lang=lang), url), ing, words, lang)


if __name__ == "__main__":
    sample = '{"offerId":"1","title":"Milsani","subtitle":"Frische Vollmilch","price":0.99,"basePrice":"(1 l = 0.99)","unit":"1 l","formattedPrice":"0,99"}' \
             '{"offerId":"2","title":"Hähnchen","subtitle":"Brustfilet","price":6.49,"basePrice":"(=1 kg 12.98)","unit":"500 g","formattedPrice":"6,49"}'
    r = offers(sample, "u")
    assert r[0]["ppu"] == 0.99 and r[1]["ppu"] == 12.98 and r[1]["size"] == 0.5 and r[1]["unit"] == "kg"
    print("kaufland self-check ok")
