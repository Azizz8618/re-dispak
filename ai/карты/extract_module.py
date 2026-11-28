#!/usr/bin/env python3
"""Собирает проверяемые факты из .be-исходника для карты модуля.

Использование: python3 ai/карты/extract_module.py <module>.be
Результат: ai/карты/raw_<MODULE>.txt (полный перечень меток, ВХОД, ВНЕШ,
шапки комментариев, статистика opcode). Исходник не изменяется.
"""
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_OPS = {"КОНД", "ПАМ", "М", "ДФ", "БЛК", "Р"}

LABEL_RE = re.compile(r"^\s*([А-ЯЁа-яёA-Za-z][А-ЯЁа-яёA-Za-z0-9_∧]*)\s+(\S+)")
OPCODES = {
    "б", "е", "м", "конд", "пам", "конк", "старт", "вход", "внеш", "финиш",
    "ноп", "опре", "гблв", "уств", "апу", "апб", "сч", "счи", "зп", "зпр",
    "и", "или", "не", "нтж", "слц", "сл", "уи", "уиа", "сда", "пб", "по",
    "пе", "пв", "цикл", "кк", "жук", "жукп", "выд", "введ", "выдк", "умн",
    "дел", "выч", "сдв", "форм", "пер", "к", "а", "р", "нач", "кон",
}
STR_RE = re.compile(r"СТАРТ\s*['’`]?([0-7]+)['’`]?", re.I)
# В некоторых исходниках директива написана латинскими гомоглифами: CTAPT.
HOMOGLYPH = str.maketrans({"C": "С", "T": "Т", "A": "А", "P": "Р", "H": "Н"})
DATA_OPS |= {"ВХОД", "ВНЕШ", "СТАРТ"}
DIR_RE = re.compile(r"\b(ВХОД|ВНЕШ)\b\s+(.+)$")

# Имена модулей в кириллице, как в ai/справочник_<МОДУЛЬ>.md.
NAME_MAP = {
    "disp70": "ДИСП70", "vzu": "ВЗУ", "term": "ТЕРМ", "mott": "МОТТ",
    "boek1": "БОЭК1", "visp": "ВИСП", "kachka": "КАЧКА", "kit": "КИТ",
    "ukachka": "УКАЧКА", "diski": "ДИСКИ", "dmlmb": "ДМЛМБ",
    "svyaz7": "СВЯЗЬ7", "osa": "ОСА", "esml": "ЕСМЛ", "nombob": "НОМБОБ",
    "sme": "СМЕ", "smena1": "СМЕНА1", "smena2": "СМЕНА2", "smena3": "СМЕНА3",
    "khlam": "ХЛАМ", "bonbot": "БОНБОТ", "puskach": "ПУСКАЧ",
    "skor1": "СКОР1", "skor2": "СКОР2", "proces": "ПРОЦЕС",
    "prorok": "ПРОРОК", "kanal": "КАНАЛ", "resurs": "РЕСУРС",
    "gens": "ГЕНС", "gens1": "ГЕНС1", "gens2": "ГЕНС2",
    "konfus": "КОНФУС", "avmd": "АВМД", "avml": "АВМЛ",
    "trubka": "ТРУБКА", "dudka": "ДУДКА", "ekvvod": "ЭКВВОД",
    "rukava": "РУКАВА", "rukav1": "РУКАВ1", "rukav2": "РУКАВ2",
    "rukdks": "РУКДКС", "prikaz": "ПРИКАЗ", "uchet": "УЧЕТ",
}


def split_comment(line: str) -> tuple[str, str]:
    """Возвращает (код, комментарий), комментарий после запятой или '*'."""
    m = re.search(r"[,\*]", line)
    if not m:
        return line.rstrip(), ""
    return line[: m.start()].rstrip(), line[m.start() :].strip()


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: extract_module.py <module>.be")
    src = ROOT / sys.argv[1]
    lines = src.read_text(encoding="utf-8").splitlines()
    name = NAME_MAP.get(src.stem.lower(), src.stem.upper())
    out = ROOT / "ai" / "карты" / f"raw_{name}.txt"

    labels, enter, extern, heads = [], [], [], []
    opcodes = Counter()
    start = ""
    for n, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if not start:
            # Директива может быть написана латинскими гомоглифами (CTAPT)
            # и находиться ниже первой строки модуля.
            m = STR_RE.search(raw.translate(HOMOGLYPH))
            if m:
                start = m.group(1)
        if stripped.startswith("*"):
            if stripped.strip("* ").strip():
                heads.append((n, stripped))
            continue
        code, comment = split_comment(raw)
        # Директивы ВХОД/ВНЕШ могут идти как с меткой модуля, так и без неё.
        dm = DIR_RE.search(code)
        if dm:
            symbols = (dm.group(2).strip() + comment).strip().lstrip(",").strip()
            row = (n, symbols, "")
            (enter if dm.group(1) == "ВХОД" else extern).append(row)
            opcodes[dm.group(1)] += 1
            continue
        m = LABEL_RE.match(code)
        if not m:
            continue
        label, opcode = m.group(1), m.group(2).upper()
        if label.lower() in OPCODES:
            # Строка начинается с мнемоники, а не с метки.
            continue
        opcodes[opcode] += 1
        operand = code[m.end() :].strip()
        kind = "данные" if opcode in DATA_OPS else "код/директива"
        labels.append((n, label, opcode, kind, operand, comment))

    def w(f, s=""):
        f.write(s + "\n")

    with out.open("w", encoding="utf-8") as f:
        w(f, f"=== RAW FACTS: {src.name} ({len(lines)} строк) ===")
        w(f, f"СТАРТ: '{start}'" if start else "СТАРТ: не найден")
        w(f, f"МЕТОК: {len(labels)} | ВХОД: {len(enter)} | ВНЕШ: {len(extern)}")
        w(f)
        w(f, "--- СТАТИСТИКА OPCODE (топ 40) ---")
        for op, cnt in opcodes.most_common(40):
            w(f, f"{op:12} {cnt}")
        w(f)
        w(f, "--- ПОЛНЫЙ ПЕРЕЧЕНЬ МЕТОК (строка | метка | opcode | тип | операнд | комментарий) ---")
        for n, label, op, kind, operand, comment in labels:
            w(f, f"{n:5} | {label:16} | {op:10} | {kind:14} | {operand:38} | {comment}")
        w(f)
        w(f, "--- ВХОД (строка | символы | комментарий) ---")
        for n, operand, comment in enter:
            w(f, f"{n:5} | {operand} | {comment}")
        w(f)
        w(f, "--- ВНЕШ (строка | символы | комментарий) ---")
        for n, operand, comment in extern:
            w(f, f"{n:5} | {operand} | {comment}")
        w(f)
        w(f, "--- БЛОКИ КОММЕНТАРИЕВ (шапки) ---")
        for n, text in heads:
            w(f, f"{n:5} | {text}")
    print(f"{out.relative_to(ROOT)}: {len(labels)} меток, {len(enter)} ВХОД, {len(extern)} ВНЕШ")


if __name__ == "__main__":
    main()
