#!/usr/bin/env python3
"""Поиск фактов о символе модуля в таблице символов и листинге БЭСМ-6.

Использование:
    python3 ai/карты/listing_lookup.py МОДУЛЬ СИМВОЛ [--all-tabs]

МОДУЛЬ: имя из карты (КИТ, NAKOPL, УКАЧКА) или имя файла без расширения
(kit, nakopl, ukachka). СИМВОЛ ищется без учёта регистра и с учётом
кириллических/латинских омоглифов (C/С, E/Е, O/О и т.п.).

Печатает:
  1) определения символа в .be.tab модуля (адрес и признак entry);
  2) определения в .be.tab модулей-провайдеров, на которые ссылается карта;
  3) строки листинга, где символ выступает внешней ссылкой ('+' в поле
     адреса и адрес внешнего символа);
  4) строки таблицы меток *МЕТ* листинга с адресом символа.

Ни один исходный файл не изменяется.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "ai" / "карты"

# Латинские омоглифы кириллических букв: в листингах и исходниках они
# встречаются вместе (например, C6401 в карте и С6401 в .be.tab).
HOMOGLYPHS = str.maketrans(
    {
        "A": "А", "B": "В", "C": "С", "E": "Е", "H": "Н", "K": "К",
        "M": "М", "O": "О", "P": "Р", "T": "Т", "X": "Х", "Y": "У",
    }
)


def norm(text: str) -> str:
    """Верхний регистр + приведение омоглифов к одному представлению."""
    return text.upper().translate(HOMOGLYPHS)


def load_module_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    readme = HERE / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8", errors="replace")
        pattern = re.compile(
            r"^\|\s*([^|]+?)\s*\|\s*\[карта_[^]]+\]\([^)]+\)\s*\|\s*([A-Za-z0-9_]+\.be)\s*\|",
            re.M,
        )
        for display, befile in pattern.findall(text):
            aliases[norm(display)] = Path(befile).stem
            aliases[norm(Path(befile).stem)] = Path(befile).stem
    for path in list(ROOT.glob("*.be")) + list(ROOT.glob("*.be.tab")) + list(ROOT.glob("*.lst")):
        stem = path.name.split(".")[0]
        aliases.setdefault(norm(stem), stem)
    return aliases


def resolve_module(name: str, aliases: dict[str, str]) -> str | None:
    key = norm(name)
    if key in aliases:
        return aliases[key]
    # Точное совпадение регистра имени файла.
    for candidate in (ROOT / name, ROOT / (name + ".be"), ROOT / (name + ".lst")):
        if candidate.exists():
            return candidate.name.split(".")[0]
    return None


def listing_path(stem: str) -> Path | None:
    for name in (f"{stem}.lst", f"{stem}.be.lst"):
        path = ROOT / name
        if path.exists():
            return path
    return None


TAB_LINE = re.compile(r"^([0-7]{5})\s+([012])\s+(\S+)(?:\s+entry\s+(\S+))?\s*$")
MET_START = "*МЕТ*"
# Символ внешней ссылки стоит в 12-й колонке листинга; после него печатается
# восьмеричный адрес внешнего символа.
EXT_MARK = 12


def tab_defs(path: Path, target: str) -> list[tuple[int, str, str, str | None]]:
    if not path.exists():
        return []
    found = []
    for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        match = TAB_LINE.match(line)
        if not match or norm(match.group(3)) != target:
            continue
        found.append((number, match.group(1), match.group(2), match.group(4)))
    return found


def provider_stems(stem: str, target: str) -> list[tuple[str, int]]:
    """Модули-провайдеры, упомянутые в карте рядом с символом."""
    cards = list(HERE.glob(f"карта_*.md"))
    card = None
    for path in cards:
        if norm(path.stem[6:]) == norm(stem):
            card = path
            break
    if card is None:
        return []
    out: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()
    for line in card.read_text(encoding="utf-8", errors="replace").splitlines():
        if norm(target) not in norm(line):
            continue
        for befile, lineno in re.findall(r"([A-Za-z0-9_]+\.be):(\d+)", line):
            key = (Path(befile).stem, int(lineno))
            if key not in seen:
                seen.add(key)
                out.append(key)
    return out


def word_pattern(target: str) -> re.Pattern[str]:
    escaped = re.escape(target)
    return re.compile(rf"(?<![А-ЯЁA-Za-z0-9]){escaped}(?![А-ЯЁA-Za-z0-9])")


def listing_evidence(path: Path, target: str) -> tuple[list[tuple[int, str, str, str, str]], list[tuple[int, str]]]:
    """Внешние ссылки и строки *МЕТ* для символа."""
    externals: list[tuple[int, str, str, str, str]] = []
    met: list[tuple[int, str]] = []
    pattern = word_pattern(target)
    in_met = False
    for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if MET_START in line:
            in_met = True
        normalized = norm(line)
        if in_met and pattern.search(normalized):
            met.append((number, line.rstrip()))
        if len(line) > EXT_MARK and line[EXT_MARK] == "+":
            if not pattern.search(normalized[60:]):
                continue
            address_match = re.search(r"[0-7]{3,6}", line[EXT_MARK + 1 : 25])
            ext_address = address_match.group(0) if address_match else "?"
            command_address = line[25:31].strip() or "-"
            src_line = line[56:60].strip() or "-"
            externals.append((number, ext_address, command_address, src_line, line.rstrip()))
    return externals, met


def print_evidence(stem: str, symbol: str, all_tabs: bool) -> None:
    target = norm(symbol)
    print(f"МОДУЛЬ: {stem}   СИМВОЛ: {symbol}   (ключ: {target})")

    own_tab = ROOT / f"{stem}.be.tab"
    defs = tab_defs(own_tab, target)
    print(f"\n[1] Определения в {own_tab.name}: {len(defs)}")
    for number, address, flag, entry in defs:
        suffix = f" entry {entry}" if entry else ""
        print(f"  {own_tab.name}:{number}: {address} {flag} {symbol}{suffix}")

    providers = provider_stems(stem, target)
    print(f"\n[2] Модули из карты (ссылки .be:N рядом с символом): {len(providers)}")
    for provider, lineno in providers:
        ptab = ROOT / f"{provider}.be.tab"
        pdefs = tab_defs(ptab, target)
        print(f"  {provider}.be:{lineno} -> {ptab.name}: {len(pdefs)} опр.")
        for number, address, flag, entry in pdefs:
            suffix = f" entry {entry}" if entry else ""
            print(f"    {ptab.name}:{number}: {address} {flag} {symbol}{suffix}")

    if all_tabs:
        print("\n[2b] Все таблицы символов:")
        for ptab in sorted(ROOT.glob("*.be.tab")):
            for number, address, flag, entry in tab_defs(ptab, target):
                suffix = f" entry {entry}" if entry else ""
                print(f"  {ptab.name}:{number}: {address} {flag} {symbol}{suffix}")

    lst = listing_path(stem)
    print(f"\n[3] Листинг: {lst.name if lst else 'ОТСУТСТВУЕТ'}")
    if lst:
        externals, met = listing_evidence(lst, target)
        print(f"  Внешних ссылок ('+' в поле адреса): {len(externals)}")
        for number, ext_address, command_address, src_line, line in externals[:40]:
            print(f"  {lst.name}:{number}: внешний адрес={ext_address}, команда={command_address}, N ИСХ={src_line}")
            print(f"      {line}")
        if len(externals) > 40:
            print(f"  ... ещё {len(externals) - 40} ссылок")
        print(f"  Строк таблицы *МЕТ*: {len(met)}")
        for number, line in met[:8]:
            print(f"  {lst.name}:{number}: {line.strip()}")
        if len(met) > 8:
            print(f"  ... ещё {len(met) - 8} строк")
    else:
        print("  Листинг отсутствует: адреса и внешние ссылки не подтверждаются.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("module", help="имя модуля из карты или имя файла без расширения")
    parser.add_argument("symbol", help="символ для поиска")
    parser.add_argument("--all-tabs", action="store_true", help="искать определение во всех .be.tab")
    args = parser.parse_args()

    aliases = load_module_aliases()
    stem = resolve_module(args.module, aliases)
    if stem is None:
        print(f"ОШИБКА: модуль '{args.module}' не найден.", file=sys.stderr)
        return 2
    print_evidence(stem, args.symbol, args.all_tabs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
