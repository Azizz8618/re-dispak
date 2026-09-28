#!/bin/bash
# build_madlen.sh — сборка МАДЛЕН-программ через dispak
# Использование: ./build_madlen.sh test_sis_k71.txt [имя_задачи]
#
# Формирует .b6 файл из МАДЛЕН-исходника:
#   - Заголовок Б6 (шифр, лента, бутстрап)
#   - Директивы Б6 (*name, *no list, *assembler)
#   - Исходник (strip комментариев '.' и инлайн '.комментарий')
#   - Хвост (*execute, *end file, еконец)

set -e

SRC="$1"
NAME="${2:-$(basename "$SRC" .txt)}"
B6="${SRC%.txt}.b6"

if [ -z "$SRC" ]; then
    echo "Использование: $0 <source.txt> [имя_задачи]"
    exit 1
fi

# Генерируем .b6 из МАДЛЕН-исходника
python3 - "$SRC" "$NAME" "$B6" << 'PYEOF'
import re, sys

src, name, b6 = sys.argv[1], sys.argv[2], sys.argv[3]

header = [
    'шифр 419999 зс5^',
    'лен 41(2048)^',
    'eeв1а3',
    f'*name {name}',
    '*no list',
    '*assembler',
]
footer = ['*execute', '*end file', '``````', 'еконец']

with open(src, 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
for line in lines:
    raw = line.rstrip('\n')
    stripped = raw.strip()
    if stripped.startswith('.'):
        out.append('')
        continue
    if '.' in raw and not stripped.startswith('.'):
        new_line = re.sub(r' \..*$', '', raw)
        out.append(new_line)
        continue
    out.append(raw)

with open(b6, 'w', encoding='utf-8') as f:
    for line in header:
        f.write(line + '\n')
    for line in out:
        f.write(line + '\n')
    for line in footer:
        f.write(line + '\n')

print(f'{name}: {len(out)} lines -> {b6}')
PYEOF

echo "Запуск dispak..."
dispak "$B6" 2>&1 | tee "${B6%.b6}.lst"

if grep -q 'БЫЛИ ОШИБКИ' "${B6%.b6}.lst"; then
    echo "ОШИБКИ ТРАНСЛЯЦИИ"
    exit 1
else
    echo "Трансляция без ошибок"
fi
