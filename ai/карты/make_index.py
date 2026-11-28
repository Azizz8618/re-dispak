#!/usr/bin/env python3
"""Собирает индекс карт ai/карты/README.md из созданных карт и raw-фактов.

Использование: python3 ai/карты/make_index.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "ai" / "карты"

CORE_GROUPS = [
    ("Центральный резидент и ввод", ["ДИСП70", "ВЗУ", "ТЕРМ", "МОТТ"]),
    ("Управление памятью и задачами", ["БОЭК1", "ВИСП", "КАЧКА", "КИТ", "УКАЧКА"]),
    ("Внешние устройства и связь", ["ДИСКИ", "ДМЛМБ", "СВЯЗЬ7", "ОСА", "ЕСМЛ"]),
    ("Нерезидентные системы", ["НОМБОБ", "СМЕ", "СМЕНА1", "СМЕНА2", "СМЕНА3", "ХЛАМ"]),
    ("Приказы и задачи", ["БОНБОТ", "ПУСКАЧ", "СКОР1", "СКОР2", "ПРОЦЕС", "ПРОРОК", "КАНАЛ", "РЕСУРС"]),
    ("Генератор и вспомогательные", ["ГЕНС", "ГЕНС1", "ГЕНС2", "КОНФУС", "АВМД", "АВМЛ", "ТРУБКА", "ДУДКА", "ЭКВВОД"]),
]
ALL = sorted(p.stem[4:] for p in HERE.glob("raw_*.txt"))
SEEN = {m for _, mods in CORE_GROUPS for m in mods}
GROUPS = [(name, mods) for name, mods in CORE_GROUPS if any((HERE / f"raw_{m}.txt").exists() for m in mods)]
GROUPS.append(("Остальные модули проекта", [m for m in ALL if m not in SEEN]))


def facts(module: str) -> tuple[str, int, int, int]:
    p = HERE / f"raw_{module}.txt"
    src, lines, enter, ext = "—", 0, 0, 0
    if p.exists():
        text = p.read_text(encoding="utf-8")
        m = re.search(r"RAW FACTS: (\S+) \((\d+) строк\)", text)
        if m:
            src, lines = m.group(1), int(m.group(2))
        m = re.search(r"ВХОД: (\d+) \| ВНЕШ: (\d+)", text)
        if m:
            enter, ext = int(m.group(1)), int(m.group(2))
    return src, lines, enter, ext


def main() -> None:
    rows = []
    for group, modules in GROUPS:
        rows.append(f"## {group}\n")
        rows.append("| Модуль | Карта | Исходник | Строк | ВХОД | ВНЕШ |")
        rows.append("|---|---|---|---:|---:|---:|")
        for module in modules:
            mp = HERE / f"карта_{module}.md"
            src, lines, enter, ext = facts(module)
            link = f"[карта_{module}.md](карта_{module}.md)" if mp.exists() else "НЕТ"
            rows.append(f"| {module} | {link} | {src} | {lines} | {enter} | {ext} |")
        rows.append("")
    body = "\n".join(rows)
    out = (
        "# КАРТЫ МОДУЛЕЙ ОС ДИСПАК\n\n"
        "Максимально подробные структурные карты модулей, составленные из текстов "
        "`.be` с привязкой к номерам строк. Формат описан в [ФОРМАТ.md](ФОРМАТ.md). "
        "Сырые факты (полный перечень меток, ВХОД, ВНЕШ) лежат в `raw_<МОДУЛЬ>.txt`, "
        "проверка полноты — `python3 ai/карты/validate.py`.\n\n"
        "Карты дополняют [справочники](../СПРАВОЧНИКИ.md): справочник даёт смысл, "
        "карта — полную структуру со всеми метками и связями.\n\n"
        + body
        + "\nИсходники `.be` не изменялись. Карты составлены по тексту модулей.\n"
    )
    (HERE / "README.md").write_text(out, encoding="utf-8")
    print(f"ai/карты/README.md: {len(out.splitlines())} строк")


if __name__ == "__main__":
    main()
