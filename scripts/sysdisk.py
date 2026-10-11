#!/usr/bin/env python3
"""Какой системный диск использует машина — по документации, а не по имени файла.

Проблема: к машине подключается много томов, имена файлов не совпадают с
номерами, которые видит ОС, а копий одного тома может быть несколько.
По `dispak.ini` судить нельзя.

Решение — три источника, каждый документирован:

1. **Директива `ПАК`** (Руководство оператора ОС ДИСПАК, 4.3.12) печатает на
   АЦПУ «СОСТОЯНИЕ ДИСКОВОДОВ»: `НУ ТОМ ТИП СТАТУС ЧЗ`. Строка с типом
   `СИС` — системный том; `СТАТУС` = `В РЕШЕНИИ` / `ЗАНЯТ` / `СВОБОДЕН`.
   Это то, что ОС считает системным диском, — п. 3.2 руководства сообщает
   при загрузке `НМД<НОМЕР МД>`, и по умолчанию это том 2053.
2. **Файлы, реально открытые процессом besm6** (`/proc/<pid>/fd`) — что
   подключено на самом деле, независимо от конфигурации.
3. **`dispak.ini`** — какой файл подключён к какому слоту НУ.

Сверка трёх источников и даёт ответ: том `N` из таблицы `ПАК` стоит в слоте
`НУ`, а к этому слоту подключён файл `F` — значит системный диск это `F`,
даже если `F` называется иначе.

    python3 sysdisk.py                 # разбор и вывод
    python3 sysdisk.py --pack 2053     # снимок таблицы ПАК в stdout

Формат выдачи АЦПУ — UTF-8 (`ACPU/output1.txt`), не koi8-r: читать
надо как есть, иначе вместо букв будет псевдографика.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

SIMH = "~/Yandex.Disk/simh/BESM6"
INI = SIMH + "/OSZAGR/dispak.ini"
ACPU = SIMH + "/ACPU"
# `НУ ТОМ ТИП СТАТУС ЧЗ` — ТИП: СИС (системный) / ОБЩ (общий) / ИНД (индивидуальный)
ROW = re.compile(
    r"^\s*(\d{2})\s+(\d{4})\s+(СИС|ОБЩ|ИНД)?\s*"
    r"(СВОБОДЕН|ЗАНЯТ|В РЕШЕНИИ|ВЫПОЛНЯЕТСЯ|СВОБОДНА)\s*"
)


def acpu_files() -> list[str]:
    out = []
    for name in ("output.txt", "output1.txt"):
        p = os.path.expanduser(f"{ACPU}/{name}")
        if os.path.isfile(p):
            out.append(p)
    return out


def read_acpu_text() -> str:
    """Текст выдачи АЦПУ. Файлы в UTF-8 — конвертировать нельзя."""
    text = []
    for p in acpu_files():
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                text.append(f.read())
        except OSError as e:
            print(f"! не читается {p}: {e}", file=sys.stderr)
    return "\n".join(text)


def parse_pack(text: str) -> list[dict]:
    """Разбор таблицы состояния дисководов из выдачи `ПАК`."""
    rows = []
    for line in text.splitlines():
        m = ROW.match(line)
        if not m:
            continue
        nu, tom, tip, status = m.groups()
        rows.append({"ну": nu, "том": tom, "тип": tip or "?", "статус": status})
    return rows


def besm6_pid() -> int | None:
    try:
        out = subprocess.run(["pgrep", "-x", "besm6"], capture_output=True,
                             text=True, timeout=5).stdout.split()
        return int(out[0]) if out else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def open_images(pid: int) -> list[str]:
    """Файлы-образы, реально открытые процессом besm6."""
    d = f"/proc/{pid}/fd"
    res = []
    try:
        for fd in os.listdir(d):
            try:
                t = os.readlink(os.path.join(d, fd))
            except OSError:
                continue
            if t.endswith(tuple("0123456789")) and ("/MD/" in t or "/ML/" in t
                                                    or "/MB/" in t):
                res.append(t)
    except OSError as e:
        print(f"! не читается {d}: {e}", file=sys.stderr)
    return sorted(set(res))


def ini_slots() -> dict[str, str]:
    """Слот НУ (mdNN) → файл образа из dispak.ini."""
    slots = {}
    path = os.path.expanduser(INI)
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.match(r"\s*attach\s+(?:-\w+\s+)*md(\w+)\s+(\S+)", line)
                if not m:
                    continue
                nu = m.group(1)
                num = int(nu, 8)                     # слот: md07 → НУ 07
                slots[f"{num:02o}"] = os.path.expanduser(
                    m.group(2).replace("~", os.path.expanduser("~")))
    except OSError as e:
        print(f"! не читается {path}: {e}", file=sys.stderr)
    return slots


def report() -> int:
    pid = besm6_pid()
    if pid is None:
        print("! процесс besm6 не найден — машина не запущена")
        return 1

    rows = parse_pack(read_acpu_text())
    if not rows:
        print("! таблица `ПАК` в выдаче АЦПУ не найдена.")
        print("  Выдать её: на операторском терминале (tty1) — директива `ПАК`,")
        print("  ответ `ЕСТЬ`, вывод идёт на АЦПУ.")
        return 1

    slots = ini_slots()
    opened = open_images(pid)

    print(f"процесс besm6: pid {pid}")
    print(f"подключено образов: {len(opened)}\n")

    print("=== СОСТОЯНИЕ ДИСКОВОДОВ (директива ПАК) ===")
    print(f"{'НУ':>4} {'ТОМ':>6} {'ТИП':<5} {'СТАТУС':<12} ФАЙЛ, ПОДКЛЮЧЁННЫЙ В СЛОТ")
    system = []
    for r in rows:
        f = slots.get(r["ну"], "—")
        mark = " ← СИСТЕМНЫЙ" if r["тип"] == "СИС" else ""
        print(f"{r['ну']:>4} {r['том']:>6} {r['тип']:<5} {r['статус']:<12} {f}{mark}")
        if r["тип"] == "СИС":
            system.append((r, f))

    if not system:
        print("\n! строк `СИС` нет — ОС не считает ни один том системным")
        return 1

    print("\n=== ОТВЕТ ===")
    for r, f in system:
        in_use = any(os.path.basename(f) == os.path.basename(o) for o in opened)
        note = "" if in_use else "   (файл НЕ открыт процессом!)"
        print(f"НУ {r['ну']}: том {r['том']} по конфигурации ОС → "
              f"файл {f} [{r['статус']}]{note}")
    print("\nПроверка: том из `ПАК` и имя файла обязаны быть сведены вместе —")
    print("расхождение означает, что в слот подставлен другой образ.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pack", metavar="ТОМ",
                    help="вывести строки таблицы ПАК для одного тома")
    args = ap.parse_args()
    rows = parse_pack(read_acpu_text())
    if args.pack:
        for r in rows:
            if r["том"] == args.pack:
                print(f"НУ {r['ну']} том {r['том']} {r['тип']} {r['статус']}")
        return 0
    return report()


if __name__ == "__main__":
    sys.exit(main())
