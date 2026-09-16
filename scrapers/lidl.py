# Lidl: открытый JSON поисковой строки сайта (тот же, что отдаётся браузеру). Один эндпоинт на 28 стран.
# Ассортимент смешанный: продукты магазина и непродовольственный онлайн-шоп, продукты отбирает matches() по стемам.
# Цена: price.price за упаковку, basePrice - за кг/л структурой ({"price":6.65,"unit":"l"}) или текстом «1 kg = 4,45 €».
import re, urllib.parse
from common import by_search, get_json, row, to_num

SITES = {  # страна -> (домен после lidl., локаль, язык словаря)
    "DE": ("de", "de_DE", "de"), "AT": ("at", "de_AT", "de"), "CH": ("ch", "de_CH", "de"),
    "PL": ("pl", "pl_PL", "pl"), "CZ": ("cz", "cs_CZ", "cs"), "SK": ("sk", "sk_SK", "sk"),
    "HU": ("hu", "hu_HU", "hu"), "RO": ("ro", "ro_RO", "ro"), "BG": ("bg", "bg_BG", "bg"),
    "HR": ("hr", "hr_HR", "hr"), "SI": ("si", "sl_SI", "sl"), "RS": ("rs", "sr_RS", "sr"),
    "GR": ("gr", "el_GR", "el"), "CY": ("com.cy", "el_CY", "el"),
    "IE": ("ie", "en_IE", "en"), "GB": ("co.uk", "en_GB", "en"), "MT": ("com.mt", "en_MT", "en"),
    "ES": ("es", "es_ES", "es"), "PT": ("pt", "pt_PT", "pt"), "IT": ("it", "it_IT", "it"),
    "FR": ("fr", "fr_FR", "fr"), "BE": ("be", "fr_BE", "fr"), "NL": ("nl", "nl_NL", "nl"),
    "SE": ("se", "sv_SE", "sv"), "DK": ("dk", "da_DK", "da"), "FI": ("fi", "fi_FI", "fi"),
    "LT": ("lt", "lt_LT", "lt"), "LV": ("lv", "lv_LV", "lv"), "EE": ("ee", "et_EE", "et"),
}


_Q = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|g|l|ml|cl|dl)\b", re.I)
_K = {"kg": ("kg", 1), "g": ("kg", .001), "l": ("l", 1), "ml": ("l", .001), "cl": ("l", .01), "dl": ("l", .1)}


def last_qty(s):
    """Последняя фасовка в строке -> (количество в кг/л, единица)."""
    m = None
    for m in _Q.finditer(s):
        pass
    if not m:
        return None
    unit, k = _K[m.group(2).lower()]
    v = float(m.group(1).replace(",", ".")) * k
    return (v, unit) if v > 0 else None


def base_ppu(bp):
    """basePrice -> (цена за кг/л, единица). Структурой или из текста: «1 kg = 4,45 €», «100 g = 0,45 €»,
    «1 Kg = Από 37€ σε 18,5€» (скидка - берём последнее число, это действующая цена).
    Опорная единица - та, что стоит НЕПОСРЕДСТВЕННО перед знаком равенства: в чешском «250 g, 100 g = 14,96 Kč»
    первой идёт фасовка пачки, и если считать по ней, килограмм масла выходит вчетверо дешевле настоящего."""
    if not isinstance(bp, dict):
        return None
    unit = (bp.get("unit") or "").lower()
    if isinstance(bp.get("price"), (int, float)) and unit in ("kg", "l") and bp["price"] > 0:
        return float(bp["price"]), unit
    left, eq, right = (bp.get("text") or "").replace("\xa0", " ").partition("=")
    if not eq:
        return None
    q = last_qty(left)
    nums = re.findall(r"\d+(?:[.,]\d+)?", right)
    if q and nums:
        v = to_num(nums[-1]) / q[0]
        return (v, q[1]) if v > 0 else None
    return None


FOOD = ("food", "a product")  # корень категории продуктов магазина


def is_food(g):
    """Выдача поиска смешана с онлайн-шопом: техника, одежда, вино. Без этого отбора «молоко» в Германии
    приводит Liebfraumilch (вино), «масло» - арахисовую пасту, «сливки» - сливочный ликёр."""
    cats = (g.get("category") or "", ((g.get("keyfacts") or {}) or {}).get("analyticsCategory") or "")
    return any(str(c).strip().lower().startswith(FOOD) for c in cats)


def parse(d, host):
    out = []
    for it in d.get("items") or []:
        g = (it.get("gridbox") or {}).get("data") or {}
        pr = g.get("price") or {}
        price = pr.get("price")
        if not isinstance(price, (int, float)) or price <= 0 or not is_food(g):
            continue  # у части карточек цена только в листовке
        pk = g.get("packaging") or {}
        r = row(g.get("fullTitle") or "", price, pk.get("text") or "" if isinstance(pk, dict) else "",
                url=f"https://www.lidl.{host}" + (g.get("canonicalPath") or ""))
        b = base_ppu(pr.get("basePrice"))
        if b:
            r["ppu"], r["unit"] = b
            r["size"] = r["size"] or round(price / b[0], 3)
        out.append(r)
    return out


def collect(cc, chain, ing, words):
    host, loc, lang = SITES[cc]

    def search(q):
        url = (f"https://www.lidl.{host}/q/api/search?q={urllib.parse.quote(q)}"
               f"&assortment={cc}&locale={loc}&version=v2.0.0")
        try:
            d = get_json(url, lang=lang)
        except ValueError:  # сайт изредка отдаёт пустой ответ вместо JSON, со второй попытки приходит нормальный
            d = get_json(url, lang=lang)
        return parse(d, host)

    return by_search(search, ing, words, chain.get("lang") or lang, chain["id"])


if __name__ == "__main__":
    f = lambda **kw: {"gridbox": {"data": {"category": "Food", **kw}}}
    d = {"items": [
        f(fullTitle="MILBONA Frische Vollmilch", canonicalPath="/p/milch/p1", packaging={"text": "1 l"},
          price={"price": 1.19, "basePrice": {"amount": 1.0, "price": 1.19, "unit": "l"}}),
        f(fullTitle="Hähnchenbrustfilet", canonicalPath="/p/h/p2",
          price={"price": 4.45, "basePrice": {"text": "1 kg = 8,90 €"}}),
        f(fullTitle="Τυροβουτιές", price={"price": 2.0, "basePrice": {"text": "100 g = 0,45 €"}}),
        f(fullTitle="Γάλα ακριβό", price={"price": 2.0, "basePrice": {"text": "1 Kg = Από 37€ σε 18,5€"}}),
        f(fullTitle="Ohne Preis", price={"currencyCode": "EUR"}),
        # чешский формат: сначала фасовка пачки, опорная единица - перед знаком равенства
        f(fullTitle="Máslo", price={"price": 36.9, "basePrice": {"text": "250 g, 100 g = 14,96 Kč"}}),
        f(fullTitle="MILKPOL Máslo", price={"price": 79.6, "basePrice": {"text": "250 g, 1 kg = 79,60 Kč"}}),
        # вино и техника из онлайн-шопа: цена есть, но это не еда
        {"gridbox": {"data": {"fullTitle": "MERTES Liebfraumilch", "category": "Kategorien/Weinwelt/Weinart/Weißwein",
                              "price": {"price": 3.0, "basePrice": {"amount": 1.0, "price": 3.0, "unit": "l"}}}}},
        {"gridbox": {"data": {"fullTitle": "SILVERCREST Milchaufschäumer", "category": "Kategorien/Haushalt & Küche",
                              "price": {"price": 17.99}}}},
    ]}
    r = parse(d, "de")
    assert len(r) == 6, [x["name"] for x in r]
    assert r[4]["ppu"] == 149.6 and r[4]["unit"] == "kg", r[4]   # 100 г за 14,96 -> 149,60 за кг
    assert r[5]["ppu"] == 79.6, r[5]
    assert last_qty("250 g, 100 g ") == (0.1, "kg") and last_qty("1 l ") == (1.0, "l")
    assert not any("Liebfraumilch" in x["name"] or "Milchaufschäumer" in x["name"] for x in r)
    assert is_food({"keyfacts": {"analyticsCategory": "Food"}}) and not is_food({"category": "Assortiment/Mode"})
    assert r[0]["ppu"] == 1.19 and r[0]["unit"] == "l" and r[0]["size"] == 1.0
    assert r[1]["ppu"] == 8.9 and r[1]["unit"] == "kg" and r[1]["size"] == 0.5
    assert r[2]["ppu"] == 4.5 and r[2]["unit"] == "kg"          # 100 г за 0,45 -> 4,50 за кг
    assert r[3]["ppu"] == 18.5 and r[3]["unit"] == "kg"          # цена со скидкой, не старая
    assert base_ppu({"text": "Осторожно, алкоголь"}) is None
    print("lidl self-check ok")
