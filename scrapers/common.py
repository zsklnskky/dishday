# Общее для сборщиков цен Dishday: вежливая загрузка с проверкой robots.txt, разбор фасовок,
# подбор товара по стемам, нормализация цены за кг/л/шт. Один файл на сеть рядом, здесь - всё повторяемое.
# Самопроверка: python scrapers/common.py
import json, os, re, statistics, threading, time, urllib.error, urllib.parse, urllib.request, urllib.robotparser

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (compatible; DishdayPrices/1.0; +https://zsklnskky.github.io/dishday/prices/)"
BOT = "DishdayPrices"
PAUSE = 1.5          # секунд между запросами к одному сайту
TIMEOUT = 25
MAX_BYTES = 8_000_000  # защита от бесконечного ответа

_robots, _last, _lock = {}, {}, threading.Lock()


def allowed(url):
    """robots.txt сайта разрешает адрес. 404 - разрешено; не прочитали по другой причине - считаем запретом."""
    p = urllib.parse.urlsplit(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            status, body, _ = fetch(base + "/robots.txt", check=False, raw=True)
            rp.parse(body.splitlines()) if status == 200 else rp.parse([] if status in (404, 410) else ["User-agent: *", "Disallow: /"])
        except Exception:
            rp.parse(["User-agent: *", "Disallow: /"])
        _robots[base] = rp
    return _robots[base].can_fetch(BOT, url)


def fetch(url, check=True, raw=False, data=None, headers=None, lang="en"):
    """GET (или POST при data) с паузой на хост. raw=True -> (status, text, content-type), иначе текст или исключение."""
    if not url.startswith("https://"):
        raise ValueError("только https")
    if check and not allowed(url):
        raise PermissionError("robots.txt запрещает " + url)
    host = urllib.parse.urlsplit(url).netloc
    with _lock:
        wait = _last.get(host, 0) + PAUSE - time.time()
        _last[host] = time.time() + max(wait, 0)
    if wait > 0:
        time.sleep(wait)
    h = {"User-Agent": UA, "Accept-Language": lang, "Accept": "application/json, text/html;q=0.9, */*;q=0.5", **(headers or {})}
    req = urllib.request.Request(url, data=data, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            status, body, ctype = r.status, r.read(MAX_BYTES), r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        status, body, ctype = e.code, e.read(200_000), e.headers.get("Content-Type", "")
    text = body.decode("utf-8", "ignore")
    if raw:
        return status, text, ctype
    if status != 200:
        raise RuntimeError(f"HTTP {status}")
    return text


def get_json(url, **kw):
    return json.loads(fetch(url, **kw))


# ---------- фасовки ----------
UNITS = {"kg": ("kg", 1), "кг": ("kg", 1), "g": ("kg", .001), "gr": ("kg", .001), "г": ("kg", .001), "гр": ("kg", .001),
         "l": ("l", 1), "л": ("l", 1), "ltr": ("l", 1), "ml": ("l", .001), "мл": ("l", .001), "cl": ("l", .01), "dl": ("l", .1),
         "шт": ("pc", 1), "pcs": ("pc", 1), "pc": ("pc", 1), "st": ("pc", 1), "stk": ("pc", 1), "szt": ("pc", 1), "ks": ("pc", 1),
         "db": ("pc", 1), "buc": ("pc", 1), "vnt": ("pc", 1), "gab": ("pc", 1), "tk": ("pc", 1), "x": None}
_Q = re.compile(r"(?:(\d+)\s*[x×х]\s*)?(\d+(?:[.,]\d+)?)\s*(kg|кг|gr|г|гр|g|ltr|l|л|ml|мл|cl|dl|шт|pcs|pc|stk|st|szt|ks|db|buc|vnt|gab|tk)(?![a-zа-яё])", re.I)


def pack(title):
    """Фасовка из названия -> (количество, 'kg'|'l'|'pc') или None. '2 x 500 g' -> (1.0, 'kg'). Диапазоны '750-g' не берём."""
    t = title.lower().replace("\xa0", " ")
    for m in _Q.finditer(t):
        if t[max(0, m.start() - 1):m.start()] in ("-", "/"):
            continue
        unit, k = UNITS[m.group(3).lower()]
        v = float(m.group(2).replace(",", ".")) * k * int(m.group(1) or 1)
        return (round(v, 4), unit) if v > 0 else None
    return None


def to_num(s):
    """'1.299,00' / '1,299.00' / '12,5' / 3.4 -> float."""
    if isinstance(s, (int, float)):
        return float(s)
    s = re.sub(r"[^\d.,]", "", str(s))
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


# ---------- подбор товара ----------
UNIT_OF = {"кг": "kg", "л": "l", "шт": "pc", "уп": "pack", "банка": "pack", "пучок": "pack"}
COMPOUND = {"de", "nl", "sv", "da", "no", "fi", "et", "hu", "is"}  # языки со сложными словами: стем может быть внутри слова
BAD_ALL = ("sauce", "chips", "snack", "drink", "baby", "bio ", "organic", "katzen", "hunde", "pet ", "dog", "cat food")


def matches(title, words, lang, bad=()):
    """Все стемы есть в названии (для сложных языков - где угодно, иначе с начала слова) и нет слов-подмен."""
    t = " " + title.lower() + " "
    if lang in COMPOUND:
        ok = all(w in t for w in words)
    else:
        ok = all(re.search(r"(?<![\w])" + re.escape(w), t) for w in words)
    return ok and not any(b in t and b not in " ".join(words) for b in tuple(bad) + BAD_ALL)


def per_unit(price, size, unit, want):
    """Цена упаковки -> цена за единицу ING. want: kg/l/pc/pack. kg и l считаем взаимозаменяемыми для жидких/пастообразных."""
    if want == "pack":
        return price
    if not size or not unit:
        return None
    if unit == want or {unit, want} == {"kg", "l"}:
        return price / size
    return None


def pick(rows, want):
    """rows: dict(name, price, size, unit, url[, ppu]). Окно 0.6-1.8x к медиане, затем медиана до 5 самых дешёвых.
    Возвращает запись контракта или None."""
    cand = []
    for r in rows:
        ppu = r.get("ppu") or per_unit(r["price"], r.get("size"), r.get("unit"), want)
        if ppu and ppu > 0:
            cand.append((ppu, r))
    if not cand:
        return None
    m = statistics.median(p for p, _ in cand)
    kept = sorted((c for c in cand if 0.6 * m <= c[0] <= 1.8 * m), key=lambda c: c[0])
    top = kept[:5]
    ppu, r = top[(len(top) - 1) // 2]
    sizes = [c[1]["size"] for c in kept if c[1].get("size") and c[1].get("unit") in (want, "kg", "l")]
    return {"price_per_unit": round(ppu, 3), "unit": want, "pack_size": r.get("size"), "pack_unit": r.get("unit"),
            "pack_price": round(r["price"], 2), "min_pack": min(sizes) if sizes else r.get("size"),
            "product_name": r["name"][:120], "url": r.get("url"), "found": len(kept)}


def load(name):
    return json.load(open(os.path.join(HERE, name), encoding="utf-8"))


if __name__ == "__main__":
    assert pack("Vollmilch 3,5% 1 l") == (1.0, "l")
    assert pack("Hähnchenbrust 2 x 500 g") == (1.0, "kg")
    assert pack("Молоко 900\xa0мл") == (0.9, "l")
    assert pack("Jajka L 10 szt") == (10, "pc")
    assert pack("Mandarinen je 750-g-Netz") is None
    assert pack("Knoblauch lose") is None
    assert to_num("1.299,00") == 1299.0 and to_num("1,299.50") == 1299.5 and to_num("12,5 €") == 12.5
    assert matches("Frische Vollmilch 3,5%", ["milch"], "de")
    assert not matches("Vollmilch-Schokolade", ["milch"], "de", bad=["schoko"])
    assert matches("Mleko UHT 2% 1 l", ["mleko"], "pl") and not matches("Czekolada mleczna", ["mleko"], "pl")
    assert not matches("Tomato ketchup", ["tomato"], "en", bad=["ketchup"])
    rows = [{"name": "A 1 l", "price": 1.0, "size": 1, "unit": "l"}, {"name": "B 0.5 l", "price": .6, "size": .5, "unit": "l"},
            {"name": "C 1 l", "price": 1.1, "size": 1, "unit": "l"}, {"name": "Junk 0.1 l", "price": 5, "size": .1, "unit": "l"}]
    got = pick(rows, "l")
    assert got["price_per_unit"] == 1.1 and got["found"] == 3 and got["min_pack"] == .5  # 50 за литр отсечён окном 0.6-1.8
    assert pick([{"name": "Eggs 10 pcs", "price": 3.0, "size": 10, "unit": "pc"}], "pc")["price_per_unit"] == .3
    assert pick([{"name": "x", "price": 2, "size": 1, "unit": "pc"}], "kg") is None  # штуки не превращаем в килограммы
    print("common self-check ok")
