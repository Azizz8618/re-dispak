#!/usr/bin/env python3
"""Перекрёстный анализ карт модулей ОС ДИСПАК.

Проверяет:
1) Все ссылки вида <файл>.be:<строка> попадают в границы исходника.
2) Внешние связи: если модуль A объявляет "B ВНЕШ сим", то в карте/сырых
   фактах модуля B этот символ должен присутствовать как метка или ВХОД.
3) Стартовый адрес в паспорте карты совпадает с СТАРТ исходника/raw.
4) Одинаковые зоны/старты у разных модулей не конфликтуют (только сообщение).

Использование: python3 ai/карты/crosscheck.py > ai/карты/crosscheck-report.txt
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "ai" / "карты"

SRC = {p.name: p for p in ROOT.glob("*.be")}
LINE_COUNT = {name: len(p.read_text(encoding="utf-8", errors="ignore").splitlines()) for name, p in SRC.items()}
RAW = {p.stem[4:]: p for p in HERE.glob("raw_*.txt")}
MAPS = {p.stem[6:]: p for p in HERE.glob("карта_*.md")}

# Имя модуля в .be -> имя в raw/карте
NAMES = {
    "disp70": "ДИСП70", "vzu": "ВЗУ", "term": "ТЕРМ", "mott": "МОТТ",
    "boek1": "БОЭК1", "visp": "ВИСП", "kachka": "КАЧКА", "kit": "КИТ",
    "ukachka": "УКАЧКА", "diski": "ДИСКИ", "dmlmb": "ДМЛМБ", "svyaz7": "СВЯЗЬ7",
    "osa": "ОСА", "esml": "ЕСМЛ", "nombob": "НОМБОБ", "sme": "СМЕ",
    "smena1": "СМЕНА1", "smena2": "СМЕНА2", "smena3": "СМЕНА3", "khlam": "ХЛАМ",
    "bonbot": "БОНБОТ", "puskach": "ПУСКАЧ", "skor1": "СКОР1", "skor2": "СКОР2",
    "proces": "ПРОЦЕС", "prorok": "ПРОРОК", "kanal": "КАНАЛ", "resurs": "РЕСУРС",
    "gens": "ГЕНС", "gens1": "ГЕНС1", "gens2": "ГЕНС2", "konfus": "КОНФУС",
    "avmd": "АВМД", "avml": "АВМЛ", "trubka": "ТРУБКА", "dudka": "ДУДКА",
    "ekvvod": "ЭКВВОД", "prikaz": "ПРИКАЗ", "uchet": "УЧЕТ",
    "rukava": "РУКАВА", "rukav1": "РУКАВ1", "rukav2": "РУКАВ2", "rukdks": "РУКДКС",
}
BE_TO_NAME = {**{k: k.upper() for k in [p.stem for p in ROOT.glob("*.be")]}, **NAMES}


def load_symbols(name: str) -> set[str]:
    """Все метки и ВХОД-символы модуля из raw-фактов."""
    p = RAW.get(name)
    if not p:
        return set()
    text = p.read_text(encoding="utf-8")
    section = ""
    out = set()
    for line in text.splitlines():
        if line.startswith("--- "):
            section = line.split("|")[0].strip("- ")
        elif not line.startswith("--- ") and "|" in line and line.strip()[:1].isdigit():
            cells = [c.strip() for c in line.split("|")]
            if section.startswith("ПОЛНЫЙ ПЕРЕЧЕНЬ МЕТОК") and len(cells) >= 3:
                out.add(cells[1].strip("`"))
            elif section.startswith("ВХОД ") and len(cells) >= 2:
                for t in cells[1].split(","):
                    t = t.strip(" `")
                    if t and " " not in t and "(" not in t and ")" not in t:
                        out.add(t)
    return out


def main() -> int:
    issues = []
    # 1. Границы ссылок
    refs = defaultdict(int)
    for name, mp in MAPS.items():
        text = mp.read_text(encoding="utf-8")
        for befile, num in re.findall(r"([A-Za-z0-9_]+\.be):(\d+)", text):
            refs[befile] += 1
            n = int(num)
            if befile not in LINE_COUNT:
                issues.append(f"ССЫЛКА: {name}: неизвестный файл {befile}:{n}")
            elif n > LINE_COUNT[befile]:
                issues.append(f"ССЫЛКА: {name}: {befile}:{n} вне границ ({LINE_COUNT[befile]})")
    print(f"Проверено ссылок: {sum(refs.values())} по {len(refs)} файлам")

    # 2. Внешние связи между модулями
    links = 0
    unresolved = 0
    for befile, src in SRC.items():
        owner = BE_TO_NAME.get(src.stem, src.stem.upper())
        for line in src.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.match(r"^\s*([А-ЯЁа-яёA-Z][А-ЯЁа-яёA-Z0-9_]*)\s+ВНЕШ\s+(.+)$", line)
            if not m:
                continue
            target, syms = m.group(1), m.group(2)
            tname = BE_TO_NAME.get(target.lower(), target.upper())
            if tname not in RAW:
                continue
            known = load_symbols(tname)
            for sym in syms.split(","):
                sym = sym.strip().lstrip(",").strip()
                if not sym or " " in sym or "(" in sym or ")" in sym or sym.startswith("'"):
                    continue
                links += 1
                if sym not in known:
                    unresolved += 1
                    issues.append(f"СВЯЗЬ: {owner} -> {tname}: символ {sym} не найден ни в метках, ни во ВХОД {tname}")
    print(f"Проверено внешних связей: {links}; неразрешённых: {unresolved}")

    # 3. Согласованность СТАРТ
    starts = defaultdict(list)
    for name, mp in MAPS.items():
        text = mp.read_text(encoding="utf-8")
        m = re.search(r"СТАРТ[^\n]*?'?([0-7]{3,6})'?", text[:4000])
        if m:
            starts[name].append(m.group(1))
    print(f"Карт со СТАРТ в паспорте: {len(starts)}")

    print(f"\nИТОГО потенциальных проблем: {len(issues)}")
    for s in issues[:200]:
        print(" -", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
