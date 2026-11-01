#!/bin/bash
#
# gens_build.sh — Сборка и развёртывание варианта ОС ДИСПАК через ГЕНС
#
# Использование:
#   ./gens_build.sh <конфиг.b6> [--dry-run] [--restart]
#
# Примеры:
#   ./gens_build.sh gens/gens_dks3.b6
#   ./gens_build.sh gens/gens_dks3.b6 --dry-run
#   ./gens_build.sh gens/gens_dks3.b6 --restart
#
# Алгоритм:
#   1. Валидация конфига
#   2. Бэкап текущего системного диска (2053/2253)
#   3. Запуск ГЕНС через dispak
#   4. Копирование результата в MD/2253
#   5. Обновление dispak.ini (если нужно)
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BESM6_DIR="/home/azizz/Yandex.Disk/simh/BESM6"
MD_DIR="$BESM6_DIR/MD"
OSZAGR_DIR="$BESM6_DIR/OSZAGR"
DISPAK_INI="$OSZAGR_DIR/dispak.ini"
WORK_DIR="/tmp/besm6_work"
ORIG_DIR="/home/azizz/Yandex.Disk/rezerv/BESM6_rez/MD"
DISK_NUM="2053"
DISK_EMU="2253"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()   { echo -e "${GREEN}[ГЕНС]${NC} $*"; }
warn()  { echo -e "${YELLOW}[ВНИМАНИЕ]${NC} $*"; }
error() { echo -e "${RED}[ОШИБКА]${NC} $*"; exit 1; }

CONFIG_FILE=""
DRY_RUN=false
DO_RESTART=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        --restart) DO_RESTART=true; shift ;;
        -h|--help)
            echo "Использование: $0 <конфиг.b6> [--dry-run] [--restart]"
            exit 0 ;;
        *) CONFIG_FILE="$1"; shift ;;
    esac
done

[[ -z "$CONFIG_FILE" ]] && error "Укажите файл конфигурации"
[[ -f "$CONFIG_FILE" ]] || error "Файл не найден: $CONFIG_FILE"

# Разрешаем абсолютный путь к конфигу ДО смены каталога
CONFIG_FILE="$(cd "$(dirname "$CONFIG_FILE")" && pwd)/$(basename "$CONFIG_FILE")"

log "=== Сборка ГЕНС ==="
log "Конфиг: $CONFIG_FILE"
log "Дата: $(date '+%Y-%m-%d %H:%M:%S')"

# ===== ШАГ 1: ВАЛИДАЦИЯ =====
log "--- Шаг 1: Валидация ---"
for field in "MЛЗAГ" "ОЗУ" "ТЕРМ" "ЕКОНЕЦ"; do
    grep -q "^$field" "$CONFIG_FILE" || error "Отсутствует поле: $field"
done
MLZAG=$(grep "^MЛЗAГ" "$CONFIG_FILE" | head -1 | sed 's/\^.*//' | awk '{print $2}')
TERM_LINES=$(grep "^ТЕРМ" "$CONFIG_FILE" | sed 's/\^//g')
log "  МЛЗАГ: $MLZAG"
echo "$TERM_LINES" | sed 's/^/  ТЕРМ: /'

$DRY_RUN && { log "Dry run — завершение"; exit 0; }

# ===== ШАГ 2: БЭКАП =====
log "--- Шаг 2: Бэкап дисков ---"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DISK_PATH="$WORK_DIR/$DISK_NUM"
EMU_DISK="$MD_DIR/$DISK_EMU"

# Бэкап текущего образа
if [[ -f "$EMU_DISK" ]]; then
    BACKUP_EMU="$MD_DIR/${DISK_EMU}.bak.${TIMESTAMP}"
    cp -p "$EMU_DISK" "$BACKUP_EMU"
    log "  $DISK_EMU → ${DISK_EMU}.bak.${TIMESTAMP} ($(stat -c%s "$EMU_DISK") байт)"
    md5sum "$EMU_DISK" | awk '{print "  MD5: "$1}'
else
    warn "  $EMU_DISK не найден!"
fi

# Бэкап рабочего диска
if [[ -f "$DISK_PATH" ]]; then
    BACKUP_WORK="$MD_DIR/${DISK_NUM}.bak.${TIMESTAMP}"
    cp -p "$DISK_PATH" "$BACKUP_WORK"
    log "  $DISK_NUM → ${DISK_NUM}.bak.${TIMESTAMP} ($(stat -c%s "$DISK_PATH") байт)"
fi

# Проверка эталона
if [[ -f "$ORIG_DIR/$DISK_EMU" ]]; then
    log "  Эталон: $(ls -lh "$ORIG_DIR/$DISK_EMU" | awk '{print $5}')"
else
    warn "  Эталон $ORIG_DIR/$DISK_EMU НЕ НАЙДЕН!"
fi

# ===== ШАГ 3: ПОДГОТОВКА РАБОЧЕГО КАТАЛОГА =====
log "--- Шаг 3: Подготовка ---"
mkdir -p "$WORK_DIR"
if [[ ! -f "$DISK_PATH" ]]; then
    if [[ -f "$ORIG_DIR/$DISK_EMU" ]]; then
        cp -p "$ORIG_DIR/$DISK_EMU" "$DISK_PATH"
        log "  Создан $DISK_PATH из эталона"
    else
        for f in /usr/local/share/besm6/[0-9]*; do
            fname=$(basename "$f")
            [[ ! -f "$WORK_DIR/$fname" ]] && cp -p "$f" "$WORK_DIR/$fname" 2>/dev/null || true
        done
        log "  Диски скопированы из /usr/local/share/besm6"
    fi
else
    log "  Рабочий каталог готов ($DISK_PATH: $(stat -c%s "$DISK_PATH") байт)"
fi

# ===== ШАГ 4: ЗАПУСК ГЕНС =====
log "--- Шаг 4: Запуск ГЕНС ---"
BESM6_PATH="$WORK_DIR" dispak --path="$WORK_DIR" "$CONFIG_FILE" 2>&1 | tee /tmp/gens_output.txt

if grep -q "ЗАПИСАН" /tmp/gens_output.txt; then
    grep "ЗАПИСАН" /tmp/gens_output.txt | sed 's/^/  /'
else
    error "ГЕНС не записал варианты!"
fi

# ===== ШАГ 5: КОПИРОВАНИЕ =====
log "--- Шаг 5: Копирование ---"
[[ -f "$DISK_PATH" ]] || error "Результат ($DISK_PATH) не найден!"

NEW_SIZE=$(stat -c%s "$DISK_PATH")
log "  Новый образ: $NEW_SIZE байт"
cp -p "$DISK_PATH" "$EMU_DISK"
md5sum "$EMU_DISK" | awk '{print "  MD5: "$1}'

# Именованная копия
CFG_NAME=$(basename "$CONFIG_FILE" .b6)
cp -p "$EMU_DISK" "$MD_DIR/${DISK_EMU}.${CFG_NAME}"
log "  Именованная копия: ${DISK_EMU}.${CFG_NAME}"

# ===== ШАГ 6: СВОДКА =====
log "=== Готово ==="
log "Диски в MD/:"
ls -lh "$MD_DIR/${DISK_EMU}"* 2>/dev/null | awk '{print "  "$NF" ("$5")"}'
log ""
log "Следующие шаги:"
log "  1. Обновите dispak.ini (set ttyN dks) если нужно"
log "  2. Перезапустите эмулятор"
log "  3. Проверьте DKS: telnet localhost 4203"