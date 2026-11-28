#!/usr/bin/env python3
"""Проверяет полноту карт модулей по сырым фактам из raw_<MODULE>.txt.

Использование: python3 ai/карты/validate.py
Вывод: для каждой карты — число строк, разделов, меток/входов/внешних связей
и количество непокрытых элементов. Выход 1, если есть ошибки.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "ai" / "карты"

HEADINGS = [
    "0. ПАСПОРТ",
    "1. ПОЛНЫЙ ПЕРЕЧЕНЬ МЕТОК",
    "2. ТОЧКИ ВХОДА (ВХОД)",
    "3. ВНЕШНИЕ СВЯЗИ (ВНЕШ)",
    "4. СТРУКТУРА И ГРАФ ПЕРЕХОДОВ",
    "5. ДАННЫЕ, ШКАЛЫ И ТАБЛИЦЫ",
    "6. КОНСТАНТЫ И МАСКИ",
    "7. ЭКСТРАКОДЫ / ПРИКАЗЫ / СООБЩЕНИЯ",
    "8. СВЯЗИ С ДРУГИМИ МОДУЛЯМИ",
    "9. КЛЮЧЕВЫЕ ФРАГМЕНТЫ ИСТОЧНИКА",
    "10. НЕПОДТВЕРЖДЁННОЕ И ВОПРОСЫ",
]


def clean_symbols(field: str) -> list[str]:
    """Отбрасывает части пояснений, попавшие в список после запятой."""
    out = []
    for token in field.split(","):
        t = token.strip()
        if not t or " " in t or "(" in t or ")" in t:
            continue
        out.append(t)
    return out


def raw_facts(path: Path) -> tuple[list[str], list[str], list[str]]:
    labels, enter, extern = [], [], []
    section = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("--- "):
            section = line.split("|")[0].strip("- ")
        elif not line.startswith("--- ") and section and "|" in line and line.strip()[:1].isdigit():
            parts = [p.strip() for p in line.split("|")]
            if section.startswith("ПОЛНЫЙ ПЕРЕЧЕНЬ МЕТОК") and len(parts) >= 3:
                labels.append(parts[1])
            elif section.startswith("ВХОД ") and len(parts) >= 2:
                enter.extend(clean_symbols(parts[1]))
            elif section.startswith("ВНЕШ ") and len(parts) >= 2:
                extern.extend(clean_symbols(parts[1]))
    return labels, enter, extern


def main() -> int:
    raws = sorted(HERE.glob("raw_*.txt"))
    total_errors = 0
    maps = 0
    print(f"{'МОДУЛЬ':14} {'СТРОК':>6} {'РАЗД':>5} {'МЕТОК':>7} {'ПОПУЩ':>7} {'ВХОД':>6} {'ВНЕШ':>6}  СТАТУС")
    for raw in raws:
        module = raw.stem[4:]
        mp = HERE / f"карта_{module}.md"
        if not mp.exists():
            print(f"{module:14} {'—':>6} {'—':>5} {'—':>7} {'—':>7} {'—':>6} {'—':>6}  НЕТ КАРТЫ")
            total_errors += 1
            continue
        maps += 1
        text = mp.read_text(encoding="utf-8")
        lines = text.splitlines()
        heads = [ln for ln in lines if ln.startswith("## ")]
        missing_heads = [h for h in HEADINGS if not any(h in ln for ln in heads)]
        labels, enter, extern = raw_facts(raw)

        def missing(items: list[str]) -> int:
            # Метка считается покрытой, если встречается как отдельное слово.
            return sum(1 for t in items if not re.search(r"(?<![А-ЯЁа-яёA-Za-z0-9])" + re.escape(t) + r"(?![А-ЯЁа-яёA-Za-z0-9])", text))

        ml, me, mx = missing(labels), missing(enter), missing(extern)
        footer = any(ln.startswith("Источник:") for ln in lines)
        bad = bool(missing_heads) or not footer or ml or me or mx
        status = "OK" if not bad else "НЕПОЛНА"
        if bad:
            total_errors += 1
        print(f"{module:14} {len(lines):6} {len(heads):5} {len(labels):7} {ml:7} {me:6} {mx:6}  {status}")
        if missing_heads:
            print(f"   нет разделов: {missing_heads}")
        if not footer:
            print("   нет строки 'Источник:'")
    print(f"\nКарт: {maps}/{len(raws)}. Ошибок: {total_errors}.")
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
