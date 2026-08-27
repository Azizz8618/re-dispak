#!/bin/bash
# backup_config.sh — резервное копирование конфигурации проекта
# Запуск: ./backup_config.sh

PROJECT_DIR="/home/azizz/Yandex.Disk/re_dispak/re-dispak"
BACKUP_BASE="/home/azizz/Yandex.Disk/config_backup"
PROJECT_NAME="re-dispak"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_BASE}/${PROJECT_NAME}_${TIMESTAMP}"

# Файлы конфигурации проекта
CONFIG_FILES=".clinerules AGENTS.md COMMANDS.md README.md"

# Глобальные файлы конфигурации (из домашнего каталога)
GLOBAL_FILES=".clinerules"

# Глобальные каталоги (из домашнего каталога)
GLOBAL_DIRS=".cline .vscode"

# Создаём каталог резервной копии
mkdir -p "$BACKUP_DIR"

# Копируем файлы проекта
for f in $CONFIG_FILES; do
    if [ -f "$PROJECT_DIR/$f" ]; then
        cp "$PROJECT_DIR/$f" "$BACKUP_DIR/"
    fi
done

# Копируем глобальные файлы (с префиксом global_)
for f in $GLOBAL_FILES; do
    if [ -f "$HOME/$f" ]; then
        cp "$HOME/$f" "$BACKUP_DIR/global_$f"
    fi
done

# Копируем глобальные каталоги (с префиксом global_)
for d in $GLOBAL_DIRS; do
    if [ -d "$HOME/$d" ]; then
        cp -r "$HOME/$d" "$BACKUP_DIR/global_$d"
    fi
done

# Создаём манифест с контрольными суммами
MANIFEST="$BACKUP_DIR/MANIFEST.txt"
echo "=== РЕЗЕРВНАЯ КОПИЯ КОНФИГУРАЦИИ ===" > "$MANIFEST"
echo "Проект:    $PROJECT_NAME" >> "$MANIFEST"
echo "Дата:      $(date '+%Y-%m-%d %H:%M:%S')" >> "$MANIFEST"
echo "Каталог:   $BACKUP_DIR" >> "$MANIFEST"
echo "" >> "$MANIFEST"
echo "=== КОНТРОЛЬНЫЕ СУММЫ (md5) ===" >> "$MANIFEST"
cd "$BACKUP_DIR"
for f in $(find . -type f \( -name '*.md' -o -name '.clinerules' -o -name 'global_*' -o -name '*.json' \) | sort); do
    md5sum "$f" >> "$MANIFEST"
done
echo "" >> "$MANIFEST"
echo "=== РАЗМЕРЫ ФАЙЛОВ ===" >> "$MANIFEST"
ls -lh *.md .clinerules global_* 2>/dev/null | awk '{print $9, $5}' >> "$MANIFEST"

echo "$BACKUP_DIR"
