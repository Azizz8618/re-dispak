#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_extract_codes.py -- построение полной таблицы экстракодов ОС ДИСПАК
из распознанной книги Тюрина 1985.

Вход:
  ocr/page-0001.txt ... page-0338.txt   (338 OCR-страниц)
  ../tyurin1985-full.txt                (сводный файл, для справки)

Источники внутри книги:
  1) Приложение П «ЭКСТРАКОДЫ OC ДИСПАК ДЛЯ ПОЛЬЗОВАТЕЛЕЙ»,
     PDF-страницы ~264-291.  Записи имеют вид
         «2.9. Запрос шифра задачи: ИР 050 A, где АИСП = 100с.»
     при этом NNN (050) -- восьмеричный код экстракода (Э50),
     а MMM (100с) -- информационное слово; конечный «с/3/5/g/»/,...»
     -- OCR-искажение восьмеричного индекса «8» («100_8»).
     Описание -- 2..5 следующих строк до следующей записи.
  2) «СПИСОК ЭКСТРАКОДОВ», PDF-страницы 331-335 -- авторский указатель
     книги с ЧИСТЫМИ 4-разрядными восьмеричными словами:
         «ИР 950 A, где АИСП:    0100 -- запрос шифра задачи 263»
     （«950» = OCR «Э50»）.  Используется как авторитетный источник
     для нормализации кодов/слов и для описаний.

OCR-ошибки, которые учитываются:
  A/4, 0/O, I/1, пропущенные пробелы,
  ИР -> MP/НР/ПР/nP/uP/UP/IR/1P/ЭР/HP,
  АИСП -> АИСИП / АЙСП / АИСИ / АНСП / AHCI / AMICI / АИСП.,
  «=» -> «==», «. =»,
  индекс «8» -> s/3/5/g/,/;/»/в/b/а/%,
  «где» -> «rye»/«rae»/«tae»/«те ~—».

Выход (в каталоге скрипта):
  extract-codes.md    -- полная таблица + список испорченных OCR-записей
  extract-codes.json  -- {"Э050:0114": {"desc":..., "page":..., ...}}
  README.md           -- метод и исходники
  logs/tyurin_extract_parse.txt -- лог (в re-dispak/logs/)

Запуск:  python3 parse_extract_codes.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
OCR_DIR = HERE / "ocr"
REPO = HERE.parent.parent                      # .../re-dispak
LOG_PATH = REPO / "logs" / "tyurin_extract_parse.txt"
MD_PATH = HERE / "extract-codes.md"
JSON_PATH = HERE / "extract-codes.json"
README_PATH = HERE / "README.md"
RUKAVA = REPO / "rukava.be"

# --------------------------------------------------------------------------
# Регулярные выражения / нормализация
# --------------------------------------------------------------------------

# Варианты написания «ИР» в OCR (>=2 символов, чтобы не ловить одиночные I).
IR_RE = r"(?:ИР|МР|НР|ПР|пР|nP|uP|UP|IR|1P|IP|ЭР|HP|IР|ЇР|1Р|МП)"
# Варианты написания «АИСП».
AIP_RE = (
    r"(?:АИСИП|АИСП|АЙСП|АИСИ|АНСП|АИСП|AHCI|AMICI|АИСП|АИСИП|АИСП|АИСП)"
)

REC_RE = re.compile(
    rf"(?P<ir>{IR_RE})\s*\.?\s*"
    rf"(?P<code>\d{{2,3}})\s*[АA]?\s*"
    rf"(?P<gap>[^\n]{{0,64}}?)"
    rf"(?P<aip>{AIP_RE})\s*\.?\s*=*\s*"
    rf"(?P<val>\S+)"
)

# Глифы, в которые OCR превращает восьмеричный индекс «8» (subscript).
SUBSCRIPTION_GLYPHS = set("sSgG,;»%вbа”)")
# Цифры 3 и 5 тоже часто являются искажённым индексом «8».
SUBSCRIPTION_DIGITS = set("35")

# Заголовок раздела: «2.9.», «7.7.2,», «1.3» и т.п.
SECTION_RE = re.compile(r"^\s*\d+(?:[.,]\d+){0,2}[.,]?\s*")

# Строка-нумератор страницы внизу OCR-страницы.
FOOTER_RE = re.compile(r"^\s*\d{1,4}\s*$")

# Индексный указатель: «ИР 950 A, где АИСП:»  (950 -> Э50, 354 -> Э54, ...)
INDEX_HEAD_RE = re.compile(
    rf"(?P<ir>{IR_RE})\s*\.?\s*(?P<code>\d{{3}})\s*[АA]?\s*,?\s*где",
)
INDEX_HEAD_RE2 = re.compile(rf"(?P<ir>{IR_RE})\s*\.?\s*(?P<code>\d{{3}})\s*[АA]?\s*[—-]")
# Строка вида «0100 -- описание … 263»
INDEX_ITEM_RE = re.compile(
    r"^\s*[`'\-–—]?\s*(?P<info>[0-9]{1,6})\s*(?:[—–-]|\.)\s*(?P<desc>.+?)\s*$"
)
# Строка указателя с возможным мусором в начале («` 0147 — …»).
ITEM_LIKE_RE = re.compile(r"^\s*[`'\-–—]?\s*[0-9]{1,6}\s*[—–-]")


def norm_ws(s: str) -> str:
    """Схлопнуть пробелы и починить переносы слов по дефису."""
    s = re.sub(r"-\s*\n\s*", "", s)
    s = s.replace("\n", " ")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def clean_title(s: str) -> str:
    """Убрать номер раздела и завершающие знаки в заголовке записи."""
    s = SECTION_RE.sub("", s)
    s = s.strip().strip(":;—–-").strip()
    return norm_ws(s)


def desc_key(s: str) -> str:
    """Ключ для сравнения описаний (регистр/пунктуация не важны)."""
    s = SECTION_RE.sub("", s)
    s = re.sub(r"[^0-9a-zа-яё]+", " ", s.lower(), flags=re.UNICODE)
    return " ".join(s.split())


def normalize_info(raw: str, allow_tail_rule: bool = True) -> tuple[str | None, list[str]]:
    """
    Привести информационное слово к восьмеричным цифрам.

    ``allow_tail_rule`` включает эвристику «хвост 3/5 в 4+ разрядном
    числе -- искажённый индекс 8».  Она нужна только для приложения:
    в авторском указателе числа набраны чистыми 4 разрядами и
    «0003» -- это действительно 3, а не «000_8».

    Возвращает (цифры, список флагов искажений).
    """
    flags: list[str] = []
    s = raw.strip().strip(".,;:»\"'").strip()
    s = re.sub(r"\s+", "", s)

    if not s:
        return None, ["empty"]

    # Не число (N+10, 100+п, М, «адрес…», B777777 и т.п.).
    if not re.match(r"^[0-7]", s):
        return None, [f"non-numeric:{s}"]

    m = re.match(r"^([0-7]+)(.*)$", s, re.S)
    assert m
    digits, rest = m.group(1), m.group(2)

    if rest:
        if all(c in SUBSCRIPTION_GLYPHS for c in rest):
            flags.append("subscript-glyph")
        elif rest in SUBSCRIPTION_DIGITS:
            # Конечная 3/5 после 2..6 цифр -- искажённый индекс «8».
            if 2 <= len(digits) <= 6:
                flags.append("subscript-3or5")
            else:
                return None, [f"junk:{rest}"]
        elif re.fullmatch(r"[sSgG,;»%вbа”)+]*", rest):
            flags.append("subscript-glyph")
        else:
            # «100%» -- '%' тоже искажение индекса.
            if rest == "%":
                flags.append("subscript-glyph")
            else:
                return None, [f"junk:{rest}"]

    # В приложении 4+ цифр, оканчивающиеся на 3/5, -- почти всегда
    # «NNN_8», где последний символ -- искажённый индекс
    # (1233 -> 123_8, 777775 -> 77777_8).
    if allow_tail_rule and len(digits) >= 4 and digits[-1] in SUBSCRIPTION_DIGITS:
        digits = digits[:-1]
        if "subscript-tail" not in flags:
            flags.append("subscript-tail")

    # В указателе OCR иногда читает ведущий «0» как «6»/«9»:
    # «6051» = «0051».  Остальные разряды при этом восьмеричные.
    if len(digits) == 4 and digits[0] in "69" and all(c in "01234567" for c in digits[1:]):
        digits = "0" + digits[1:]
        flags.append("leading-6or9-ocr")

    # Нормализация «4»->«1» в начале 3-разрядного слова («465» -> «165»)
    # делается позже, по указателю (см. match_index).
    return digits, flags


def normalize_code(raw: str) -> str | None:
    """Код экстракода -> 3 восьмеричные цифры (050, 062, 073 …).

    В авторском указателе OCR читает «э» как 9 или 3:
    «ИР 950» = Э50, «ИР 354» = Э54, «ИР 363» = Э63.
    """
    s = str(raw).strip()
    if len(s) == 3 and s[0] in "93" and all(c in "01234567" for c in s[1:]):
        s = "0" + s[1:]
    try:
        return format(int(s, 8), "03o")
    except ValueError:
        return None


def code_to_idx(code: str) -> str:
    """«050» -> «Э050»."""
    return "Э" + code


def info_key(info: str) -> str:
    """Канонический ключ для сравнения и объединения."""
    return format(int(info, 8), "o")


def make_key(code: str, info: str) -> str:
    """Ключ JSON: Э050:0114."""
    try:
        i = int(info, 8)
    except ValueError:
        return f"{code_to_idx(code)}:{info}"
    return f"{code_to_idx(code)}:{format(i, '04o')}"


# --------------------------------------------------------------------------
# Структуры
# --------------------------------------------------------------------------

@dataclass
class Record:
    code: str                       # «050»
    info: str                       # восьмеричные цифры
    desc: str
    page: int                       # номер PDF-страницы
    source: str                     # "appendix" | "index"
    title: str = ""                  # заголовок записи (для сопоставления)
    confidence: str = "confident"
    flags: list[str] = field(default_factory=list)
    raw: str = ""
    book_page: int | None = None    # печатная страница (из указателя)
    detail: str = ""                # развёрнутое описание из приложения
    corrected_info: str | None = None

    def canonical(self) -> tuple[str, str]:
        return info_key(self.code), info_key(self.info)


# --------------------------------------------------------------------------
# Парсер 1: записи приложения «ИР NNN … АИСП … MMM»
# --------------------------------------------------------------------------

def parse_appendix_page(page: int, lines: list[str]) -> list[Record]:
    out: list[Record] = []
    n = len(lines)
    for i in range(n):
        line = lines[i]
        nxt = lines[i + 1] if i + 1 < n else ""
        window = line + " " + nxt

        for m in REC_RE.finditer(window):
            # ИР должно начинаться в строке i (иначе запись будет
            # найдена дважды -- на i и на i-1).
            if m.start("ir") >= len(line):
                continue

            ir_raw = m.group("ir")
            code_raw = m.group("code")
            code = normalize_code(code_raw)
            if code is None:
                continue
            val_raw = m.group("val")

            info, flags = normalize_info(val_raw)
            if info is None:
                # Записи с формулой/адресом вместо числа в основную
                # таблицу не попадают, но попадают в лог.
                out.append(Record(
                    code=code, info="",
                    desc=clean_title(line[: m.start("ir")]),
                    page=page, source="appendix", confidence="low",
                    title=clean_title(line[: m.start("ir")]),
                    flags=flags + ["no-numeric-info"],
                    raw=window[m.start(): m.end()].strip(),
                ))
                continue

            # Описание: заголовок до «ИР» + 2..5 следующих строк.
            title = clean_title(line[: m.start("ir")])
            value_on_next = m.start("val") >= len(line)
            start = i + (1 if value_on_next else 0) + 1
            body_lines: list[str] = []
            for j in range(start, min(start + 5, n)):
                cand = lines[j].strip()
                if not cand or FOOTER_RE.match(cand):
                    break
                # Любая новая запись «ИР NNN…» обрывает описание --
                # даже если OCR исказил «где/АИСП» и REC_RE её не ловит.
                if re.search(IR_RE + r"\s*\.?\s*\d{2,3}", cand):
                    break
                if REC_RE.search(cand) or INDEX_HEAD_RE.search(cand):
                    break
                if re.match(r"^\s*\d+(?:\.\d+){1,3}\s*\.?\s*\S", cand):
                    break
                body_lines.append(cand)
            body = norm_ws(" ".join(body_lines))
            if body:
                if len(body) > 900:
                    body = body[:900].rsplit(" ", 1)[0] + " …"
                desc = norm_ws(title + " — " + body) if title else body
            else:
                desc = title

            if ir_raw not in ("ИР",):
                flags.append("ir-ocr:" + ir_raw)
            if m.group("aip") not in ("АИСП",):
                flags.append("aip-ocr:" + m.group("aip"))
            if "=" not in m.group("gap")[-4:] and m.group("gap").strip() not in ("",):
                if "==" in window[m.start("aip"): m.start("val")]:
                    flags.append("double-eq")
            if value_on_next:
                flags.append("line-break")

            out.append(Record(
                code=code,
                info=info,
                desc=desc,
                page=page,
                source="appendix",
                confidence="low" if flags else "confident",
                title=title,
                flags=flags,
                raw=window[m.start(): m.end()].strip(),
                detail=body,
            ))
    return out


# --------------------------------------------------------------------------
# Парсер 2: авторский указатель «СПИСОК ЭКСТРАКОДОВ» (стр. 331-335)
# --------------------------------------------------------------------------

def parse_index_page(page: int, lines: list[str],
                     initial_code: str | None = None) -> tuple[list[Record], str | None]:
    out: list[Record] = []
    current_code: str | None = initial_code
    n = len(lines)
    j = 0
    while j < n:
        line = lines[j].rstrip("\n")
        h = INDEX_HEAD_RE.search(line) or INDEX_HEAD_RE2.search(line)
        if h:
            current_code = normalize_code(h.group("code"))
            j += 1
            continue
        if current_code is None or re.match(r"^\s*АИСП\s*[>=]", line, re.I):
            j += 1
            continue

        it = INDEX_ITEM_RE.match(line)
        if not it:
            j += 1
            continue

        info, flags = normalize_info(it.group("info"), allow_tail_rule=False)
        j += 1
        if info is None:
            continue

        # Описание может занимать 2-3 строки; печатный номер страницы
        # часто стоит на последней строке.
        parts = [it.group("desc").strip()]
        while j < n and len(parts) < 2:
            nxt = lines[j].strip()
            if not nxt or FOOTER_RE.match(nxt):
                j += 1
                continue
            if ITEM_LIKE_RE.match(nxt) or INDEX_HEAD_RE.search(nxt) \
                    or INDEX_HEAD_RE2.search(nxt):
                break
            if re.match(r"^\s*АИСП\s*[>=]", nxt, re.I):
                break
            # Не тащим в описание следующий заголовок раздела.
            if re.match(r"^\s*ИР\s+\d{3}", nxt, re.I):
                break
            parts.append(nxt)
            j += 1

        desc = norm_ws(" ".join(parts))
        bm = re.search(r"\s(\d{1,3})[\s.;`'\-–—,:%]*[а-яa-z]?[\s.;`'\-–—,:%]*$", desc)
        book_page = None
        if bm and 40 <= int(bm.group(1)) <= 340:
            book_page = int(bm.group(1))
            desc = desc[: bm.start()].strip().rstrip(" .;`'—–-")
        out.append(Record(
            code=current_code, info=info, desc=desc, page=page,
            source="index", confidence="confident", flags=flags,
            raw=line.strip(), book_page=book_page, title=desc,
        ))
    return out, current_code


# --------------------------------------------------------------------------
# Объединение
# --------------------------------------------------------------------------

def match_index(app: Record, index: list[Record]) -> Record | None:
    """Найти запись указателя для записи приложения.

    Приоритет: точная пара (код, слово) > совпадение заголовка >
    близкое число.  Заголовок надёжнее числа, когда OCR исказил
    цифру («465» вместо «165»).
    """
    ca, ia = app.canonical()
    cands = [r for r in index if r.code == app.code]

    # 1) точное совпадение (код, слово)
    for r in cands:
        if r.canonical() == (ca, ia):
            return r

    # 1a) типичная подстановка ведущей цифры при OCR: 4->1, 6/9->0
    variants = []
    if ia.startswith("4"):
        variants.append("1" + ia[1:])
    if ia.startswith(("6", "9")):
        variants.append("0" + ia[1:])
    for v in variants:
        for r in cands:
            if info_key(r.info) == v:
                return r

    # 2) совпадение по заголовку (при OCR-искажении числа)
    k = desc_key(app.title)
    if len(k) >= 10:
        for r in cands:
            rk = desc_key(r.desc)
            if len(rk) >= 10 and (rk == k or k.startswith(rk) or rk.startswith(k)):
                return r
    return None


def clean_appendix_desc(app: Record) -> str | None:
    """Отобрать описание из приложения, отбраковав явно испорченное."""
    t = app.title.strip()
    if len(t) < 8 or " " not in t or re.match(r"^[\d\W]", t) or re.search(
        r"\bИР\b|\bАИСП\b|rye|rae|tae", t, re.I
    ):
        return None
    body = app.detail.strip()
    if body and re.search(r"\bИР\b|\bАИСП\b|rye|rae", body, re.I):
        body = ""
    if body and len(body) < 25:
        body = ""
    if body:
        return norm_ws(t + " — " + body[:420])
    return t


def merge_records(appendix: list[Record], index: list[Record]) -> list[Record]:
    merged: dict[tuple[str, str], Record] = {}
    corrections: list[str] = []

    # Указатель -- авторитетный источник: создаём базовые записи.
    for r in index:
        merged[r.canonical()] = Record(
            code=r.code, info=r.info, desc=r.desc,
            page=(r.book_page + 1) if r.book_page else r.page,
            source="index", confidence="confident", flags=list(r.flags),
            raw=r.raw, book_page=r.book_page,
        )

    for app in appendix:
        if not app.info:
            continue
        idx = match_index(app, index)
        if idx is not None:
            key = idx.canonical()
            base = merged[key]
            # Описание: заголовок приложения + 2-5 строк, если оно
            # читаемое; иначе оставляем краткое описание указателя.
            ad = clean_appendix_desc(app)
            base.detail = ad or ""
            if ad and (not base.desc or len(ad) > len(base.desc)):
                base.desc = ad
                base.page = app.page
            if app.flags:
                base.flags = sorted(set(base.flags + app.flags))
                if app.canonical() != idx.canonical():
                    base.corrected_info = f"{app.info} -> {idx.info}"
                    corrections.append(
                        f"Э{app.code}:{app.info} (стр.{app.page}) -> "
                        f"Э{idx.code}:{idx.info} по указателю"
                    )
            continue
        # Нет соответствия в указателе -- отдельная запись.
        key = app.canonical()
        if key in merged:
            old = merged[key]
            ad = clean_appendix_desc(app)
            if ad and len(ad) > len(old.detail):
                old.desc, old.detail, old.page = ad, ad, app.page
            old.flags = sorted(set(old.flags + app.flags))
            if app.flags:
                old.confidence = "low"
        else:
            app.detail = clean_appendix_desc(app) or ""
            if app.detail:
                app.desc = app.detail
            merged[key] = app

    uncertain = {"subscript-tail", "subscript-3or5", "aip-ocr", "ir-ocr",
                 "junk", "no-numeric-info"}
    for r in merged.values():
        if r.flags and any(f.split(":")[0] in uncertain for f in r.flags):
            r.confidence = "low"
        else:
            r.confidence = "confident"

    return sorted(merged.values(), key=lambda r: (r.code, int(r.info, 8))), corrections


# --------------------------------------------------------------------------
# Сравнение с rukava.be
# --------------------------------------------------------------------------

def load_rukava_pairs() -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    if not RUKAVA.exists():
        return pairs
    rx = re.compile(r"^\*\|\s*Э([0-7]{2,3})\s+([0-7]{1,6})", re.M)
    for m in rx.finditer(RUKAVA.read_text(encoding="utf-8", errors="replace")):
        try:
            code = format(int(m.group(1), 8), "o")
            info = format(int(m.group(2), 8), "o")
        except ValueError:
            continue
        pairs.add((code, info))
    return pairs


# --------------------------------------------------------------------------
# Вывод
# --------------------------------------------------------------------------

def write_outputs(records: list[Record], appendix: list[Record], index: list[Record],
                  corrections: list[str], stats: dict, log_lines: list[str]) -> None:
    # --- JSON ---
    js = {}
    for r in records:
        entry = {"desc": r.desc, "page": r.page, "confidence": r.confidence}
        if r.flags:
            entry["flags"] = r.flags
        if r.corrected_info:
            entry["corrected_info"] = r.corrected_info
        js[make_key(r.code, r.info)] = entry
    JSON_PATH.write_text(
        json.dumps(js, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # --- Markdown ---
    low = [r for r in records if r.confidence == "low"]
    corrupted = [r for r in appendix if r.flags or not r.info]
    md: list[str] = []
    md.append("# Экстракоды ОС ДИСПАК — полная таблица (Тюрин, 1985)\n")
    md.append(
        "Источник: распознанная книга В. Ф. Тюрин, «Операционная система ДИСПАК» "
        "(1985), приложение П «ЭКСТРАКОДЫ OC ДИСПАК ДЛЯ ПОЛЬЗОВАТЕЛЕЙ» "
        "(PDF-страницы 264–291) и авторский «СПИСОК ЭКСТРАКОДОВ» "
        "(PDF-страницы 331–335).\n"
    )
    md.append(
        f"Всего записей: **{len(records)}** "
        f"(confident: {len(records) - len(low)}, low: {len(low)}). "
        f"Записей приложения: {stats['appendix_total']}, "
        f"записей указателя: {len(index)}.\n"
    )
    md.append(
        "Код `Эnnn` — восьмеричный (`ИР 050` = Э50). "
        "Информационное слово — восьмеричное (`0114` = `114₈`). "
        "Ключ JSON: `Эnnn:mmmm`.\n"
    )
    md.append("## Таблица\n")
    md.append("| Код | Информационное слово (8) | Описание | Стр. PDF | Confidence |")
    md.append("|---|---|---|---|---|")
    for r in records:
        d = r.desc.replace("|", "\\|").replace("\n", " ")
        if len(d) > 320:
            d = d[:320].rsplit(" ", 1)[0] + " …"
        star = " ⚠" if r.flags else ""
        md.append(
            f"| `{code_to_idx(r.code)}` | `{r.info}` | {d}{star} | {r.page} | "
            f"{r.confidence} |"
        )

    md.append("\n## Записи с явно испорченным OCR\n")
    md.append(
        "Ниже приведены исходные фрагменты, где распознавание исказило код, "
        "информационное слово или описание. Большинство из них приведено к "
        "чистому виду по авторскому указателю; помеченные `low` остаются "
        "предположительными.\n"
    )
    md.append("| Стр. PDF | Исходный фрагмент | Нормализация | Флаги |")
    md.append("|---|---|---|---|")
    for r in corrupted:
        raw = r.raw.replace("|", "\\|").replace("\n", " ")
        if len(raw) > 200:
            raw = raw[:200].rsplit(" ", 1)[0] + " …"
        norm = (f"`Э{r.code}:{r.info}`" if r.info else "— (нет числа)")
        if r.corrected_info:
            norm += f" → `{r.corrected_info}`"
        md.append(
            f"| {r.page} | `{raw}` | {norm} | {', '.join(r.flags) or 'ocr'} |"
        )

    if corrections:
        md.append("\n## Исправления по указателю\n")
        for c in corrections:
            md.append(f"- {c}")

    # Покрытие rukava.be
    rp = load_rukava_pairs()
    ours = {r.canonical() for r in records}
    hit = ours & rp
    md.append("\n## Покрытие пар из `rukava.be`\n")
    md.append(
        f"В `rukava.be` найдено {len(rp)} пар «Экод слово». "
        f"Покрыто таблицей: **{len(hit)} из {len(rp)}** "
        f"({100 * len(hit) / max(1, len(rp)):.1f}%).\n"
    )
    missing = sorted(rp - ours)
    if missing:
        md.append("Не покрытые пары (из более поздней версии ОС):\n")
        md.append("| Код (8) | Слово (8) |")
        md.append("|---|---|")
        for c, i in missing:
            md.append(f"| `Э{c}` | `{i}` |")

    MD_PATH.write_text("\n".join(md) + "\n", encoding="utf-8")

    # --- README ---
    readme = f"""# Распознанные экстракоды Тюрина (1985)

## Файлы

| Файл | Содержание |
|---|---|
| `parse_extract_codes.py` | парсер OCR-страниц; создаёт всё остальное |
| `extract-codes.md` | полная таблица экстракодов + испорченные OCR-записи |
| `extract-codes.json` | машиночитаемый вид `{{"Э050:0114": {{"desc": …, "page": …}}}}` |
| `ocr/page-0001.txt` … `page-0338.txt` | исходный OCR (338 страниц) |
| `../tyurin1985-full.txt` | сводный OCR-текст |
| `../../logs/tyurin_extract_parse.txt` | лог запуска |

## Метод

1. **Приложение П** (PDF-страницы 264–291). Каждая строка сканируется и ищется регулярным выражением `ИР NNN … АИСП … MMM`.  
   `NNN` и `MMM` нормализуются как **восьмеричные** числа.  
   Описание берётся из заголовка до `ИР` и 2–5 следующих строк до
   следующей записи. Сохраняется номер PDF-страницы.
2. **Авторский указатель** (PDF-страницы 331–335, «СПИСОК
   ЭКСТРАКОДОВ») даёт чистые 4-разрядные восьмеричные слова и
   короткие описания. Он используется как авторитетный источник
   для исправления OCR-ошибок и для записей, которые в приложении
   распознаны плохо. Номер печатной страницы указателя +1 даёт
   номер PDF-страницы с подробным описанием.
3. **Объединение** по канонической паре `(код, слово)`. Записи,
   совпадающие с указателем, получают confidence `confident`;
   записи, где число восстановлено с помощью эвристики или осталось формулой —
   `low` и перечисляются отдельно.

## Учтённые OCR-ошибки

- `ИР` → `MP`, `НР`, `ПР`, `nP`, `uP`, `UP`, `IR`, `1P`, `ЭР`, `HP`;
- `АИСП` → `АИСИП`, `АЙСП`, `АИСИ`, `АНСП`, `AHCI`, `AMICI`, `АИСП.`;
- `=` → `==`, `. =`; `где` → `rye`, `rae`, `tae`, `те`;
- восьмеричный индекс `8` → `s`, `3`, `5`, `g`, `,`, `;`, `»`, `в`, `%`;
- `A`/`4`, `0`/`O`, `I`/`1`, пропущенные пробелы.

## Исходные файлы

- `/home/azizz/Рабочий стол/БЭСМ-6/Тюрин-1985_-ОС-Диспак_compressed.pdf`
  (338 страниц, сканированный образ, текстового слоя нет).
- OCR выполнен субагентами A/B/C/D (`ocr/README-*.txt`):
  `pdftoppm -r 200 -gray -png` + `tesseract -l rus+eng --psm 3`.
- Сравнение: `../../rukava.be` (таблица системных вызовов).

## Итог

- Записей в таблице: **{len(records)}** (low: **{len(low)}**).
- Покрытие пар `rukava.be`: **{len(hit)}/{len(rp)}**.
"""
    README_PATH.write_text(readme, encoding="utf-8")


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main() -> int:
    pages = sorted(
        OCR_DIR.glob("page-*.txt"),
        key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)),
    )
    if not pages:
        print(f"Нет OCR-страниц в {OCR_DIR}", file=sys.stderr)
        return 1

    log: list[str] = []
    log.append("Лог парсинга экстракодов Тюрин-1985")
    log.append("=" * 70)
    log.append(f"Вход: {OCR_DIR} ({len(pages)} файлов)")
    log.append(f"Библиотека пар для сравнения: {RUKAVA}")
    log.append("")

    appendix: list[Record] = []
    index: list[Record] = []
    per_page: list[str] = []
    index_code: str | None = None

    for p in pages:
        page_no = int(re.search(r"(\d+)", p.stem).group(1))
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        if 330 <= page_no <= 336:
            idx, index_code = parse_index_page(page_no, lines, index_code)
            index.extend(idx)
        else:
            a = parse_appendix_page(page_no, lines)
            appendix.extend(a)
            if a:
                per_page.append(f"  стр.{page_no:4d}: {len(a)} записей")

    # Удалить дубли записей приложения (один и тот же фрагмент,
    # найденный на двух соседних строках).
    seen: set[tuple[int, str]] = set()
    uniq: list[Record] = []
    for r in appendix:
        k = (r.page, r.raw)
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    appendix = uniq

    records, corrections = merge_records(appendix, index)
    low = [r for r in records if r.confidence == "low"]
    corrupted = [r for r in appendix if r.flags or not r.info]

    log.append("Распознанные записи приложения по страницам:")
    log.extend(per_page)
    log.append("")
    log.append(f"Всего записей приложения: {len(appendix)}")
    log.append(f"Всего записей авторского указателя: {len(index)}")
    log.append(f"Итоговых уникальных записей: {len(records)}")
    log.append(f"  confident: {len(records) - len(low)}")
    log.append(f"  low:       {len(low)}")
    log.append(f"Записей с явно испорченным OCR: {len(corrupted)}")
    log.append("")
    if corrections:
        log.append("Исправления по указателю:")
        log.extend("  " + c for c in corrections)
        log.append("")

    rp = load_rukava_pairs()
    ours = {r.canonical() for r in records}
    hit = ours & rp
    log.append("Покрытие rukava.be:")
    log.append(f"  пар в rukava.be: {len(rp)}")
    log.append(f"  покрыто: {len(hit)} ({100 * len(hit) / max(1, len(rp)):.1f}%)")
    log.append(f"  не покрыто: {len(rp - ours)}")
    log.append("")
    log.append("Не покрытые пары:")
    for c, i in sorted(rp - ours):
        log.append(f"  Э{c}:{i}")
    log.append("")
    log.append("Низкая уверенность (low):")
    for r in low:
        log.append(f"  стр.{r.page:4d}  Э{r.code}:{r.info or '?'}  {r.desc[:70]}")
        log.append(f"      raw: {r.raw[:120]}")
        log.append(f"      flags: {', '.join(r.flags)}")

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("\n".join(log) + "\n", encoding="utf-8")

    write_outputs(
        records, appendix, index, corrections,
        {"appendix_total": len(appendix)}, log,
    )

    print(f"Записей: {len(records)} (low={len(low)})")
    print(f"Испорченный OCR: {len(corrupted)}")
    print(f"Покрытие rukava.be: {len(hit)}/{len(rp)}")
    print(f"Файлы: {MD_PATH.name}, {JSON_PATH.name}, {README_PATH.name}")
    print(f"Лог: {LOG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
