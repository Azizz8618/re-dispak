#!/usr/bin/env python3
"""Эвристическая проверка интерпретации: ищет цитирования, где ни один
выделенный(token) из строки карты не встречается в указанной строке .be.

Это НЕ доказательство ошибки, а список кандидатов для ручной ревизии.
Использование: python3 ai/карты/interpretation_check.py > ai/карты/interpretation-candidates.txt
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "ai" / "карты"
CITE = re.compile(r"([A-Za-z0-9_]+\.be):(\d+)(?:-(\d+))?")
TOKEN = re.compile(r"`([^`\n]+)`")


def norm(token: str) -> list[str]:
    out = []
    for part in re.split(r"[\s,;()\[\]/]+", token):
        p = part.strip(" .,:;'’`")
        if len(p) >= 4 and re.search(r"[А-ЯЁа-яёA-Za-z]", p):
            out.append(p)
    return out


def main() -> int:
    candidates = []
    checked = 0
    for mp in sorted(HERE.glob("карта_*.md")):
        text = mp.read_text(encoding="utf-8")
        part = text.split("## 9. КЛЮЧЕВЫЕ ФРАГМЕНТЫ ИСТОЧНИКА")
        if len(part) < 2:
            continue
        section9 = part[1].split("## 10.")[0]
        offset = text.split(section9)[0].count("\n") if section9 else 0
        mapline = 0
        for line in section9.splitlines():
            mapline += 1
            cites = list(CITE.finditer(line))
            if not cites:
                continue
            tokens = []
            for m in TOKEN.finditer(line):
                tokens.extend(norm(m.group(1)))
            tokens = [
                t for t in dict.fromkeys(tokens)
                if not re.search(r"\.(be|txt|md)\b", t) and ":" not in t
            ]
            for c in cites:
                checked += 1
                name, a, b = c.group(1), int(c.group(2)), int(c.group(3) or c.group(2))
                src = ROOT / name
                if not src.exists():
                    candidates.append((mp.name, mapline, f"{name}:{a}", "нет файла"))
                    continue
                lines = src.read_text(encoding="utf-8", errors="ignore").splitlines()
                if a > len(lines) or b > len(lines):
                    continue  # уже ловится crosscheck.py
                window = "\n".join(lines[max(0, a - 2): min(len(lines), b + 2)])
                if tokens and not any(t in window for t in tokens):
                    candidates.append((mp.name, mapline, f"{name}:{a}-{b}" if b != a else f"{name}:{a}", tokens[:3]))
    print(f"Проверено цитирований: {checked}; кандидатов на ревизию: {len(candidates)}")
    for f, ln, ref, info in candidates[:300]:
        print(f"{f}:{ln} | {ref} | {info}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
