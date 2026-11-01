#!/usr/bin/env perl
# extract_labels.pl — Извлечение таблицы меток из листинга БЭМШ
#
# Формат листинга (колонки):
#   АДРЕС(5) КОМАНДА(?) ... N(4) ГЕН(4) [МЕТКА] ОПЕРАЦИЯ [ОПЕРАНД]
#
# Пример строки с меткой:
#   40005 00 24 02003       0115  0041 УСТЕРМ УИА   '2003'
#
# Пример строки без метки:
#   40004 04 000 1171 41171 0114  0040        ЗП    РПРИЕМ
#
# Формат вывода:
#   <относительный_адрес> <метка>
#   00005 УСТЕРМ
#
# Использование:
#   perl extract_labels.pl <listing.lst> <base_octal>
#   perl extract_labels.pl svyaz7.lst 40000
#   perl extract_labels.pl konfus.lst 70000

use strict;
use warnings;
use utf8;
binmode(STDOUT, ':utf8');

my $listing = $ARGV[0] or die "Использование: $0 <listing.lst> <base_octal>\n";
my $base = 0;
$base = oct($ARGV[1]) if defined $ARGV[1];

open(my $fh, '<:encoding(UTF-8)', $listing) or die "Не могу открыть $listing: $!\n";

while (<$fh>) {
    chomp;
    # Строка с адресом (5 цифр) и операцией (2-3 кириллические буквы)
    # Between gen number and operation there may be a label
    # Key pattern: after gen number, if next non-space starts with Cyrillic uppercase
    # and is followed by another Cyrillic uppercase = that's a label
    if (/^\s+(\d{5})\s+.+?\s+(\d{4})\s+(\d{4})\s{1,3}(\p{Cyrillic}+)\s+(\p{Cyrillic}+)/) {
        my $addr  = $1;
        my $label = $4;
        my $op    = $5;
        # Переводим абсолютный адрес в адрес относительно модуля
        my $abs = oct($addr);
        my $rel = $abs - $base;
        printf "%05o %s\n", $rel, $label;
    }
}

close($fh);
