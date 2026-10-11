#!/usr/bin/env python3
"""Выдача каталога тома программой СЕРП из тестов пакетного эмулятора dispak.

Готовую программу выдачи каталога писать не нужно — она уже есть:
`dispak/tests/serp-keys-2053/serp-keys.b6` — это СЕРП (сервисная программа
ДИСПАК) с директивой `КЛЮ`, которая печатает каталог имён задач тома
(«ОГЛ»). Тот же приём печатает пользователей (`ФИО`) и паспорта (`ПАСП`).

Запуск на копиях томов, живая машина не нужна и не затрагивается:

    BESM6_PATH=<каталог с копиями томов> dispak serp-keys.b6

Каталог томов — копии образов из `~/Yandex.Disk/simh/BESM6/MD`. Имя файла
значимо: `serp-keys-2053` ищет именно том **2053** (`serp3.be`: `сч МД2053`
в директиве `ПРИ`). Если рабочий том называется иначе (у нас системный том
2053 подключён как файл `MD/2253`), его надо положить под именем `2053`:

    vol/2053 = копия MD/2253   # так каталог читается с рабочего тома

Директивы СЕРП (3-буквенные, `serp.be:258-307`):

| директива | назначение |
|---|---|
| `ФИО` | **список пользователей** тома: фамилии и их шифры (`ФИОРАЗ`) |
| `КЛЮ` | каталог имён задач с паспортами и шифрами (`КЛЮЧ`) |
| `ПАС` | паспорта задач (`ПАСП`) |
| `ПРИ` | **запись**: каталог приоритетных шифров (`ПРИО`) |
| `ТОМ` | выбор тома (в ПРИО печатается как `ТОМ- <N>`) |

`КЛЮЧАР` — не директива, а строка-подсказка (`serp.be:935`), которую ПРИО
печатает перед вводом (`serp.be:873, 898`); директивы с таким именем в
таблице нет.

СЕРП умеет **записывать**: директива `ПРИ` (ПРИО) заносит шифр в каталог
приоритетных шифров (Dispak-description.md 5.2.2: «слова 700—777(8)
размещен каталог приоритетных шифров… информация в него заносится
директивой "ПРИО" сервисной программы "СЕРП"»).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

MD = os.path.expanduser("~/Yandex.Disk/simh/BESM6/MD")
TESTS = os.path.expanduser("~/Yandex.Disk/dispak/tests")


def find_test(name: str) -> str:
    p = os.path.join(TESTS, name, name.rsplit("-", 1)[0] + ".b6")
    if os.path.isfile(p):
        return p
    cands = [os.path.join(TESTS, n) for n in os.listdir(TESTS)
             if n.startswith(name)]
    for c in cands:
        for f in os.listdir(c):
            if f.endswith(".b6"):
                return os.path.join(c, f)
    raise SystemExit(f"! тест {name} не найден в {TESTS}")


def stage(volume: str, workdir: str, extra: list[str] | None = None) -> str:
    """Каталог томов для BESM6_PATH: рабочий том под именем 2053 + служебные."""
    vols = os.path.join(workdir, "vols")
    os.makedirs(vols, exist_ok=True)
    src = volume if os.path.isabs(volume) else os.path.join(MD, volume)
    if not os.path.isfile(src):
        raise SystemExit(f"! образа тома нет: {src}")
    # том 2053 — тот, к которому обращается СЕРП
    shutil.copy(src, os.path.join(vols, "2053"))
    for n in (extra or []):
        s = n if os.path.isabs(n) else os.path.join(MD, n)
        if os.path.isfile(s):
            shutil.copy(s, os.path.join(vols, os.path.basename(n)))
        else:
            print(f"! нет тома {n} — пропускаю", file=sys.stderr)
    return vols


def run(test: str, volume: str, answer: str = "пасп;\n02610;\nключ;\nогл;\n;\nкнц;\n",
        extra: list[str] | None = None, timeout: int = 300) -> str:
    src = find_test(test)
    with tempfile.TemporaryDirectory(prefix="serp-") as tmp:
        vols = stage(volume, tmp, extra)
        inp = os.path.join(tmp, os.path.basename(src))
        shutil.copy(src, inp)
        env = dict(os.environ, BESM6_PATH=vols)
        p = subprocess.run(["dispak", os.path.basename(inp)],
                           cwd=tmp, env=env, input=answer.encode(),
                           capture_output=True, timeout=timeout)
        out = p.stdout.decode("utf-8", "replace")
        err = p.stderr.decode("utf-8", "replace")
        if err.strip():
            out += "\n[stderr] " + err.strip()
        return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--volume", default="2253",
                    help="образ рабочего тома (по умолчанию 2253)")
    ap.add_argument("--test", default="serp-keys-2053",
                    help="тест dispak с нужной директивой СЕРП")
    ap.add_argument("--users", action="store_true",
                    help="каталог пользователей (ФИО) вместо ключей")
    ap.add_argument("--answer", help="своя последовательность ввода")
    ap.add_argument("--extra", nargs="*", default=["2099"],
                    help="дополнительные тома (по умолчанию 2099)")
    a = ap.parse_args()

    test = a.test
    answer = a.answer
    if answer is None:
        if a.users:
            answer = "пасп;\n02610;\nф;\n12;\n=\n41;\n=\n52;\n=\n;\nкнц;\n"
        print(run(test, a.volume, answer or "", a.extra))
        return 0
    print(run(test, a.volume, answer, a.extra))
    return 0


if __name__ == "__main__":
    sys.exit(main())
