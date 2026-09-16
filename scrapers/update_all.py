# Сбор цен всех стран -> prices/<cc>.json (контракт в COVERAGE.md / SPEC-intl.md).
# Живые сети: модуль scrapers/<parser>.py с функцией collect(cc, chain, ing, words) -> {ingKey: запись}.
# Остальные сети и пропуски: оценка = цена Беларуси (data.js) по курсу × уровень цен страны, помечается est.
# Сеть, собравшая меньше 30% прошлого покрытия (или упавшая), остаётся со старыми ценами и старой датой.
# Запуск: python scrapers/update_all.py [DE PL ...]   --check самопроверка   --summary строка для коммита
import concurrent.futures as cf, datetime, importlib, json, os, statistics, sys, traceback
from common import HERE, UNIT_OF, get_json, load

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "prices")
BY_VS_DE = 0.85  # Беларусь к Германии по еде: медиана 11 совпадений акций Kaufland к Евроопту, 14.09.2026 (1/1.17)


def keep_old(before, after):
    """Старые цены сети остаются, если собрано меньше 30% прошлого покрытия."""
    return before > 0 and after < before * 0.3


def level_vs_by(c):
    """Во сколько раз еда в стране дороже, чем в Беларуси. Eurostat - по индексу цен на еду, иначе грубо по ВВП."""
    lv = c["priceLevel"]
    if lv.get("vsBY"):
        return lv["vsBY"]
    if lv.get("pli"):
        return lv["pli"] / 102.7 / BY_VS_DE  # 102.7 - Германия, prc_ppp_ind 2024, EU27=100
    # ponytail: степень 0.15 подобрана по двум живым точкам (DE/BY 1.17, RU/BY 1.05); уточнять, когда появятся живые цены страны
    return (lv["gdpPlr"] / 0.759) ** 0.15 / BY_VS_DE


def rates(prev):
    try:
        r = get_json("https://open.er-api.com/v6/latest/EUR", check=False)
        return {"date": r["time_last_update_utc"][5:16], "eur": r["rates"], "src": "https://www.exchangerate-api.com"}
    except Exception as e:
        print("курсы не получены, беру прошлые:", e)
        return prev


def usd_rates(fallback):
    """Сколько местной валюты за 1 USD, с источником и датой. ЕЦБ - валюты ЕС/EFTA через EUR; НБРБ - BYN и валюты СНГ
    (кросс через BYN); BAM - фиксированный курс к EUR; остальные (GEL, RSD, MKD, ALL) - exchangerate-api (не центробанк)."""
    out = {}
    try:
        cur = "USD+GBP+CHF+PLN+CZK+HUF+RON+SEK+DKK+NOK+ISK"
        d = get_json(f"https://data-api.ecb.europa.eu/service/data/EXR/D.{cur}.EUR.SP00.A?lastNObservations=1&format=jsondata", check=False)
        ids = d["structure"]["dimensions"]["series"][1]["values"]
        days = d["structure"]["dimensions"]["observation"][0]["values"]
        per_eur = {}
        for k, v in d["dataSets"][0]["series"].items():
            t, val = sorted(v["observations"].items(), key=lambda o: int(o[0]))[-1]
            per_eur[ids[int(k.split(":")[1])]["id"]] = (val[0], days[int(t)]["id"])
        usd, day = per_eur.pop("USD")
        src = "ECB data-api.ecb.europa.eu EXR"
        out["EUR"] = {"rate": round(1 / usd, 6), "date": day, "src": src}
        out["BAM"] = {"rate": round(1.95583 / usd, 6), "date": day, "src": "фиксированный 1.95583 BAM/EUR + " + src}
        for c, (v, dd) in per_eur.items():
            out[c] = {"rate": round(v / usd, 6), "date": dd, "src": src}
    except Exception as e:
        print("ЕЦБ недоступен:", e)
    try:
        by = get_json("https://api.nbrb.by/exrates/rates?periodicity=0", check=False)
        per_byn = {r["Cur_Abbreviation"]: r["Cur_OfficialRate"] / r["Cur_Scale"] for r in by}
        day = by[0]["Date"][:10]
        out["BYN"] = {"rate": per_byn["USD"], "date": day, "src": "НБРБ api.nbrb.by"}
        for c in ("RUB", "KZT", "UAH", "AMD", "MDL"):
            out[c] = {"rate": round(per_byn["USD"] / per_byn[c], 4), "date": day, "src": "НБРБ api.nbrb.by, кросс-курс"}
    except Exception as e:
        print("НБРБ недоступен:", e)
    try:
        r = get_json("https://open.er-api.com/v6/latest/USD", check=False)
        for c in ("GEL", "RSD", "MKD", "ALL", *[k for k in (fallback or {}) if k not in out]):
            if c not in out and c in r["rates"]:
                out[c] = {"rate": r["rates"][c], "date": r["time_last_update_utc"][5:16], "src": "exchangerate-api.com"}
    except Exception as e:
        print("exchangerate-api недоступен:", e)
    out["USD"] = {"rate": 1, "date": datetime.date.today().isoformat(), "src": "-"}
    return {**(fallback or {}), **out}


def estimate(ing, c, fx, level):
    k = fx["eur"][c["currency"]["code"]] / fx["eur"]["BYN"] * level
    return {key: {"price_per_unit": round(g["p"] * k, 2), "unit": UNIT_OF[g["u"]], "pack_size": g.get("pack", 1), "est": 1}
            for key, g in ing.items()}


def run_chain(cc, chain, ing, words):
    try:
        mod = importlib.import_module(chain["parser"])
        return mod.collect(cc, chain, ing, words), None
    except Exception as e:
        traceback.print_exc()
        return {}, f"{type(e).__name__}: {e}"[:200]


def sane(items, base):
    """Отбрасываем живые цены, отличающиеся от оценки больше чем в 4 раза: почти всегда это не тот товар."""
    good = {}
    for k, v in items.items():
        ref = base.get(k, {}).get("price_per_unit")
        if ref and 0.25 <= v["price_per_unit"] / ref <= 4:
            good[k] = v
        else:
            print(f"  отброшено {k}: {v['price_per_unit']} при оценке {ref} ({v.get('product_name')})")
    return good


def proxy_items(c, donor, dstore, dcur, fx, skip=()):
    """Цена-ориентир: живые позиции сети-донора x (уровень цен страны / уровень донора) x курс. -> (items, коэффициент).
    skip - позиции, где парсер донора взял не тот товар."""
    k = level_vs_by(c) / level_vs_by(donor) * fx["eur"][c["currency"]["code"]] / fx["eur"][dcur]
    src = f"{dstore['id']}@{donor['code']}"
    items = {key: {**v, "price_per_unit": round(v["price_per_unit"] * k, 3), "est": "proxy", "src": src,
                   **({"pack_price": round(v["pack_price"] * k, 2)} if v.get("pack_price") else {})}
             for key, v in dstore["items"].items() if key not in skip}
    return items, k


def apply_proxy(s, c, ch, fx, allc, n_ing):
    """Сеть без живых цен с полем proxy получает цены донора из prices/<from>.json (дата - донора). Донор пуст - остаётся оценка."""
    pr = ch["proxy"]
    d = read(os.path.join(OUT, pr["from"].lower() + ".json")) or {}
    ds = next((x for x in d.get("stores", []) if x["id"] == pr["chain"] and x.get("source") == "live" and x.get("items")), None)
    donor = next((x for x in allc if x["code"] == pr["from"]), None)
    if not ds or not donor:
        s["error"] = f"донор {pr['chain']}@{pr['from']} без живых цен"
        return
    items, k = proxy_items(c, donor, ds, d["currency"], fx, pr.get("skip", ()))
    dname = next((x["name"]["en"] for x in donor["chains"] if x["id"] == ds["id"]), ds["id"])
    s.update(source="proxy", items=items, coverage=round(len(items) / n_ing, 3), updated=ds["updated"],
             proxy={**pr, "k": round(k, 4)}, note={"ru": f"ориентир по {dname} {pr['from']}", "en": f"estimate from {dname} {pr['from']}"})
    s.pop("error", None)


def build(c, ing, words, fx, live, old, allc=()):
    today = datetime.date.today().isoformat()
    level = level_vs_by(c)
    base = estimate(ing, c, fx, level)
    oldstores = {s["id"]: s for s in (old or {}).get("stores", [])}
    stores, ratios, store_meds = [], [], []
    for ch in c["chains"]:
        prev = oldstores.get(ch["id"], {})
        s = {"id": ch["id"], "name": ch["name"], "color": ch["color"], "source": "index", "region": ch.get("region"),
             "idx": ch.get("idx"), "updated": today, "coverage": 0, "items": {}}
        if ch.get("parser"):
            items, err = live.get(ch["id"], ({}, "не запускался"))
            items = sane(items, base)
            before = len(prev.get("items", {}))
            if keep_old(before, len(items)) or (err and before):
                print(f"{c['code']} {ch['id']}: собрано {len(items)} при прошлых {before} ({err or 'мало'}), оставляю старые")
                s = {**prev, "name": ch["name"], "color": ch["color"], "stale": 1}
            elif items:
                s.update(source="live", items=items, coverage=round(len(items) / len(ing), 3), updated=today)
            else:
                s["error"] = err or "ничего не найдено"
        if s["source"] == "index" and ch.get("proxy"):  # ориентир не входит в уровень страны и в base: это не её цены
            apply_proxy(s, c, ch, fx, allc, len(ing))
        if s["source"] == "live":
            r = [v["price_per_unit"] / base[k]["price_per_unit"] for k, v in s["items"].items() if k in base]
            ratios += r
            if len(r) >= 8:  # медиана по каждой сети отдельно: иначе сеть с бОльшим покрытием товаров (не обязательно
                store_meds.append(statistics.median(r))  # репрезентативная - парсер есть не у лидеров рынка) перетягивает уровень страны на себя
        stores.append(s)
    if len(ratios) >= 8 and store_meds:  # живых цен достаточно: уровень страны берём из них, оценки подтягиваются к реальности
        level *= statistics.median(store_meds)
        base = estimate(ing, c, fx, level)
    for s in stores:  # в базе - медиана живых цен сетей страны, где есть
        for k in ing:
            vals = [s2["items"][k]["price_per_unit"] for s2 in stores if s2["source"] == "live" and k in s2["items"]]
            if vals:
                base[k] = {"price_per_unit": round(statistics.median(vals), 2), "unit": base[k]["unit"], "pack_size": base[k]["pack_size"], "est": 0}
    return {"cc": c["code"], "currency": c["currency"]["code"], "updated": today, "level_vs_by": round(level, 3),
            "rates": {"date": fx["date"], "per_eur": fx["eur"][c["currency"]["code"]], "src": fx["src"]},
            "base": base, "stores": stores}


def same(a, b):
    """Сравнение без дат: коммит только при реальных изменениях цен."""
    strip = lambda d: json.dumps({**d, "updated": 0, "rates": 0, "stores": [{**s, "updated": 0} for s in d.get("stores", [])]}, sort_keys=True)
    return b is not None and strip(a) == strip(b)


def read(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return None


def main(only):
    countries = [c for c in load("countries.json")["countries"] if not only or c["code"] in only]
    ing, words = load("ing.json"), load("words.json")
    os.makedirs(OUT, exist_ok=True)
    prev = read(os.path.join(OUT, "rates.json")) or {}
    fx = rates(prev if prev.get("eur") else None)
    fx["usd"] = usd_rates(prev.get("usd"))  # для цен подписок: USD -> местная валюта, округление common.PRETTY
    json.dump(fx, open(os.path.join(OUT, "rates.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    jobs = [(c["code"], ch) for c in countries for ch in c["chains"] if ch.get("parser")]
    live = {}
    with cf.ThreadPoolExecutor(max_workers=12) as ex:  # сети параллельно, к одному сайту - последовательно (пауза в fetch)
        futs = {ex.submit(run_chain, cc, ch, ing, words.get(ch.get("lang") or next(c["lang"] for c in countries if c["code"] == cc), {})): ch["id"] for cc, ch in jobs}
        for f in cf.as_completed(futs):
            live[futs[f]] = f.result()
            print(f"{futs[f]}: {len(live[futs[f]][0])} цен {live[futs[f]][1] or ''}", flush=True)
    index = read(os.path.join(OUT, "index.json")) or {"countries": {}}
    allc = load("countries.json")["countries"]
    for c in sorted(countries, key=lambda c: any(ch.get("proxy") for ch in c["chains"])):  # ориентиры - после свежих цен доноров
        path = os.path.join(OUT, c["code"].lower() + ".json")
        old = read(path)
        new = build(c, ing, words, fx, live, old, allc)
        if not same(new, old):
            json.dump(new, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        cur = new if not same(new, old) else old
        index["countries"][c["code"]] = {"updated": cur["updated"], "currency": cur["currency"],
                                         "live": [s["id"] for s in cur["stores"] if s["source"] == "live"],
                                         "proxy": [s["id"] for s in cur["stores"] if s["source"] == "proxy"],
                                         "coverage": max([s["coverage"] for s in cur["stores"] if s["source"] == "live"] or [0])}
    index["updated"] = datetime.date.today().isoformat()
    json.dump(index, open(os.path.join(OUT, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def coverage():
    """Markdown-таблица покрытия из опубликованных prices/*.json - для COVERAGE.md."""
    ing = load("ing.json")
    lines = ["| Страна | Валюта | Сеть | Источник | Продуктов с живой ценой | Покрытие | Дата цен |", "|---|---|---|---|---|---|---|"]
    for c in load("countries.json")["countries"]:
        d = read(os.path.join(OUT, c["code"].lower() + ".json"))
        stores = {s["id"]: s for s in (d or {}).get("stores", [])}
        for ch in c["chains"]:
            s = stores.get(ch["id"], {})
            live = s.get("source") == "live"
            n = len(s.get("items", {}))
            src = ("live" + (" (ориентир)" if ch.get("ref") else "") + (", устарели" if s.get("stale") else "")) if live else (
                f"proxy: {s['note']['ru']}" if s.get("source") == "proxy" else "index" + (f": {s['error']}" if s.get("error") else ""))
            n = n if live else 0
            lines.append(f"| {c['code']} | {c['currency']['code']} | {ch['name'].get('ru') or ch['name']['en']} | {src} | "
                         f"{n} из {len(ing)} | {round(100 * n / len(ing))}% | {s.get('updated', '-') if live else '-'} |")
    return "\n".join(lines)


def summary():
    idx = read(os.path.join(OUT, "index.json")) or {"countries": {}}
    live = sum(len(v["live"]) for v in idx["countries"].values())
    return f"{len(idx['countries'])} стран, живых сетей {live}"


def self_check():
    assert keep_old(20, 5) and not keep_old(20, 6) and not keep_old(0, 0)
    assert abs(level_vs_by({"priceLevel": {"pli": 102.7}}) - 1 / BY_VS_DE) < 1e-9
    assert abs(level_vs_by({"priceLevel": {"gdpPlr": 0.759}}) - 1 / BY_VS_DE) < 1e-9
    assert same({"updated": "a", "rates": 1, "stores": [{"updated": 1, "x": 1}]}, {"updated": "b", "rates": 2, "stores": [{"updated": 2, "x": 1}]})
    assert not same({"updated": "a", "rates": 1, "stores": [{"updated": 1, "x": 1}]}, {"updated": "b", "rates": 2, "stores": [{"updated": 2, "x": 2}]})
    ing = {"milk": {"u": "л", "p": 2.0, "pack": 1}}
    c = {"code": "XX", "currency": {"code": "EUR"}, "priceLevel": {"vsBY": 1.0}, "chains": [{"id": "a", "name": "A", "color": "#fff", "parser": "x"}]}
    fx = {"date": "d", "src": "s", "eur": {"EUR": 1, "BYN": 4}}
    old = {"stores": [{"id": "a", "source": "live", "items": {"milk": {"price_per_unit": 0.9}}, "updated": "old"}]}
    assert build(c, ing, {}, fx, {"a": ({}, "HTTP 403")}, old)["stores"][0]["updated"] == "old"  # упала - старые цены остаются
    got = build(c, ing, {}, fx, {"a": ({"milk": {"price_per_unit": 0.6, "unit": "l"}}, None)}, None)
    assert got["base"]["milk"] == {"price_per_unit": 0.6, "unit": "l", "pack_size": 1, "est": 0} and got["stores"][0]["source"] == "live"
    assert build(c, ing, {}, fx, {"a": ({"milk": {"price_per_unit": 9.0, "unit": "l"}}, None)}, None)["stores"][0]["source"] == "index"  # в 18 раз дороже оценки
    # цена-ориентир: 1.00 EUR у донора с уровнем 100, страна с уровнем 120 и валютой 25 за EUR -> 1.2 * 25 = 30
    cz = {"code": "CZ", "currency": {"code": "CZK"}, "priceLevel": {"pli": 120}}
    de = {"code": "DE", "currency": {"code": "EUR"}, "priceLevel": {"pli": 100}}
    items, k = proxy_items(cz, de, {"id": "lidl_de", "items": {"milk": {"price_per_unit": 1.0, "pack_price": 0.5, "unit": "l"}}}, "EUR",
                           {"eur": {"EUR": 1, "CZK": 25}})
    assert abs(k - 30) < 1e-9 and items["milk"] == {"price_per_unit": 30.0, "pack_price": 15.0, "unit": "l", "est": "proxy", "src": "lidl_de@DE"}
    assert proxy_items(cz, de, {"id": "x", "items": {"milk": {"price_per_unit": 1.0}}}, "EUR", {"eur": {"EUR": 1, "CZK": 25}}, ["milk"])[0] == {}


if __name__ == "__main__":
    if "--check" in sys.argv:
        self_check()
        print("update_all self-check ok")
    elif "--summary" in sys.argv:
        print(summary())
    elif "--coverage" in sys.argv:
        print(coverage())
    else:
        main([a.upper() for a in sys.argv[1:] if not a.startswith("-")])
