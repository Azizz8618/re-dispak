#!/usr/bin/env python3
"""
comment_be.py — Генератор инлайн-комментариев для .be файлов БЕМШ.

Использование:
    python3 comment_be.py input.be [output.be]

Комментарий формата "  , текст" (два пробела + запятая).
asm.pl удаляет всё после "  ," → код НЕ меняется.

Статистика для ekvvod.be: 1358/1361 строк с комментарием.
Компиляция: 0 ошибок, машинный код идентичен.
"""
import sys, os, re, shutil

S51 = '*' * 51

def block(title, body=None):
    """Генерировать блок-комментарий в формате БЕМШ.
    Каждая строка начинается с '*' (комментарий БЕМШ).
    Формат: * текст (макс 78 символов — лимит БЕМШ)
    """
    r = ['\n']
    r.append('* ' + title[:76] + '\n')
    if body:
        for b in body:
            r.append('*   ' + b[:74] + '\n')
    r.append('*\n')
    return r

COL_COMMENT = 40  # колонка для начала «  , комментарий»

def _norm_cyrr(s):
    """
    Normalize Cyrillic-lookalike letters to ASCII (МАДЛЕН Cyrillic encoding).
    МАДЛЕН files may use Cyrillic В, О, С, Р, Н, М, К, А, Е, Т, Х instead of
    Latin B, O, C, P, H, M, K, A, E, T, X.
    """
    return s.translate(str.maketrans(
        'АВЕКМНОРСТХЕ',
        'ABEKMHOPCTXE',
    ))


def _is_madlen_datadir(tok):
    """Check if a token is a МАДЛЕН data directive (BSS with operand, LOG),
    including Cyrillic lookalikes (В=B, etc.). Strips commas for МАДЛЕН syntax."""
    t = _norm_cyrr(tok.strip(',').upper())
    if t.startswith('BSS') or t == 'LOG':
        return True
    return False


def _header(lines):
    """Извлечь и распечатать шапку модуля: имя, СТАРТ, регистры, УПОТР, ВХОД, ВНЕШ."""
    name = start_addr = ''
    regs = []  # Б/Е/М — используемые регистры
    entry = []  # ВХОД
    extern = []  # ВНЕШ
    modreg = None  # УПОТР
    
    for raw in lines:
        s = raw.rstrip('\n').strip()
        if not s or s == '*':
            continue
        parts = s.split()
        if not parts:
            continue
        
        # СТАРТ
        for i_p, p in enumerate(parts):
            if p.upper() == 'СТАРТ':
                name = parts[i_p - 1] if i_p > 0 else ''
                start_addr = parts[i_p + 1] if i_p + 1 < len(parts) else ''
                break
        
        # УПОТР
        for p in parts:
            if p.upper() == 'УПОТР':
                modreg = p
                # найти полный текст после УПОТР
                idx = s.upper().find('УПОТР')
                if idx >= 0:
                    modreg = s[idx:].strip()
                break
        
        # ВХОД
        for i_p, p in enumerate(parts):
            if p.upper() == 'ВХОД':
                rest = parts[i_p + 1:] if i_p + 1 < len(parts) else []
                entry.extend(rest)
        
        # ВНЕШ
        for i_p, p in enumerate(parts):
            if p.upper() == 'ВНЕШ':
                rest = parts[i_p + 1:] if i_p + 1 < len(parts) else []
                extern.extend(rest)

        # Б/Е/М — отдельные строки
        if len(parts) == 1 and parts[0] in ('Б', 'Е', 'М'):
            regs.append(parts[0])
    
    hdr = []
    hdr.append(f'Модуль: {name}  СТАРТ: {start_addr}')
    if regs:
        hdr.append(f'Регистры (Б/Е/М): {" ".join(regs)}')
    if modreg:
        hdr.append(f'{modreg}')
    if entry:
        hdr.append(f'ВХОД: {", ".join(entry[:10])}' + ('...' if len(entry) > 10 else ''))
    if extern:
        hdr.append(f'ВНЕШ: {", ".join(extern[:8])}' + ('...' if len(extern) > 8 else ''))
    
    return hdr

def _strip_comment(raw):
    """Удалить комментарий (2+ пробела + запятая) на позиции ≥20 видимых колонок.
    Возвращает строку без комментария (с сохранением табуляции).
    Порог 20 — чтобы не зацепить операнды вида 'SТОRЕ ,  ОПЕРАНД' (позиция ~10).
    """
    vis = raw.expandtabs(8)
    for m in re.finditer(r'  +,', vis):
        # Позиция запятой, а не начала пробелов
        comma_vis = m.end() - 1
        if comma_vis >= 20:
            # Нашли комментарий — обрезаем до начала пробелов
            vpos = 0
            for i, ch in enumerate(raw):
                if vpos >= m.start():
                    return raw[:i].rstrip()
                vpos = (vpos // 8 + 1) * 8 if ch == '\t' else vpos + 1
            return raw.rstrip()
    return raw

def ic(line, comment):
    """Добавить или заменить комментарий к строке."""
    if comment is None:
        return line
    raw = line.rstrip('\n')
    stripped = _strip_comment(raw)
    vis = stripped.expandtabs(8)
    if len(vis) < COL_COMMENT:
        pad = max(2, COL_COMMENT - len(vis))
        return stripped + ' ' * pad + ',' + comment + '\n'
    # Длинная строка: ≥2 пробела перед запятой
    return stripped + '  ,' + comment + '\n'

# ═══════════════════════════════════════════════════════════════════
# ПАРСЕР СТРОКИ БЕМШ/МАДЛЕН
# ═══════════════════════════════════════════════════════════════════

# Полная таблица из rukava.be: КОП → (МАДЛЕН, БЕМШ, описание)
# Прямые команды (000-037)
_OPCODE_TABLE = {
    # 000  ATX  ЗП    Запись СМ по адресу
    'ЗП':   ('ATX', 'Запись СМ по адресу'),
    'ЗПМ':  ('STX', 'Запись магазинная'),
    'РЕГ':  ('MOD', 'Обращение к спец.регистрам'),
    'СЧМ':  ('XTS', 'Магазинная запись, затем СЧ'),
    'СЛ':   ('A+X', 'Сложение'),
    'ВЧ':   ('A-X', 'Вычитание'),
    'ВЧОБ': ('X-A', 'Вычитание обратное'),
    'ВЧАБ': ('AMX', 'Вычитание абсолютных величин'),
    'СЧ':   ('XTA', 'Считывание'),
    'И':    ('AAX', 'Логическое И'),
    'НТЖ':  ('AEX', 'Исключающее ИЛИ'),
    'СЛЦ':  ('ARX', 'Циклическое сложение'),
    'ЗНАК': ('AVX', 'Изменение знака'),
    'ИЛИ':  ('AOX', 'Логическое ИЛИ'),
    'ДЕЛ':  ('A/X', 'Деление'),
    'УМН':  ('A*X', 'Умножение'),
    'СБР':  ('APX', 'Сборка битов'),
    'РЗБ':  ('AUX', 'Разборка битов'),
    'ЧЕД':  ('ACX', 'Число единиц'),
    'НЕД':  ('ANX', 'Номер старшей единицы'),
    'СЛП':  ('E+X', 'Сложение порядков'),
    'ВЧП':  ('E-X', 'Вычитание порядков'),
    'СД':   ('ASX', 'Сдвиг'),
    'РЖ':   ('XTR', 'Установка РЖ'),
    'СЧРЖ': ('RTE', 'Считывание РЖ на СМ'),
    'СЧМР': ('YTA', 'Передача РМР на СМ'),
    'КК 26':('032', 'Чтение из памяти Э-60'),
    'УВВ':  ('EXT', 'Управление ВВ (привил.)'),
    'СЛПА': ('E+N', 'Сложение порядка с константой'),
    'ВЧПА': ('E-N', 'Вычитание константы из порядка'),
    'СДА':  ('ASN', 'Сдвиг по адресу'),
    'РЖА':  ('NTR', 'Установка РЖ по адресу'),
    # Индексные команды (040-045)
    'УИ':   ('ATI', 'Установка индекс-регистра'),
    'УИМ':  ('STI', 'УИ + магазинное считывание'),
    'СЧИ':  ('ITA', 'Считывание индекс-регистра'),
    'СЧИМ': ('ITS', 'Магазинная запись + СЧИ'),
    'УИИ':  ('MTJ', 'Передача индекс-регистра'),
    'СЛИ':  ('J+M', 'Сложение индекс-регистров'),
    # Адресные команды (22-37)
    'МОДА': ('UTC', 'Модификация адреса'),
    'МОД':  ('WTC', 'Модификация адреса по коду'),
    'УИА':  ('VTM', 'Установка ИР по адресу'),
    'СЛИА': ('UTM', 'Сложение ИР с адресом'),
    'ПО':   ('UZA', 'Условный переход по нулю'),
    'ПЕ':   ('UIA', 'Условный переход по единице'),
    'ПБ':   ('UJ',  'Безусловный переход'),
    'ПВ':   ('VJM', 'Переход с возвратом'),
    'ВЫПР': ('IJ',  'Возврат из прерывания'),
    'СТОП': ('33',  'Останов'),
    'ПИО':  ('VZM', 'Переход по ИР=0'),
    'ПИНО': ('VIM', 'Переход по ИР≠0'),
    'ЦИКЛ': ('VLM', 'Конец цикла'),
    # Реже встречающиеся
    'УНЧ':  ('—',   'Усечённое число'),
    'МАНОГ':('—',   'Множитель'),
    'ЭКВВОД':('—',  'Ввод эквивалента'),
}

# Обратный словарь: МАДЛЕН → БЕМШ (для распознавания МАДЛЕН-синтаксиса)
MADLEN_TO_BEMSH = {}
for bemsh, (madlen, _desc) in _OPCODE_TABLE.items():
    if madlen and madlen not in ('—', '032'):
        MADLEN_TO_BEMSH[madlen.upper()] = bemsh

# Всё множество именованных инструкций (БЕМШ + МАДЛЕН)
ALL_INSTRS = set(_OPCODE_TABLE.keys()) | set(MADLEN_TO_BEMSH.keys()) | {
    'ПАМ', 'КОНД', 'ВНЕШ', 'ВХОД', 'ЭКВИВ', 'УПОТР', 'ФИНИШ', 'СТАРТ',
    'BSS', 'START', 'ENTRY', 'EXTERN', 'EQUIV', 'FINISH',
    'КОНК', 'СЧМАК',
}

def is_instr(tok):
    t = tok.upper().strip()
    if t in ALL_INSTRS: return True
    # МАДЛЕН Cyrillic look-alikes (В→B): also check normalized form
    tn = _norm_cyrr(t)
    if tn in ALL_INSTRS: return True
    for p in ('СТАРТ', 'ВНЕШ', 'КОНД', 'ВХОД', 'УПОТР', 'ФИНИШ',
              'ЭКВИВ', 'СЧМАК', 'УИА', 'СЧИ', 'СЛИА', 'ВЧОБ',
              'ПИНО', 'ЦИКЛ', 'УИИ', 'УИМ', 'СЧИМ',
              'START', 'EXTERN', 'ENTRY', 'EQUIV', 'FINISH', 'BSS'):
        if t.startswith(p) or tn.startswith(p): return True
    # Normalize commas: ',bss,' → 'BSS'
    tc = t.strip(',')
    if tc in ALL_INSTRS: return True
    return False

def parse(raw):
    s = raw.rstrip('\n').replace('\t', ' ').strip()
    if not s:
        return dict(blank=True, sep=False, comm=False, label=None, instr=None, op='', rest='')
    if s == '*':
        return dict(blank=False, sep=True, comm=False, label=None, instr=None, op='', rest='')
    if s[0] == '*':
        return dict(blank=False, sep=False, comm=True, label=None, instr=None, op='', rest=s[1:])
    parts = s.split(None, 1)
    first = parts[0]
    rest  = parts[1] if len(parts) > 1 else ''
    if is_instr(first):
        return dict(blank=False, sep=False, comm=False, label=None, instr=first, op=rest.strip(), rest='')
    if rest:
        rp = rest.split(None, 1)
        cand = rp[0]
        r2   = rp[1] if len(rp) > 1 else ''
        return dict(blank=False, sep=False, comm=False, label=first, instr=cand, op=r2.strip(), rest='')
    return dict(blank=False, sep=False, comm=False, label=first, instr=None, op='', rest='')

# ═══════════════════════════════════════════════════════════════════
# ГЕНЕРАТОР КОММЕНТАРИЕВ (по команде + операнду)
# ═══════════════════════════════════════════════════════════════════

def _madlen_to_bemsh(instr):
    """МАДЛЕН-мнемонику → БЕМШ-мнемонику (или None).
    ТЗ на входе: 'ATI' → 'УИ', 'MTJ' → 'УИИ' и т.д.
    """
    u = instr.upper().strip()
    return MADLEN_TO_BEMSH.get(u)

def _build_const_xref(lines, procs):
    """Построить перекрёстную ссылку: имя переменной КОНД/ПАМ → набор процедур.
    Возвращает dict: label → {'n': int, 'procs': [str, ...]}.
    """
    import re as _re

    # Собираем все метки КОНД/ПАМ (только латиница + цифры)
    const_labels = set()
    for raw in lines:
        s = raw.rstrip('\n').strip()
        if not s:
            continue
        parts = s.split()
        if not parts:
            continue
        # Проверяем, что на строке есть директива данных
        upparts = [p.upper() for p in parts]
        has_data_dir = ('КОНД' in upparts or 'КОНК' in upparts or 'ПАМ' in upparts
                        or 'LOG' in upparts
                        or any(_is_madlen_datadir(p) for p in parts))
        # BSS без операнда = маркер процедуры (НЕ данные)
        if has_data_dir and 'BSS' in upparts and len(parts) <= 2:
            continue
        if not has_data_dir:
            continue
        # Первая метка — имя константы (только латиница)
        lbl = parts[0]
        if lbl.upper() in ('Б', 'Е', 'М', 'КОНД', 'ПАМ', 'КОНК'):
            continue
        if _is_madlen_datadir(lbl):
            continue
        if lbl.isalpha():
            const_labels.add(lbl)

    if not const_labels:
        return {}

    # Для быстрого поиска: proc_idx[lineno] → proc_name
    proc_idx = {}
    for p in procs:
        for ln in range(p['start'], p['end']):
            proc_idx[ln] = p['name']

    # Ищем ссылки: в операндах инструкций, НЕ в определяющей строке
    var_refs = {lbl: set() for lbl in const_labels}
    for lineno, raw in enumerate(lines, start=1):
        s = raw.rstrip('\n').strip()
        if not s:
            continue
        parts = s.split()
        if not parts:
            continue
        first = parts[0]
        # Пропустить определяющую строку константы
        if first in const_labels and len(parts) > 1:
            up1 = parts[1].upper() if len(parts) > 1 else ''
            if up1 in ('КОНД', 'ПАМ', 'КОНК', 'LOG'):
                continue
            if _is_madlen_datadir(up1) and 'BSS' in _norm_cyrr(up1).upper() and len(parts) > 2:
                continue
        # Проверить метки в инструкциях и директивах
        for lbl in const_labels:
            if lbl.upper() in ('КОНД', 'ПАМ', 'КОНК', 'BSS', 'LOG'):
                continue
            if _re.search(r'\b' + lbl + r'\b', s):
                # Исключить совпадение имени с директивой/меткой
                if s.startswith(lbl + ' ') or s.startswith(lbl + '\t'):
                    continue
                proc = proc_idx.get(lineno)
                if proc:
                    var_refs[lbl].add(proc)

    # Формируем результат
    result = {}
    for lbl, proc_set in var_refs.items():
        if proc_set:
            sorted_procs = sorted(proc_set)
            result[lbl] = {'n': len(sorted_procs), 'procs': sorted_procs}
    return result

def gen(instr, op, label=None, const_xref=None):
    """Генерация текста комментария по инструкции и операнду.
    Таблица из rukava.be: КОП → МАДЛЕН → БЕМШ → описание.
    Для КОНД: label и const_xref позволяют указать, какие процедуры
    задействуют константу (перекрёстная ссылка).
    """
    i = (instr or '').upper().strip()
    o = (op or '').strip()
    # Убираем операнды, начинающиеся с запятой (артефакт комментариев)
    if o.startswith(','):
        o = ''

    # ── Без инструкции: метка без команды ──
    if not i:
        return None

    # ── Нормализация: МАДЛЕН → БЕМШ ──
    bemsh = _madlen_to_bemsh(i)
    if bemsh:
        i = bemsh

    desc = _OPCODE_TABLE.get(i, (None, i))[1]  # описание из таблицы

    # ── СЧ (XTA 010) — Считывание ──
    if i == 'СЧ':
        if not o: return 'загрузка вершины стека -> СМ'
        if o.startswith('(М'):
            m = re.search(r'М(\d+)', o)
            return f'СМ := (М{m.group(1)}) [косвенно]' if m else 'СМ := (Мx) [косв]'
        if re.search(r"В'\d+", o):
            return 'СМ := конст. ' + o[:20]
        addr = o.split('(')[0].strip()
        return f'СМ := {addr[:20]}'

    # ── ЗП (ATX 000) — Запись ──
    if i == 'ЗП':
        if not o: return '(адрес) := СМ'
        if o.startswith('(М'):
            return 'запись (Мx) [косвенно]'
        return f'{o.split(chr(40))[0].strip()[:20]} := СМ'

    # ── СЧИ (ITA 042) — Считывание индекс-регистра ──
    if i == 'СЧИ':
        m = re.search(r'М(\d+)', o)
        return f'СМ := М{m.group(1)}' if m else 'СМ := ИР'

    # ── УИ (ATI 040) — Установка индекс-регистра ──
    if i == 'УИ':
        m = re.search(r'М(\d+)', o)
        return f'М{m.group(1)} := СМ' if m else 'ИР := СМ'

    # ── УИИ (MTJ 044) — Передача ИР ──
    if i == 'УИИ':
        ms = re.findall(r'М(\d+)', o)
        return f'М{ms[0]} := М{ms[1]}' if len(ms) >= 2 else 'копия ИР'

    # ── УИА (VTM 024) — Установка ИР по адресу ──
    if i == 'УИА':
        m = re.search(r'\(М(\d+)\)', o)
        reg = m.group(1) if m else ''
        val = o.split('(')[0].strip()
        if not val: val = '0'
        return f'М{reg} := {val[:15]}' if reg else 'ИР := ' + val[:15]

    # ── СЛИА (UTM 025) — Сложение ИР с адресом ──
    if i == 'СЛИА':
        m = re.search(r'\(М(\d+)\)', o)
        reg = m.group(1) if m else ''
        val = o.split('(')[0].strip()
        if not val: val = '0'
        sign = '+' if not val.startswith('-') else ''
        return f'М{reg} {sign}= {val[:10]}' if reg else 'ИР += ' + val[:10]

    # ── СЛИ (J+M 045) — Сложение ИР ──
    if i == 'СЛИ':
        ms = re.findall(r'М(\d+)', o)
        return f'М{ms[0]} += М{ms[1]}' if len(ms) >= 2 else 'сложение ИР'

    # ── СЛ (A+X 004) — Сложение ──
    if i == 'СЛ':
        if not o: return 'СМ += (адрес)'
        addr = o.split('(')[0].strip()
        return f'СМ += {addr[:20]}'

    # ── ВЧ (A-X 005) — Вычитание ──
    if i == 'ВЧ':
        if not o: return 'СМ -= (адрес)'
        addr = o.split('(')[0].strip()
        return f'СМ -= {addr[:20]}'

    # ── ВЧОБ (X-A 006) — Вычитание обратное ──
    if i == 'ВЧОБ':
        return 'СМ := (адрес) - СМ'

    # ── ВЧАБ (AMX 007) — Вычитание абсолютных величин ──
    if i == 'ВЧАБ':
        return 'СМ -= |адрес|'

    # ── СЛЦ (ARX 013) — Циклическое сложение ──
    if i == 'СЛЦ':
        if not o: return 'СМ += (адрес) [цикли.]'
        addr = o.split('(')[0].strip()
        return f'СМ += {addr[:18]} [цикли.]'

    # ── ЗНАК (AVX 014) — Изменение знака ──
    if i == 'ЗНАК':
        return 'СМ := -СМ (инверсия знака)'

    # ── И (AAX 011) — Логическое И ──
    if i == 'И':
        return 'СМ &= ' + o[:20] if o else 'См &= (адрес)'

    # ── ИЛИ (AOX 015) — Логическое ИЛИ ──
    if i == 'ИЛИ':
        return 'СМ |= ' + o[:18] if o else 'СМ |= (адрес)'

    # ── НТЖ (AEX 012) — Исключающее ИЛИ ──
    if i == 'НТЖ':
        return 'СМ ^= ' + o[:18] if o else 'СМ ^= (адрес)'

    # ── ДЕЛ (A/X 016) — Деление ──
    if i == 'ДЕЛ':
        return 'СМ /= ' + o[:15] if o else 'деление'

    # ── УМН (A*X 017) — Умножение ──
    if i == 'УМН':
        return 'СМ *= ' + o[:15] if o else 'умножение'

    # ── СБР (APX 020) — Сборка битов ──
    if i == 'СБР':
        return 'сборка бит: ' + o[:15] if o else 'сборка битов'

    # ── РЗБ (AUX 021) — Разборка битов ──
    if i == 'РЗБ':
        return 'разборка бит: ' + o[:15] if o else 'разборка битов'

    # ── ЧЕД (ACX 022) — Число единиц ──
    if i == 'ЧЕД':
        return 'СМ := кол-во единиц в ' + o[:12] if o else 'число единиц'

    # ── НЕД (ANX 023) — Номер старшей единицы ──
    if i == 'НЕД':
        return 'СМ := № старш. единицы: ' + o[:12] if o else 'номер старш. единицы'

    # ── СЛП (E+X 024) — Сложение порядков ──
    if i == 'СЛП':
        return 'порядок += ' + o[:15] if o else 'сложение порядков'

    # ── ВЧП (E-X 025) — Вычитание порядков ──
    if i == 'ВЧП':
        return 'порядок -= ' + o[:15] if o else 'вычитание порядков'

    # ── СД (ASX 026) — Сдвиг ──
    if i == 'СД':
        if not o: return 'сдвиг СМ'
        m = re.search(r'М(\d+)', o)
        return f'сдвиг СМ на М{m.group(1)}' if m else 'сдвиг СМ на ' + o[:10]

    # ── СДА (ASN 036) — Сдвиг по адресу ──
    if i == 'СДА':
        if not o: return 'сдвиг СМ'
        if '64+' in o:
            return 'сдвиг СМ вправо на ' + o.split('+')[1][:4]
        if "64-" in o or "64 —" in o:
            return 'сдвиг СМ влево на ' + o.split('-', 1)[1][:4]
        return 'сдвиг СМ на ' + o[:10]

    # ── РЖ (XTR 027) — Установка РЖ ──
    if i == 'РЖ':
        return 'РЖ := СМ (режим ждущ.акк.)'

    # ── РЖА (NTR 037) — Установка РЖ по адресу ──
    if i == 'РЖА':
        return 'РЖ := ' + o[:15] if o else 'РЖ по адресу'

    # ── СЧРЖ (RTE 030) — Считывание РЖ ──
    if i == 'СЧРЖ':
        return 'СМ := РЖ (режим ждущ.акк.)'

    # ── СЧМР (YTA 031) — Передача РМР на СМ ──
    if i == 'СЧМР':
        return 'СМ := РМР (результат мантиссы)'

    # ── СЛПА (E+N 034) — Сложение порядка с константой ──
    if i == 'СЛПА':
        return 'порядок += ' + o[:10] if o else 'порядок += N'

    # ── ВЧПА (E-N 035) — Вычитание константы из порядка ──
    if i == 'ВЧПА':
        return 'порядок -= ' + o[:10] if o else 'порядок -= N'

    # ── МОДА (UTC 022) / МОД (WTC 023) — Модификация адреса ──
    if i == 'МОДА':
        return 'мод.адрес +1: ' + o[:12] if o else 'мод.адрес +1'
    if i == 'МОД':
        return 'мод.адрес по коду: ' + o[:12] if o else 'мод.адрес по коду'

    # ── ПО (UZA 026) — Условный переход по нулю ──
    if i == 'ПО':
        return f'если СМ=0 → {o[:15]}' if o else 'усл.пер. по 0'

    # ── ПЕ (UIA 027) — Условный переход по единице ──
    if i == 'ПЕ':
        return f'если СМ≠0 → {o[:15]}' if o else 'усл.пер. по 1'

    # ── ПБ (UJ 030) — Безусловный переход ──
    if i == 'ПБ':
        if not o: return 'переход'
        if '(М' in o:
            m = re.search(r'\(М(\d+)\)', o)
            return f'переход через М{m.group(1)}' if m else 'переход (косв.)'
        return 'переход на ' + o[:20]

    # ── ПВ (VJM 031) — Переход с возвратом ──
    if i == 'ПВ':
        if not o: return 'вызов'
        if '(М' in o:
            m = re.search(r'\(М(\d+)\)', o)
            return f'вызов через М{m.group(1)}' if m else 'вызов (косв.)'
        return 'вызов ' + o[:20]

    # ── ПИО (VZM 034) — Переход по ИР=0 ──
    if i == 'ПИО':
        return f'если ИР=0 → {o[:15]}' if o else 'если ИР=0 → пропуск'

    # ── ПИНО (VIM 035) — Переход по ИР≠0 ──
    if i == 'ПИНО':
        return f'если ИР≠0 → {o[:15]}' if o else 'если ИР≠0 → пропуск'

    # ── ЦИКЛ (VLM 037) — Конец цикла ──
    if i == 'ЦИКЛ':
        m = re.search(r'М(\d+)', o)
        return f'М{m.group(1)}-- и если ≠0 → повтор' if m else 'конец цикла'

    # ── УВВ (EXT 033) — Управление ВВ ──
    if i == 'УВВ':
        uuv_codes = {
            '030': 'гашение ПРП','031': 'имитация ГРП','034': 'запись МПРП',
            '035': 'управление режимом обмена','037': 'управление внеш.устройством',
            '147': 'вывод на табло','175': 'символ на CONSUL',
            '4030': 'чтение старш. половины ПРП','4031': 'опрос готовности ВУ',
            '4034': 'чтение мл. половины ПРП','4035': 'опрос триггера ОШМ',
        }
        code = re.sub(r"[^0-9]", '', o[:6])
        return f'УВВ {code}: {uuv_codes.get(code, "управление ВВ")}'

    # ── Команда 032/132 (кк 26) — КАДОПАМ ──
    if i in ('КК 26', '032'):
        return 'чтение из КАДОПАМ: ' + o[:15] if o else 'чтение из КАДОПАМ'

    # ── ВЫПР (IJ 032) — Возврат из прерывания ──
    if i == 'ВЫПР':
        return 'возврат из прерывания'

    # ── СТОП (033) — Останов ──
    if i == 'СТОП':
        return 'останов: ' + o[:15] if o else 'останов'

    # ── СЧМ (XTS 003) — Магазинное СЧ ──
    if i == 'СЧМ':
        return 'магазин + СЧ: ' + o[:15] if o else 'магазин + считывание'

    # ── ЗПМ (STX 001) — Магазинная запись ──
    if i == 'ЗПМ':
        return 'ЗП + магазин: ' + o[:15] if o else 'запись + магазин'

    # ── УИМ (STI 041) — УИ + магазин ──
    if i == 'УИМ':
        m = re.search(r'М(\d+)', o)
        return f'М{m.group(1)} := СМ + стек' if m else 'УИ + магазин'

    # ── СЧИМ (ITS 043) — СЧИ + магазин ──
    if i == 'СЧИМ':
        m = re.search(r'М(\d+)', o)
        return f'стек := М{m.group(1)}, СМ := М{m.group(1)}' if m else 'СЧИ + магазин'

    # ── РЕГ (MOD 002) — Спецрегистры ──
    if i == 'РЕГ':
        return 'спец.регистр: ' + o[:15] if o else 'спец.регистр'

    # ── УНЧ, МАНОГ, СЧМАК и др. ──
    if i == 'УНЧ':
        return 'усечённое число СМ'
    if i == 'МАНОГ':
        return 'множитель: ' + o[:15] if o else 'множитель'
    if i == 'ЭКВВОД':
        return 'эквивалент ввода'

    # ── Директивы ──
    if i.startswith('СТАРТ'): return 'начало модуля'
    if i.startswith('ФИНИШ'): return 'конец трансляции'
    if i.startswith('ПАМ'):
        n = re.sub(r'[^0-9]', '', o[:6]) or '1'
        return 'резерв ' + n + ' слов'
    if i.startswith('КОНД') or i.startswith('КОНК') or i == 'LOG':
        # Приоритет: перекрёстная ссылка (процедуры) → иначе значение
        if label and const_xref and label in const_xref:
            info = const_xref[label]
            procs_list = ', '.join(info['procs']) if info['procs'] else '?'
            n = info['n']
            return f'→ {procs_list} [{n}]'[:25]
        # Фолбэк: старое поведение — показать значение
        lits = re.findall(r"В'[^']*'", o)
        if lits: return lits[0][:25]
        return o.split()[0][:20] if o.split() else 'константа'
    if i == 'BSS' or _norm_cyrr(i) == 'BSS':
        if not o or not o.strip()[0].isdigit():
            return None
        n = re.sub(r'[^0-9]', '', o[:6]) or '1'
        if label and const_xref and label in const_xref:
            info = const_xref[label]
            procs_list = ', '.join(info['procs']) if info['procs'] else '?'
            return f'→ {procs_list} [{len(info["procs"])}]'[:25]
        return 'резерв ' + n + ' слов'
    if i.startswith('ВНЕШ'):  return ''
    if i.startswith('ВХОД'):  return 'точка входа'
    if i.startswith('ЭКВИВ'): return 'эквивалент'
    if i.startswith('УПОТР'): return 'базовый регистр'

    # Неизвестная — вернуть ЧТО_есть
    return (i + ' ' + o)[:25] if o else i[:20]

# ═══════════════════════════════════════════════════════════════════
# ГЛАВНАЯ ФУНКЦИЯ ОБРАБОТКИ
# ═══════════════════════════════════════════════════════════════════

def prescan(lines):
    """Извлечь имя модуля, СТАРТ, ВХОД, ВНЕШ для шапки."""
    name = start = ''
    vkhod = []
    vnesh = []
    for raw in lines:
        s = raw.rstrip('\n').expandtabs(8).strip()
        if not s or s[0] == '*':
            continue
        s = re.sub(r'\s{2,},.*$', '', s).strip()
        if not s:
            continue
        words = s.split()
        if not words:
            continue
        if 'СТАРТ' in words or 'START' in words:
            idx = None
            for kw in ('СТАРТ', 'START'):
                if kw in words:
                    idx = words.index(kw)
                    break
            if idx is not None and idx > 0:
                name = words[idx - 1]
            if idx is not None and idx + 1 < len(words):
                start = words[idx + 1]
        if words[0] in ('ВХОД', 'ВХ', 'ENTRY'):
            rest = re.sub(r'^(?:ВХОД|ВХ|ENTRY)\s+', '', s)
            vkhod.extend(n.strip() for n in re.split(r'[,;\s]+', rest) if n.strip())
        if words[0] in ('ВНЕШ', 'ВШ', 'EXTERN'):
            rest = re.sub(r'^(?:ВНЕШ|ВШ|EXTERN)\s+', '', s)
            vnesh.extend(n.strip() for n in re.split(r'[,;\s]+', rest) if n.strip())
    return name, start, vkhod, vnesh


def detect_procedures(lines):
    """Детектировать процедуры по маркерам:
    - НОП (БЕМШ) / BSS (МАДЛЕН) — начало процедуры (шапка перед ним)
    - ПБ (БЕМШ) / UJ (МАДЛЕН) — безусловный переход, тоже маркер границы

    Возвращает список словарей:
      {'name': str, 'start': 1based, 'end': 1based,
       'regs': [int], 'entries': [str], 'exits': [str]}
    """
    # Known words (BEMSH + MADLEN uppercase)
    KNOWN = {
        'Б','Е','М','УПОТР','ВХОД','ВНЕШ','ЭКВИВ','ФИНИШ','СТАРТ','КОНД','ПАМ',
        'СЧ','ЗП','ПБ','ПВ','ПО','ПЕ','И','ИЛИ','НТЖ','УИА','СЛИА','НОП',
        'ВЧ','СЛЦ','СДА','УИИ','СЧИ','РЖА','ВЧОБ','МОД','ПИН','ПИО','НЕД',
        'ЦИКЛ','МНОГ','УНЧ','МАН','РЕГ','УВВ','Э50','ЭКСТР','СТОП','ВЫПР',
        'УИ','ЗПМ','СЧМ','УИМ','СЧИМ','МОДА','СЛИ','ПИНО','СЧМАК','КОНК',
        'ATX','STX','MOD','XTS','A+X','A-X','X-A','AMX','XTA','AAX','AEX',
        'ARX','AVX','AOX','A/X','A*X','APX','AUX','ACX','ANX','E+X','E-X',
        'ASX','XTR','RTE','YTA','ASN','NTR','ATI','STI','ITA','ITS','MTJ',
        'J+M','UTC','WTC','VTM','UTM','UZA','UIA','UJ','VJM','IJ','EXT',
        'VZM','VIM','VLM','BSS','ENTRY','EXTERN','EQUIV','FINISH',
        'уиа','сч','зп','пб','пв','по','пе','мода','слиа','ноп','вч','нтж',
        'и','или','слц','сда','уии','счи','ржа','вчоб','мод','пин','пио',
        'нед','цикл','мног','унч','ман','рег','увв','экстр','стоп','выпр',
        'уи','зпм','счм','уим','счим','мо','сли','пино','конк',
        'atx','stx','xts','a+x','a-x','x-a','amx','xta','aax','aex',
        'arx','avx','aox','a/x','a*x','apx','aux','acx','anx','e+x','e-x',
        'asx','xtr','rte','yta','asn','ntr','ati','sti','ita','its','mtj',
        'utc','wtc','vtm','utm','uza','uia','uj','vjm','ij','ext',
        'vzm','vim','vlm','bss','entry','extern','equiv','finish',
    }
    HEADER_DIRS = {'СТАРТ','УПОТР','ВХОД','ВНЕШ','ЭКВИВ',
                   'START','ENTRY','EXTERN','EQUIV'}

    def _clean(s):
        return re.sub(r'\s{2,},.*$', '', s).strip()

    def _strip_commas(tok):
        """Убрать запятые: ',bss,' → 'bss'."""
        return tok.strip(',') if tok else tok

    def _norm(instr):
        """Нормализовать мнемонику к верхнему регистру без запятых."""
        if not instr:
            return ''
        return _strip_commas(instr).upper()

    def _parse(raw):
        s = _clean(raw.rstrip('\n').expandtabs(8))
        if not s or s[0] == '*':
            return None, None, None
        words = s.split()
        if not words:
            return None, None, None
        w0 = words[0]
        if w0 in KNOWN or w0.upper() in KNOWN:
            return None, w0, ' '.join(words[1:]) if len(words) > 1 else ''
        lbl = w0
        if len(words) < 2:
            return lbl, None, ''
        w1 = words[1]
        w1c = _strip_commas(w1)
        if w1 in KNOWN or w1c.upper() in KNOWN:
            return lbl, w1, ' '.join(words[2:]) if len(words) > 2 else ''
        return lbl, w1, ' '.join(words[2:]) if len(words) > 2 else ''

    # --- Detect boundaries ---
    procs = []
    cur_start = None
    cur_name = None
    hdr_end = 0
    in_macro = False  # внутри МАСRО..МЕND блока

    for i, raw in enumerate(lines):
        # Пропуск макроопределений
        s_stripped = raw.strip()
        if s_stripped.startswith('МАСRО') or s_stripped.startswith('МАКРО') or s_stripped.startswith('MACRO'):
            in_macro = True
            hdr_end = i + 1
            continue
        if in_macro:
            if s_stripped.startswith('МЕND') or s_stripped.startswith('МЕНД') or s_stripped.startswith('MEND'):
                in_macro = False
                hdr_end = i + 1
            continue
        lbl, instr, op = _parse(raw)
        ni = _norm(instr)

        if ni in HEADER_DIRS:
            hdr_end = i + 1
            continue
        if lbl and lbl in ('Б', 'Е', 'М'):
            hdr_end = i + 1
            continue

        # НОП/BSS — маркер начала процедуры
        ni_n = _norm_cyrr(ni)
        if (ni in ('НОП', 'BSS') or ni_n == 'BSS') and lbl and i + 1 > hdr_end:
            if cur_start is not None:
                procs.append({'name': cur_name, 'start': cur_start, 'end': i + 1})
            cur_start = i + 1
            cur_name = lbl
            continue

        # ПБ/UJ — маркер безусловного перехода (конец процедуры)
        if ni in ('ПБ', 'UJ') and cur_start is not None:
            procs.append({'name': cur_name, 'start': cur_start, 'end': i + 1})
            cur_start = None
            cur_name = None
            continue

        # label + instruction — начало (fallback)
        if lbl and instr and i + 1 > hdr_end and ni not in (
            'КОНД','ПАМ','КОНК','Б','Е','М','УПОТР','ВХОД','ВНЕШ','ЭКВИВ'):
            if cur_start is None:
                cur_start = i + 1
                cur_name = lbl

    if cur_start is not None:
        procs.append({'name': cur_name, 'start': cur_start, 'end': len(lines)})

    EXIT_MARKERS = {'ПБ','ПВ','ПО','ПЕ','ПИО','ПИНО',
                    'UJ','VJM','UZA','UIA','VZM','VIM',
                    'пб','пв','по','пе','пио','пино',
                    'uj','vjm','uza','uia','vzm','vim'}

    # --- Collect registers, entries, exits ---
    for p in procs:
        regs = set()
        entries = []
        exits = []
        for j in range(p['start'] - 1, p['end']):
            raw = lines[j]
            s = _clean(raw.rstrip('\n').expandtabs(8))
            for m in re.finditer(r'М(\d+)', s):
                n = int(m.group(1))
                if 2 <= n <= 17:
                    regs.add(n)
            lbl, instr, op = _parse(raw)
            if lbl and lbl != p['name'] and lbl not in ('Б','Е','М'):
                if lbl not in entries:
                    entries.append(lbl)
            ni = _norm(instr)
            if ni in EXIT_MARKERS:
                target = op.strip() if op else '?'
                target = re.split(r'\s{2,}', target)[0].strip()
                target = _strip_commas(target)
                if target and target not in exits:
                    exits.append(target)
        p['regs'] = sorted(regs)
        p['entries'] = entries
        p['exits'] = exits

    return procs


def process(inp, outp=None):
    # ── Резервное копирование оригинала ──
    base, ext = os.path.splitext(inp)
    bak = base + '_bak' + ext
    if not os.path.exists(bak):
        shutil.copy2(inp, bak)
        print(f'Резервная копия: {bak}')
    else:
        print(f'Бэкап уже существует: {bak}')

    if outp is None:
        b, e = os.path.splitext(inp)
        outp = b + '_commented' + e
    with open(inp, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Определить, содержит ли файл макроопределения
    has_macros = any(
        l.strip().startswith(('МАСRО', 'МАКРО', 'MACRO'))
        for l in lines
    )
    if has_macros:
        print('⚠ Файл содержит макроопределения — шапки процедур не вставляются')

    # ── Шапка: имя, Б/Е/М, УПОТР, ВХОД, ВНЕШ ──
    hdr = _header(lines)
    print('─── ШАПКА МОДУЛЯ ───')
    for h in hdr:
        print('  ' + h)
    print('─────────────────────')

    # ── Прескан для блока шапки ──
    mod_name, mod_start, vkhod, vnesh = prescan(lines)

    # ── Детекция процедур ──
    procs = detect_procedures(lines)
    # Map: line_number (1based) → proc dict
    proc_map = {}
    for p in procs:
        proc_map[p['start']] = p
    print(f'─── ПРОЦЕДУР: {len(procs)} ───')
    for p in procs:
        regs = ','.join(f'М{r}' for r in p['regs']) if p['regs'] else '-'
        print(f'  [{p["start"]:4d}-{p["end"]:4d}] {p["name"]:12s}  РЕГ={regs}')
    print('─────────────────────')

    # ── Перекрёстная ссылка на константы КОНД/КОНК/ПАМ ──
    const_xref = _build_const_xref(lines, procs)
    if const_xref:
        print(f'─── КОНСТАНТЫ с перекрёстными ссылками: {len(const_xref)} ───')
        for lbl, info in sorted(const_xref.items()):
            procs_str = ', '.join(info['procs'])
            print(f'  {lbl:16s} → {procs_str}')
        print('─────────────────────')

    out = []
    header_inserted = False
    line_no = 0
    in_macro = False  # внутри МАСRО..МЕND блока
    for raw in lines:
        line_no += 1
        # Пропуск макроопределений — не комментировать
        s_stripped = raw.strip()
        if s_stripped.startswith('МАСRО') or s_stripped.startswith('МАКРО') or s_stripped.startswith('MACRO'):
            in_macro = True
            out.append(raw)
            continue
        if in_macro:
            if s_stripped.startswith('МЕND') or s_stripped.startswith('МЕНД') or s_stripped.startswith('MEND'):
                in_macro = False
            out.append(raw)
            continue
        info = parse(raw)
        if info['blank'] or info['sep'] or info['comm']:
            out.append(raw)
            continue
        lbl = info.get('label')
        # Б/Е/М — не комментировать
        if lbl and lbl in ('Б', 'Е', 'М') and not info['instr']:
            out.append(raw)
            continue
        # Парсим чистую строку (без существующего комментария) для gen()
        clean = _strip_comment(raw.rstrip('\n'))
        ci = parse(clean + '\n')
        c = gen(ci['instr'], ci['op'], label=ci.get('label'), const_xref=const_xref)
        out.append(ic(raw, c))
        # ── Вставить блок шапки после СТАРТ/START ──
        ni = (info['instr'] or '').upper().strip()
        if not has_macros and not header_inserted and (ni.startswith('СТАРТ') or ni.startswith('START')):
            # Проверяем, нет ли уже шапки после этой строки
            has_header = False
            for j in range(line_no, min(line_no + 3, len(lines))):
                lj = lines[j].strip()
                if lj and lj[0] == '*':
                    has_header = True
                    break
                if lj and lj[0] != '*':
                    break
            if not has_header:
                body = []
                if vkhod:
                    vk = ', '.join(vkhod[:10])
                    if len(vkhod) > 10:
                        vk += ', ...'
                    body.append(f'ВХОД ({len(vkhod)}): {vk}')
                if vnesh:
                    vn = ', '.join(vnesh[:10])
                    if len(vnesh) > 10:
                        vn += ', ...'
                    body.append(f'ВНЕШ ({len(vnesh)}): {vn}')
                title = f'Модуль {mod_name}  СТАРТ={mod_start}' if mod_name else info['instr']
                out.extend(block(title, body))
            header_inserted = True
        # ── Вставить шапку процедуры ──
        if not has_macros and line_no in proc_map:
            # Проверяем, нет ли уже шапки после этой строки
            next_idx = line_no  # 0-based индекс следующей строки
            has_header = False
            for j in range(next_idx, min(next_idx + 3, len(lines))):
                lj = lines[j].strip()
                if lj and lj[0] == '*':
                    has_header = True
                    break
                if lj and lj[0] != '*':
                    break
            if not has_header:
                p = proc_map[line_no]
                body = []
                if p['regs']:
                    body.append(f'Регистры: {", ".join(f"М{r}" for r in p["regs"])}')
                else:
                    body.append('Регистры: -')
                if p['entries']:
                    body.append(f'Вход: {", ".join(p["entries"][:8])}')
                else:
                    body.append(f'Вход: {p["name"]}')
                if p['exits']:
                    body.append(f'Выход: {", ".join(p["exits"][:6])}')
                title = p['name']
                out.extend(block(title, body))
    with open(outp, 'w', encoding='utf-8') as f:
        f.writelines(out)
    cn = sum(1 for l in lines if l.strip() and l.strip() != '*' and l.strip()[0] != '*')
    icn = sum(1 for l in out if '  ,' in l.rstrip('\n'))
    print(f'Файл: {inp}')
    print(f'Исходных строк: {len(lines)}')
    print(f'Выход: {len(out)} строк')
    print(f'С комментарием: {icn} / {cn} ({100*icn//cn if cn else 0}%%)')
    print(f'Записано: {outp}')
    return outp

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    outp = process(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    if outp and outp.endswith('.be'):
        src = sys.argv[1]
        if os.path.abspath(src) != os.path.abspath(outp):
            ans = input('Применить к исходнику и сделать make clean && make? [y/N] ')
            if ans.strip().lower() == 'y':
                shutil.copy2(outp, src)
                os.system('make clean && make')
