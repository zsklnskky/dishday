# Фантастико (BG): сеть публикует для КЗП ежедневный CSV цен всех товаров по магазинам (fantastico.bg/files/kzp/fantastico.csv).
# Берём магазин с самым большим ассортиментом. Цена - промо, если есть, иначе обычная. Названия капсом -> строчные.
import collections, csv, io
from common import by_catalog, fetch, row

URL = "https://www.fantastico.bg/files/kzp/fantastico.csv"


def parse(text):
    rs = list(csv.reader(io.StringIO(text.lstrip("﻿"))))[1:]
    rs = [r for r in rs if len(r) >= 7]
    shop = collections.Counter(r[1] for r in rs).most_common(1)[0][0]
    out = []
    for _, s, name, code, _, price, promo in (r[:7] for r in rs):
        if s != shop or not (promo or price):
            continue
        r = row(name.capitalize(), float(promo or price), url=URL)
        if not r["size"]:  # ponytail: без фасовки в названии - весовой товар (мясо, овощи, витрина), цена за кг
            r["size"], r["unit"] = 1.0, "kg"
        out.append(r)
    return out


def collect(cc, chain, ing, words):
    return by_catalog(parse(fetch(URL, lang="bg")), ing, words, "bg")


if __name__ == "__main__":
    head = '﻿"Населено място","Търговски обект","Наименование на продукта","Код на продукта","Категория","Цена на дребно","Цена в промоция"\n'
    body = ('"68134","Ф30","МЛЯКО ПРЯСНО ВЕРЕЯ 3% 1 Л","002036","6","1.78",""\n'
            '"68134","Ф30","ЛУК ЖЪЛТ ПРОИЗХОД БЪЛГАРИЯ ОПС","1","55","0.65",""\n'
            '"68134","Ф30","ОРИЗ БИСЕРЕН 1 КГ ОРО","2","40","2.55","2.09"\n'
            '"68134","Ф01","МЛЯКО ПРЯСНО ВЕРЕЯ 3% 1 Л","002036","6","1.99",""\n')
    a, b, c = parse(head + body)
    assert a["name"] == "Мляко прясно верея 3% 1 л" and a["price"] == 1.78 and (a["size"], a["unit"]) == (1.0, "l"), a
    assert (b["size"], b["unit"]) == (1.0, "kg") and c["price"] == 2.09, (b, c)
    print("fantastico self-check ok")
