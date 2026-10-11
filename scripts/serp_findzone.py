#!/usr/bin/env python3
"""Найти зону каталога пользователей на томе — бинарным поиском, oracle'ом служит СЕРП.

Задача: выяснить, из какой зоны тома СЕРП (директива `ФИО`) берёт список
пользователей. Номер зоны нигде не записан константой — ни в СЕРП
(`serp*.be`), ни надёжно в ГЕНС: `gens.be:647-648` прямо предупреждает, что
номера зон в КУС — «начальные параметры, которые далее модифицируются в
ЧТСМД/ЧТМД1». Поэтому номер ищется экспериментом на копии тома.

Метод: положить в подозреваемые зоны отличительную заливку и посмотреть,
изменилась ли выдача `ФИО`. Зона с каталогом даст «мусор» в списке
пользователей; зона с кодом СЕРП — падение программы. Дальше — деление
пополам: нули, единицы, мусор.

Работа идёт на копиях в отдельном каталоге, живая машина не затрагивается.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

MD = os.path.expanduser("~/Yandex.Disk/simh/BESM6/MD")
TEST = os.path.expanduser("~/Yandex.Disk/dispak/tests/serp-users-2053/serp-users.b6")
ANSWER = "пасп;\n02610;\nфио;\n41;\n=\n;\nкнц;\n"
MARK = "777777777777"          # отличительная заливка подозреваемых зон


def dump(zones: list[int], vols: str, out: str) -> bool:
    args = ["besmtool", "dump", "2053"]
    for z in zones:
        args += [f"--start={z}", "--length=1"]
    return subprocess.run(args, env=dict(os.environ, BESM6_PATH=vols),
                          capture_output=True).returncode == 0


def oct_zone(z: int) -> str:
    """Номер зоны для besmtool — ВОСЬМЕРИЧНО.

    Номера зон у ОС октальные, и besmtool их такими и принимает: в ответе он
    печатает пару `том/зона`, где второе число — физическая зона, тоже
    восьмеричная. Например `--start=540` (540₈ = 352₁₀) отвечает
    `disk 2030/1034`, то есть физическая 1034₈ = 540₁₀.

    Если передать десятичное число, будет проверена не та зона — поиск
    молча уходит мимо цели.
    """
    return format(z, "o")


def fill(zones: list[int], vols: str, names: list[str]) -> None:
    """Залить зоны отличительной заливкой через besmtool (корректная геометрия)."""
    for name in names:
        for z in zones:
            tmp = f"/tmp/.serp-fill-{z}.bin"
            with open(tmp, "wb") as f:
                f.write(bytes.fromhex(MARK) * 1024)      # 1024 слова по 6 байт
            subprocess.run(["besmtool", "write", name,
                                f"--start={oct_zone(z)}",
                                f"--from-file={tmp}"],
                           env=dict(os.environ, BESM6_PATH=vols),
                           capture_output=True)
            os.unlink(tmp)


def serp_fio(vols: str) -> str:
    p = subprocess.run(["dispak", os.path.basename(TEST)],
                       cwd=os.path.dirname(TEST),
                       env=dict(os.environ, BESM6_PATH=vols),
                       input=ANSWER.encode(), capture_output=True, timeout=300)
    return p.stdout.decode("utf-8", "replace")


def users_of(out: str) -> list[str]:
    """Строки со списком пользователей (шифр + ФИО)."""
    res = []
    for line in out.splitlines():
        s = line.strip()
        if len(s) > 4 and s[:4].isdigit() and not s.startswith("КОНЕЦ"):
            res.append(s)
    return res


def scenario(volume: str, zones: list[int], last: int,
             alias: list[str]) -> str:
    """Отдельный каталог: том с заливкой в подозреваемых зонах.

    `alias` — дополнительные имена, под которыми том кладётся в каталог.
    Нужны, потому что СЕРП обращается к разным томам: `ПРИО` работает с
    МД 2053 (`serp3.be`: `сч МД2053`), а `РИТМ` запрашивает 2030 и 2113 —
    стандартные тома устава ДИСПАК. Каталог пользователей может лежать не
    на томе, который мы назвали 2053.
    """
    d = tempfile.mkdtemp(prefix="serp-bisect-")
    vols = os.path.join(d, "vols")
    os.makedirs(vols)
    src = os.path.join(MD, volume)
    for name in ["2053"] + alias:
        shutil.copy(src, os.path.join(vols, name))
    if os.path.isfile(os.path.join(MD, "2099")):
        shutil.copy(os.path.join(MD, "2099"), os.path.join(vols, "2099"))
    if zones:
        fill(zones, vols, ["2053"] + alias)
    out = serp_fio(vols)
    shutil.rmtree(d, ignore_errors=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--volume", default="2253")
    ap.add_argument("--last", type=int, default=1033,
                    help="старшая граница поиска (зона)")
    ap.add_argument("--alias", nargs="*", default=["2030"],
                    help="дополнительные имена тома (по умолчанию 2030)")
    a = ap.parse_args()

    print("эталонная выдача ФИО:")
    base = scenario(a.volume, [], a.last, a.alias)
    ref = users_of(base)
    for s in ref:
        print("   ", s)
    if not ref:
        print("! эталон пуст — СЕРП не отработал", file=sys.stderr)
        return 1

    lo, hi = 0, a.last
    found = None
    # Поиск по половинам: заливка сразу многих зон — иначе проба по одной
    # зоне требует тысяч запусков. Отличаем три исхода:
    #   выдача изменилась -> каталог внутри этой половины, делим пополам;
    #   программа упала   -> в половине лежит код СЕРП, берём вторую;
    #   выдача та же     -> каталога там нет, берём вторую.
    while hi - lo > 1:
        mid = (lo + hi) // 2
        first = list(range(lo, mid))
        print(f"\nзоны {lo}…{mid - 1} ({len(first)} шт.) …", flush=True)
        out = scenario(a.volume, first, a.last, a.alias)
        cur = users_of(out)
        if cur and cur != ref:
            print("  ВЫДАЧА ИЗМЕНИЛАСЬ — каталог в этой половине")
            hi = mid
            continue
        if not cur:
            print("  программа упала (в половине код СЕРП) — берём вторую")
        else:
            print("  выдача та же — берём вторую половину")
        second = list(range(mid, hi))
        out = scenario(a.volume, second, a.last, a.alias)
        cur = users_of(out)
        if cur and cur != ref:
            print("  ВЫДАЧА ИЗМЕНИЛАСЬ — каталог во второй половине")
            lo = mid
            continue
        print("  и во второй половине нет — исключаем весь диапазон")
        print(f"\nв зонах {lo}…{hi - 1} каталога нет")
        return 1

    print(f"\nОТВЕТ: каталог пользователей — зона {lo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
