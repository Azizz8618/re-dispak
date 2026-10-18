#!/usr/bin/env python3
"""
Комментирование ekvvod.be:
- Шапки: блоки * в первой колонке с ***** границами
- Строчные: "  , текст" на ТОЙ ЖЕ строке
- 1366 оригинальных строк СОХРАНЯЮТСЯ (кроме добавления ,)
"""
S51 = '*' * 51 + '\n'

def block(title, body=None, regs=None, entry=None, exit_=None):
    """Блок-шапка: возвращает список строк с \\n на конце КАЖДОЙ"""
    r = ['\n', S51]
    t = f'* {title}'
    while len(t) < 49: t += ' '
    r.append(t + ' *\n')
    if body:
        for b in body:
            line = f'*   {b}'
            while len(line) < 49: line += ' '
            r.append(line + ' *\n')
    if regs:
        r.append('*' + ' '*47 + ' *\n')
        r.append('*   Регистры:' + ' '*34 + ' *\n')
        for rg in regs:
            line = f'*     {rg}'
            while len(line) < 49: line += ' '
            r.append(line + ' *\n')
    if entry:
        r.append('*' + ' '*47 + ' *\n')
        r.append(f'*   Вход: {entry}'.ljust(49) + ' *\n')
    if exit_:
        r.append(f'*   Выход: {exit_}'.ljust(49) + ' *\n')
    r.append(S51)
    return r

def ic(line, comment):
    """Добавить строчный комментарий: '  , текст'"""
    return line.rstrip('\n') + '  ,' + comment + '\n'

# Читаем оригинал
with open('/home/azizz/Yandex.Disk/re-dispak/ekvvod.be',
          'r', encoding='utf-8') as f:
    orig = f.readlines()

assert len(orig) == 1366, f"Ожидалось 1366 строк, получено {len(orig)}"

out = []

# Обработка построчно: orig[i] — строка с номером i+1
for i, line in enumerate(orig):
    ln = i + 1  # номер строки в оригинале (1-based)

    # === СТРОКА 1: ЭКВВОД СТАРТ ===
    if ln == 1:
        out.extend(block(
            'МОДУЛЬ ЭКВВОД — ДИСПЕТЧЕР',
            ['Экстракодов ОС ДИСПАК.',
             'Обрабатывает Э100–Э221.',
             'Управление каталогом задач,',
             'оперативной памятью, МД.'],
            ['М7  — базовый адрес ИПЗ',
             'М3  — адрес ИПЗ (phys.)',
             'М16 — параметры вызова']))
        out.append(ic(line, ' начало модуля в 8-м секторе'))
        continue

    # === СТРОКИ 2-4: Б, Е, М ===
    if ln == 2:
        out.append(ic(line, ' 8-ричный режим адресации'))
        continue
    if ln == 3:
        out.append(ic(line, ' чётная адресация'))
        continue
    if ln == 4:
        out.append(ic(line, ' режим модуля'))
        continue

    # === СТРОКА 5: * (пустой комментарий) ===
    if ln == 5:
        out.append(line)
        continue

    # === СТРОКА 6: УПОТР ===
    if ln == 6:
        out.append(ic(line, ' М7 := адрес начала ИПЗ'))
        continue

    # === СТРОКА 7: КОНД В'0' ===
    if ln == 7:
        out.append(ic(line, ' неиспользуемая ячейка'))
        continue

    # === СТРОКА 8: КОНД М41В'3' РЖА 3 ===
    if ln == 8:
        out.append(ic(line, ' РЖА 3 (режим работы)'))
        continue

    # === СТРОКА 9: КОНД (21)В'0' ===
    if ln == 9:
        out.append(ic(line, ' 21 нулевых слова (резерв)'))
        continue

    # === СТРОКА 10: КОНД В'0' НЕ ЗАНИМАТЬ ===
    if ln == 10:
        out.append(ic(line, ' последняя ячейка'))
        continue

    # === СТРОКА 11: КВ ЗП 34(М3) — КОНЕЦ ===
    if ln == 11:
        out.extend(block(
            'КОНЕЦ — ЗАВЕРШЕНИЕ ЭКСТРАКОДА',
            ['Запись результата в ИПЗ',
             'и возврат из экстракода.'],
            ['М3  — адрес ИПЗ']))
        out.append(ic(line, ' результат → 34(М3)'))
        continue

    # === СТРОКА 12: ПБ КОНЕЦ1 ===
    if ln == 12:
        out.append(ic(line, ' переход к завершению'))
        continue

    # === СТРОКА 13 ===
    if ln == 13:
        out.append(ic(line, ' 25-я ячейка, НЕ ЗАНИМАТЬ'))
        continue

    # === СТРОКА 14: Р1 ПАМ 1 — рабочие ячейки ===
    if ln == 14:
        out.extend(block(
            'РАБОЧИЕ ЯЧЕЙКИ МОДУЛЯ',
            ['Р1–Р4, РА, ИР16, РР, Ш, КИС, R1, R2']))
        out.append(ic(line, ' Р1'))
        continue
    if ln == 15:
        out.append(ic(line, ' Р2'))
        continue
    if ln == 16:
        out.append(ic(line, ' Р3'))
        continue
    if ln == 17:
        out.append(ic(line, ' Р4'))
        continue
    if ln == 18:
        out.append(ic(line, ' РА — адрес области данных'))
        continue
    if ln == 19:
        out.append(ic(line, ' ПРИП — приоритет'))
        continue
    if ln == 20:
        out.append(ic(line, ' маска для Э64'))
        continue
    if ln == 21:
        out.append(ic(line, ' время работы ЭКВВОД'))
        continue
    if ln == 22:
        out.append(ic(line, ' промежуточный регистр 16'))
        continue
    if ln == 23:
        out.append(ic(line, ' РР — результат работы'))
        continue
    if ln == 24:
        out.append(ic(line, ' Ш — шкала/маска'))
        continue
    if ln == 25:
        out.append(ic(line, ' КИС — контрольная информация'))
        continue
    if ln == 26:
        out.append(ic(line, ' R1 — вспомогательная'))
        continue
    if ln == 27:
        out.append(ic(line, ' R2 — вспомогательная'))
        continue

    # === СТРОКА 28: ВХОД В ЭКВВОД ===
    if ln == 28:
        out.extend(block(
            'ВХОД В ЭКВВОД — ИНИЦИАЛИЗАЦИЯ',
            ['Проверка типа вызова:',
             'М4=3 → КОН1 (начало задачи),',
             'иначе → обработка экстракода.'],
            ['М3  — адрес ИПЗ',
             'М7  — адрес начала ИПЗ',
             'М2  — номер вызова',
             'М4  — тип (3=начало)'],
            entry='УПОТР ЭКВВОД(М7)',
            exit_='КОНЕЦ1 / КОН1'))
        out.append(ic(line, ' М16 := 3 (признак типа)'))
        continue

    # === СТРОКА 29 ===
    if ln == 29:
        out.append(ic(line, ' выделить младшие 3 бита'))
        continue
    if ln == 30:
        out.append(ic(line, ' если М4=3 → КОН1'))
        continue
    if ln == 31:
        out.append(ic(line, ' признак → почту задачи'))
        continue
    if ln == 32:
        out.append(ic(line, ' М2 := номер вызова'))
        continue
    if ln == 33:
        out.append(ic(line, ' адрес ИПЗ из ОБВНП+28'))
        continue
    if ln == 34:
        out.append(ic(line, ' обнулить сумматор'))
        continue
    if ln == 35:
        out.append(ic(line, ' рабочий адрес := 0'))
        continue
    if ln == 36:
        out.append(ic(line, ' М12 := 0'))
        continue
    if ln == 37:
        out.append(ic(line, ' М4 := 0'))
        continue
    if ln == 38:
        out.append(ic(line, ' М5 := 0'))
        continue
    if ln == 39:
        out.append(ic(line, ' А := 1 (маска)'))
        continue
    if ln == 40:
        out.append(ic(line, ' младший модуль := 1'))
        continue
    if ln == 41:
        out.append(ic(line, ' R := 1 (для ТБУФ)'))
        continue
    if ln == 42:
        out.append(ic(line, ' номер модуля из ОБВНП'))
        continue
    if ln == 43:
        out.append(ic(line, ' НМ := номер модуля'))
        continue
    if ln == 44:
        out.append(ic(line, ' адрес ИПЗ из ТУСП'))
        continue
    if ln == 45:
        out.append(ic(line, ' М3 := физ.адрес ИПЗ'))
        continue
    if ln == 46:
        out.append(ic(line, ' слово 36 ИПЗ'))
        continue
    if ln == 47:
        out.append(ic(line, ' биты 15–11 (тип задачи)'))
        continue
    if ln == 48:
        out.append(ic(line, ' если ≠0 → АВОС'))
        continue
    if ln == 49:
        out.append(ic(line, ' слово 44(М3) — код операции'))
        continue
    if ln == 50:
        out.append(ic(line, ' старший байт'))
        continue
    if ln == 51:
        out.append(ic(line, ' вычесть 7'))
        continue
    if ln == 52:
        out.append(ic(line, ' если >7 → ВВОДМ'))
        continue
    if ln == 53:
        out.append(ic(line, ' М13 := 0'))
        continue
    if ln == 54:
        out.append(ic(line, ' сравнить с ЧЭК (=121)'))
        continue
    if ln == 55:
        out.append(ic(line, ' если = ЧЭК → дешифровка'))
        continue
    if ln == 56:
        out.append(ic(line, ' М13 := 0 (нестандартный)'))
        continue
    if ln == 57:
        out.append(ic(line, ' переход к ВЫЗ4'))
        continue

    # === СТРОКА 58: КПР1 ===
    if ln == 58:
        out.extend(block(
            'КПР1/КПР — ЧТЕНИЕ КАТАЛОГА С МД',
            ['Чтение каталога задачи.'],
            ['М5  — номер подкаталога',
             'КАТ — адрес каталога',
             'М1  — начало листа каталога',
             'М16 — параметр ФИЗОБМ'],
            entry='ВЫЗ4 / КПР1',
            exit_='ПБ (М6)'))
        out.append(ic(line, ' номер задачи из М2'))
        continue

    if ln == 59:
        out.append(ic(line, ' выделить 4 бита'))
        continue
    if ln == 60:
        out.append(ic(line, ' М5 := номер подкаталога'))
        continue
    if ln == 61:
        out.append(ic(line, ' повторно загрузить М2'))
        continue
    if ln == 62:
        out.append(ic(line, ' сдвиг влево на 4'))
        continue
    if ln == 63:
        out.append(ic(line, ' вычесть 2'))
        continue
    if ln == 64:
        out.append(ic(line, ' объединить с КАТ1'))
        continue
    if ln == 65:
        out.append(ic(line, ' КАТ := адрес каталога'))
        continue
    if ln == 66:
        out.append(ic(line, ' загрузить R (лист каталога)'))
        continue
    if ln == 67:
        out.append(ic(line, ' запрос страницы ОЗУ'))
        continue
    if ln == 68:
        out.append(ic(line, ' сдвиг → физ.адрес'))
        continue
    if ln == 69:
        out.append(ic(line, ' М1 := начало листа'))
        continue
    if ln == 70:
        out.append(ic(line, ' сдвиг на 2 (номер листа)'))
        continue
    if ln == 71:
        out.append(ic(line, ' добавить НМ (барабан)'))
        continue
    if ln == 72:
        out.append(ic(line, ' М4 := 0 (смещение)'))
        continue
    if ln == 73:
        out.append(ic(line, ' сложить с КАТ'))
        continue
    if ln == 74:
        out.append(ic(line, ' полный физ.адрес каталога'))
        continue
    if ln == 75:
        out.append(ic(line, ' чтение каталога с диска'))
        continue
    if ln == 76:
        out.append(ic(line, ' М16 := 3 (чтение)'))
        continue
    if ln == 77:
        out.append(ic(line, ' возврат по М6'))
        continue

    # === СТРОКА 78: КНЦ ===
    if ln == 78:
        out.extend(block(
            'КНЦ/АВОС1/АВОС — ЗАВЕРШЕНИЕ',
            ['Освобождение ресурсов,',
             'аварийный выход.'],
            ['М6  — код ошибки',
             'М17 — адрес возврата',
             'М15 — адрес ИПЗ']))
        out.append(ic(line, ' загрузить адрес каталога'))
        continue

    if ln == 79:
        out.append(ic(line, ' отдать лист ОЗУ'))
        continue
    if ln == 80:
        out.append(ic(line, ' М17 := М6 (возврат)'))
        continue
    if ln == 81:
        out.append(ic(line, ' М15 := М3 (ИПЗ)'))
        continue
    if ln == 82:
        out.append(ic(line, ' М16 := КОНЕЦ1'))
        continue
    if ln == 83:
        out.append(ic(line, ' М16 := адрес КОНЕЦ1'))
        continue
    if ln == 84:
        out.append(ic(line, ' М15 := 2003 (супервизор)'))
        continue
    if ln == 85:
        out.append(ic(line, ' переход к АВОСТА'))
        continue
    if ln == 86:
        out.append(ic(line, ' М6 := 36 (код ошибки)'))
        continue
    if ln == 87:
        out.append(ic(line, ' переход к АВОС1'))
        continue
    if ln == 88:
        out.append(ic(line, ' М6 := 41 (код G10106)'))
        continue
    if ln == 89:
        out.append(ic(line, ' переход к АВОС1'))
        continue

    # === СТРОКА 90: ВЫЗ1 ===
    if ln == 90:
        out.extend(block(
            'ВЫЗ1/ВЫЗА — ВЫЗОВ ПОДПРОГРАММЫ',
            ['Диспетчер вызовов модулей',
             'ЭК2–ЭК7. Формирование',
             'адреса обработчика.'],
            ['М16 — параметры (КЭК)',
             'М1  — база модуля',
             'М13 — смещение обработчика',
             'РА  — адрес области данных']))
        out.append(ic(line, ' М16 := КЭКСТ-Э (каталог)'))
        continue

    if ln == 91:
        out.append(ic(line, ' слияние с М7'))
        continue
    if ln == 92:
        out.append(ic(line, ' номер задачи из М7'))
        continue
    if ln == 93:
        out.append(ic(line, ' ×4 (размер записи)'))
        continue
    if ln == 94:
        out.append(ic(line, ' объединить с каталогом'))
        continue
    if ln == 95:
        out.append(ic(line, ' +НОММБ1 (база модуля)'))
        continue
    if ln == 96:
        out.append(ic(line, ' М1 := М7'))
        continue
    if ln == 97:
        out.append(ic(line, ' +768 (область экстракодов)'))
        continue
    if ln == 98:
        out.append(ic(line, ' РА := адрес модуля'))
        continue
    if ln == 99:
        out.append(ic(line, ' выделить 8 бит (номер)'))
        continue
    if ln == 100:
        out.append(ic(line, ' XOR с НСЕ (проверка)'))
        continue
    if ln == 101:
        out.append(ic(line, ' М15 := 2003'))
        continue
    if ln == 102:
        out.append(ic(line, ' модификация по М13'))
        continue
    if ln == 103:
        out.append(ic(line, ' чтение обработчика'))
        continue
    if ln == 104:
        out.append(ic(line, ' повторный XOR с НСЕ'))
        continue
    if ln == 105:
        out.append(ic(line, ' сброс НСЕ'))
        continue
    if ln == 106:
        out.append(ic(line, ' загрузить РА'))
        continue
    if ln == 107:
        out.append(ic(line, ' М16 := М1'))
        continue
    if ln == 108:
        out.append(ic(line, ' М16 += М13 (смещение)'))
        continue
    if ln == 109:
        out.append(ic(line, ' переход к ФИЗОБМ'))
        continue

    # === СТРОКИ 110-121: ВЫЗ2-ВЫЗ7 ===
    if ln == 110:
        out.extend(block(
            'ВЫЗ2–ВЫЗ7 — ДИСПЕТЧЕРЫ МОДУЛЕЙ',
            ['Каждый устанавливает М16',
             'и переходит к ВЫЗА.'],
            ['М16 — смещение каталога КЭКx']))
        out.append(ic(line, ' М16 := КЭК2-Э'))
        continue
    if ln == 111:
        out.append(ic(line, ' переход к ВЫЗА'))
        continue
    if ln == 112:
        out.append(ic(line, ' М16 := КЭК3-Э'))
        continue
    if ln == 113:
        out.append(ic(line, ' переход к ВЫЗА'))
        continue
    if ln == 114:
        out.append(ic(line, ' М16 := КЭК4-Э'))
        continue
    if ln == 115:
        out.append(ic(line, ' переход к ВЫЗА'))
        continue
    if ln == 116:
        out.append(ic(line, ' М16 := КЭК5-Э'))
        continue
    if ln == 117:
        out.append(ic(line, ' переход к ВЫЗА'))
        continue
    if ln == 118:
        out.append(ic(line, ' М16 := КЭК6-Э'))
        continue
    if ln == 119:
        out.append(ic(line, ' переход к ВЫЗА'))
        continue
    if ln == 120:
        out.append(ic(line, ' М16 := КЭК7-Э'))
        continue
    if ln == 121:
        out.append(ic(line, ' переход к ВЫЗА'))
        continue

    # === СТРОКА 122: ЭС100А ===
    if ln == 122:
        out.extend(block(
            'ДЕШЭК/ЭС100А — ТАБЛИЦА ЭКСТРАКОДОВ',
            ['Обработчики Э100–Э221.',
             'Загрузка параметра,',
             'установка М13, переход ВЫЗx.'],
            ['М3  — адрес ИПЗ',
             'М13 — смещение обработчика']))
        out.append(ic(line, ' вход: дешифровка'))
        continue

    # Строки 123-289: таблица экстракодов — комментарии
    ext_comments = {
        123: ' слово из ИПЗ',
        126: ' Э100: загрузить ШИФ(М3)',
        127: ' выдать шифр (Э105Г)',
        128: ' Э101: слово 36 ИПЗ',
        129: ' выдать причину аварии',
        130: ' выделить 6 бит',
        131: ' Э102: число авостов',
        134: ' Э103: М13 := Э104-ЭК2',
        135: ' к ВЫЗ2',
        136: ' Э104: М4 := 0',
        137: ' к ДЕЛЬТА',
        138: ' Э105: М13 := 0',
        139: ' к Э106',
        140: ' Э106: М13 := 16',
        142: ' Э108: М14 := 64',
        143: ' к Э110',
        144: ' Э109: слово ИПЗ (≠0)',
        145: ' к Э111',
        146: ' Э112: М4 := 1',
        147: ' к ДЕЛЬТА (для МД)',
        148: ' Э113: М5 := 1',
        149: ' к ДД',
        150: ' Э114: загрузить ГОД',
        152: ' ENQ: М17 := 0',
        153: ' к Э115',
        154: ' DEQ: М17 := 1',
        155: ' к Э115',
        156: ' Э117: М13 := Э116-ЭТ',
        157: ' к ВЫЗ1',
        158: ' Э120: М13 := Э120-ЭК4',
        159: ' к ВЫЗ4',
        160: ' Э121: М13 := ЭК121-ЭК4',
        161: ' к ВЫЗ4',
        162: ' Э122: М13 := Э122-ЭТ',
        163: ' к ВЫЗ1',
        164: ' Э123: М13 := Э123-ЭК4',
        165: ' отказ от пароля',
        166: ' загрузить номер задачи',
        167: ' выдать номер задачи',
        168: ' Э125: М13 := СПЕЦ-ЭТ',
        169: ' к ВЫЗ1',
        170: ' Э126: пароль Э72',
        171: ' к ВЫЗ1',
        172: ' Э127: проверка пароля',
        173: ' к ВЫЗ1',
        174: ' Э130: М13 := Э130-ЭТ',
        175: ' к ВЫЗ1',
        176: ' слово из ИПЗ',
        178: ' Э132: М13 := Э132-ЭТ',
        179: ' к ВЫЗ1',
        180: ' Э133: вход из ЭК7',
        181: ' к ВЫЗ7',
        182: ' Э134: М13 := Э134-ЭТ',
        183: ' к ВЫЗ1',
        184: ' Э135: М13 := Э135-ЭТ',
        185: ' к ВЫЗ1',
        186: ' Э136 (СВС): загрузить 0',
        188: ' Э137: загрузить 0',
        190: ' Э140: М13 := Э140-ЭК5',
        191: ' к ВЫЗ5',
        192: ' М1 := М3+1',
        194: ' Э142: М13 := Э142-ЭК3',
        195: ' к ВЫЗ3',
        196: ' М1 := М3+1',
        198: ' Э143: М13 := Э143-ЭК3',
        199: ' к ВЫЗ3',
        200: ' М14 := 1',
        202: ' Э144: М13 := Э144-ЭК4',
        203: ' к ВЫЗ4',
        206: ' выделить биты 20-16',
        207: ' вычесть 1',
        208: ' если >0 → Э146А',
        211: ' Э146А: М13 := 1',
        215: ' Э150: М13 := Э150-ЭК3',
        216: ' к ВЫЗ3',
        218: ' Э151: М13 := Э151-ЭК3',
        219: ' к ВЫЗ3',
        223: ' Э152: М13 := Э152-ЭК3',
        224: ' к ВЫЗ3',
        226: ' Э153: М13 := Э153-ЭК2',
        227: ' к ВЫЗ2',
        229: ' Э154: М13 := Э154-ЭК3',
        230: ' к ВЫЗ3',
        232: ' Э155: М13 := Э155-ЭК2',
        233: ' к ВЫЗ2',
        234: ' Э156: М13 := Э156-ЭТ',
        235: ' к ВЫЗ1',
        240: ' Э161: М13 := Э161-ЭК2',
        241: ' к ВЫЗ2',
        243: ' Э162: М13 := Э162-ЭТ',
        244: ' к ВЫЗ1',
        246: ' Э164: М13 := Э164-ЭК4',
        247: ' к ВЫЗ4',
        251: ' Э166: М13 := Э166-ЭК4',
        252: ' к ВЫЗ4',
        256: ' Э170: М13 := Э170-ЭК2',
        257: ' к ВЫЗ2',
        264: ' Э174: М13 := Э174-ЭК4',
        265: ' к ВЫЗ4',
        271: ' Э176: М13 := Э176-ЭК5',
        272: ' к ВЫЗ5',
        274: ' Э177: М13 := Э177-ЭК5',
        275: ' к ВЫЗ5',
        282: ' Э202: М13 := Э202-ЭК6',
        283: ' к ВЫЗ6',
        285: ' Э203: М13 := Э203-ЭК6',
        286: ' к ВЫЗ6',
        288: ' Э204: М13 := Э204-ЭК6',
        289: ' к ВЫЗ6',
    }
    if 123 <= ln <= 289:
        if ln in ext_comments:
            out.append(ic(line, ext_comments[ln]))
        else:
            out.append(line)
        continue

    # === СТРОКА 290: ЧЭК ===
    if ln == 290:
        out.extend(block(
            'ЧЭК — ГРАНИЦА ЭКСТРАКОДОВ',
            ['121₈ = граница номеров',
             'стандартных экстракодов.']))
        out.append(ic(line, ' ЧЭК = 121₈'))
        continue

    # === СТРОКИ 291-298 ===
    if ln == 291:
        out.append(ic(line, ' Э217: если >0 → Э105Г'))
        continue
    if 292 <= ln <= 298:
        out.append(line)
        continue

    # === СТРОКА 299: ЗИО ===
    if ln == 299:
        out.extend(block(
            'ЗИО/ЦЗИО/ЗАПРЕТ — ВВОД/ВЫВОД',
            ['Зональные операции',
             'ввода/вывода на МД.'],
            ['М10 — блок описания',
             'М11 — адрес буфера',
             'М12 — начальный адрес']))
        out.append(ic(line, ' загрузить ЕЗАР'))
        continue

    # Строки 300-403: ЗИО — без комментариев (код ввода/вывода)
    if 300 <= ln <= 403:
        out.append(line)
        continue

    # === СТРОКА 404: КОНЕЦ/КОНЕЦ1 ===
    if ln == 404:
        out.extend(block(
            'КОНЕЦ/КОНЕЦ1/КОН1 — ЗАВЕРШЕНИЕ',
            ['Начало новой задачи,',
             'завершение обработки.'],
            ['М3  — адрес ИПЗ',
             'М4  — тип задачи (3=начало)'],
            entry='ВХОД',
            exit_='АВОСТА'))
        out.append(ic(line, ' загрузить КАТ'))
        continue

    if 405 <= ln <= 443:
        out.append(line)
        continue

    # === СТРОКА 444: Э111 ===
    if ln == 444:
        out.extend(block(
            'Э111 — ПРИЧИНА ЗАВЕРШЕНИЯ',
            ['Выдача причины завершения',
             'задачи через Э105Г.']))
        out.append(line)
        continue

    if 445 <= ln <= 451:
        out.append(line)
        continue

    # === СТРОКА 452: ДЕЛЬТА ===
    if ln == 452:
        out.extend(block(
            'ДЕЛЬТА — ФИЗИЧЕСКИЙ НОМЕР',
            ['Определение физического',
             'номера МЛ/МД.'],
            ['М4  — тип (0=МЛ, 1=МД)',
             'М5  — номер устройства']))
        out.append(ic(line, ' определение физ.номера'))
        continue

    if 453 <= ln <= 499:
        out.append(line)
        continue

    # === СТРОКА 500: О ===
    if ln == 500:
        out.extend(block(
            'О/НОРМА/ДАЙБОБ/Э105Г',
            ['Выдача данных задаче.',
             'Формирование ответа через Э105Г.'],
            ['М3  — адрес ИПЗ',
             'М4  — смещение в каталоге',
             'М12 — начальный адрес']))
        out.append(ic(line, ' слово из ИПЗ'))
        continue

    if 501 <= ln <= 552:
        out.append(line)
        continue

    # === СТРОКА 553: Э106 ===
    if ln == 553:
        out.extend(block(
            'Э106 — ЧТЕНИЕ ФАЙЛА',
            ['Чтение данных с МД',
             'в буфер задачи.']))
        out.append(ic(line, ' загрузить Е1'))
        continue

    if 554 <= ln <= 623:
        out.append(line)
        continue

    # === СТРОКА 624: Э115 ===
    if ln == 624:
        out.extend(block(
            'Э115 — ENQ/DEQ',
            ['Запрос/освобождение',
             'блокировки ресурса.'],
            ['М17 — тип операции',
             '  0 = ENQ (захват)',
             '  1 = DEQ (освобождение)'],
            entry='Э115',
            exit_='КОНЕЦ1'))
        out.append(ic(line, ' ENQ/DEQ'))
        continue

    if 625 <= ln <= 661:
        out.append(line)
        continue

    # === СТРОКА 662: НЕПА ===
    if ln == 662:
        out.extend(block(
            'НЕПА/АРХЕNQ/EQ — БЛОКИРОВКИ',
            ['Захват и освобождение',
             'дисковых устройств.'],
            ['М16 — блок описания МД',
             'М6  — тип операции']))
        out.append(ic(line, ' начало'))
        continue

    if 663 <= ln <= 734:
        out.append(line)
        continue

    # === СТРОКА 735: ДР ===
    if ln == 735:
        out.extend(block(
            'НС/ДР — СОХРАНЕНИЕ ЗАХВАТА',
            ['Сохранение информации',
             'о захвате устройства.']))
        out.append(ic(line, ' загрузить ЕNQ'))
        continue

    if 736 <= ln <= 776:
        out.append(line)
        continue

    # === СТРОКА 777: ПРОВАР ===
    if ln == 777:
        out.extend(block(
            'ПРОВАР — ПРОВЕРКА АРХИВА',
            ['Проверка архивного',
             'режима работы МД.']))
        out.append(line)
        continue

    if 778 <= ln <= 864:
        out.append(line)
        continue

    # === СТРОКА 865: С1 ===
    if ln == 865:
        out.extend(block(
            'С1/С3/Е — ОШИБКИ БЛОКИРОВКИ',
            ['Обработка ошибок',
             'при захвате ресурсов.']))
        out.append(line)
        continue

    if 866 <= ln <= 890:
        out.append(line)
        continue

    # === СТРОКА 891: ЯЯ ===
    if ln == 891:
        out.extend(block(
            'ЯЯ/Я — ПОИСК ПОДЧИНЁННОЙ',
            ['Поиск подчинённой задачи',
             'в каталоге.']))
        out.append(line)
        continue

    if 892 <= ln <= 939:
        out.append(line)
        continue

    # === СТРОКА 940: ОСВ ===
    if ln == 940:
        out.extend(block(
            'ОСВ/С2 — ОСВОБОЖДЕНИЕ',
            ['Освобождение захваченного',
             'устройства.']))
        out.append(line)
        continue

    if 941 <= ln <= 981:
        out.append(line)
        continue

    # === СТРОКА 982: БРУКС ===
    if ln == 982:
        out.extend(block(
            'БРУКС/БРУК — БРОНИРОВАНИЕ',
            ['Бронирование кусков МД',
             'для операций в/в.']))
        out.append(line)
        continue

    if 983 <= ln <= 1029:
        out.append(line)
        continue

    # === СТРОКА 1030: ВЧА ===
    if ln == 1030:
        out.extend(block(
            'ВЧА/ПК/ПРХ — БУФЕРЫ',
            ['Вычисление адреса буфера,',
             'формирование описателя',
             'обмена с МД.'],
            ['М5  — блок описания',
             'М15 — адрес буфера']))
        out.append(ic(line, ' начало'))
        continue

    if 1031 <= ln <= 1082:
        out.append(line)
        continue

    # === СТРОКА 1083: Э131 ===
    if ln == 1083:
        out.extend(block(
            'Э131 — ОБРАБОТКА ЭКСТРАКОДА',
            ['Специальная обработка',
             'экстракода Э131.']))
        out.append(line)
        continue

    if 1084 <= ln <= 1161:
        out.append(line)
        continue

    # === СТРОКА 1162: ОШКА ===
    if ln == 1162:
        out.extend(block(
            'ОШКА/ЧЛ/��РВН — ОШИБКИ',
            ['Обработка ошибок',
             'при работе с МД и МЛ.']))
        out.append(ic(line, ' загрузить 0'))
        continue

    if 1163 <= ln <= 1173:
        out.append(line)
        continue

    # === СТРОКА 1174: ЗМЛ ===
    if ln == 1174:
        out.extend(block(
            'ЗМЛ/СЦ/МСС — ПОИСК ЛЕНТЫ',
            ['Поиск магнитной ленты',
             'в таблице носителей.'],
            ['М17 — указатель таблицы',
             'М15 — счётчик']))
        out.append(ic(line, ' М16 := 3'))
        continue

    if 1175 <= ln <= 1228:
        out.append(line)
        continue

    # === СТРОКА 1229: НТД ===
    if ln == 1229:
        out.extend(block(
            'НТД/БА/С/КЛА — КАТАЛОГ',
            ['Дополнительный поиск',
             'в каталоге задач.']))
        out.append(ic(line, ' мод. (М17)'))
        continue

    if 1230 <= ln <= 1292:
        out.append(line)
        continue

    # === СТРОКА 1293: КОНСТАНТЫ ===
    if ln == 1293:
        out.extend(block(
            'КОНСТАНТЫ И ДАННЫЕ',
            ['Описатели вызовов КЭК2–7,',
             'маски, адреса,',
             'рабочие ячейки.']))
        out.append(line)
        continue

    if 1294 <= ln <= 1320:
        out.append(line)
        continue

    # === СТРОКА 1321: ВНЕШНИЕ ССЫЛКИ ===
    if ln == 1321:
        out.extend(block(
            'ВНЕШНИЕ ССЫЛКИ',
            ['Модули: ЭК2–ЭК7, ЭКСТ,',
             'ДИСП70, ДИСКИ, ВЗУ,',
             'КАЧКА, СОСТАВ и др.']))
        out.append(line)
        continue

    if 1322 <= ln <= 1365:
        out.append(line)
        continue

    # === СТРОКА 1366: ФИНИШ ===
    if ln == 1366:
        out.append(line)
        continue

    # Необработанная строка — без изменений
    out.append(line)

# Запись
with open('/home/azizz/Yandex.Disk/re-dispak/ekvvod_commented.be',
          'w', encoding='utf-8') as f:
    f.writelines(out)

# Подсчёт оригинальных строк
orig_count = sum(1 for l in out if not l.startswith('*') or l == '*\n' or l.strip() == '*****' + '*' * 40 + '\n')
print(f'Всего строк: {len(out)}')

# Проверим что все оригинальные строки на месте
with open('/home/azizz/Yandex.Disk/re-dispak/ekvvod.be',
          'r', encoding='utf-8') as f:
    orig_lines = [l.rstrip('\n') for l in f.readlines()]

code_out = [l.rstrip('\n') for l in out if not (l.startswith('*') and l.strip().startswith('*') and ' ' not in l.lstrip()[:1])]
# Better check: extract only non-block-comment lines
code_out2 = []
for l in out:
    stripped = l.rstrip('\n')
    # Skip block comment lines (start with * and are part of header)
    if stripped.startswith('*') and not stripped.startswith('*  ,') and len(stripped) > 0:
        # It's a comment line - skip for comparison
        continue
    code_out2.append(stripped)

# Even better: just check that all original lines appear in order
j = 0
ok = True
for i, orig_l in enumerate(orig_lines):
    # Find this line in output
    found = False
    while j < len(out):
        ol = out[j].rstrip('\n')
        if ol == orig_l:
            found = True
            j += 1
            break
        # Skip comment lines and blank lines
        if ol.startswith('*') or ol == '':
            j += 1
            continue
        # Non-comment, non-matching line ��� mismatch
        break
    if not found:
        print(f'ОШИБКА: строка {i+1} оригинала не найдена: {repr(orig_l[:60])}')
        ok = False
        break

if ok:
    print('Все 1366 оригинальных строк на месте!')
