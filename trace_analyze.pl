#!/usr/bin/env perl
# trace_analyze.pl — Анализ трассы БЭСМ-6 с разрешением меток по листингам
#
# Формат трассы (touched.pl output):
#   <cmd>: <zone> <addr>L|R
#   02 50 0133: 0677 0001L
#
# Использование:
#   perl trace_analyze.pl [опции] <trace.txt>
#
# Опции:
#   --labels-dir <path>  — директория с .lst файлами (по умолчанию текущая)
#   --zone <ZZZZ>        — показать только указанную зону
#   --sort zone|addr|count — сортировка (по умолчанию zone+addr)
#   --summary            — только сводка по зонам
#   --unique             — только уникальные адреса в каждой зоне

use strict;
use warnings;
use utf8;
binmode(STDOUT, ':utf8');
binmode(STDERR, ':utf8');

# Конфигурация зон: номер => {имя, листинг, базовый_адрес}
my %ZONE_MODULE = (
    '0677' => { name => 'СВЯЗЬ7',  lst => 'svyaz7.lst',  base => 040000 },
    '0676' => { name => 'КОНФУС',  lst => 'konfus.lst',  base => 070000 },
);

# Параметры по умолчанию
my $labels_dir = '.';
my $filter_zone = '';
my $sort_mode = 'zone';
my $summary_only = 0;
my $unique_only = 0;
my $trace_file = '';

# Парсинг аргументов
while (@ARGV) {
    my $arg = shift @ARGV;
    if    ($arg eq '--labels-dir') { $labels_dir = shift @ARGV; }
    elsif ($arg eq '--zone')       { $filter_zone = shift @ARGV; }
    elsif ($arg eq '--sort')       { $sort_mode = shift @ARGV; }
    elsif ($arg eq '--summary')    { $summary_only = 1; }
    elsif ($arg eq '--unique')     { $unique_only = 1; }
    elsif ($arg =~ /^-/)           { die "Неизвестный аргумент: $arg\n"; }
    else                           { $trace_file = $arg; }
}

die "Использование: $0 [--labels-dir DIR] [--zone ZZZZ] [--sort zone|addr|count] [--summary] [--unique] <trace.txt>\n"
    unless $trace_file;

# ═══ Загрузка таблиц меток из листингов ═══
my %labels;  # zone => { addr_relative => label }

for my $zone (sort keys %ZONE_MODULE) {
    my $info = $ZONE_MODULE{$zone};
    my $lst_path = "$labels_dir/$info->{lst}";
    my $base = $info->{base};
    my $count = 0;

    if (-f $lst_path) {
        open(my $fh, '<:encoding(UTF-8)', $lst_path) or next;
        while (<$fh>) {
            chomp;
            if (/^\s+(\d{5})\s+.+?\s+(\d{4})\s+(\d{4})\s{1,3}(\p{Cyrillic}+)\s+(\p{Cyrillic}+)/) {
                my $abs = oct($1);
                my $rel = $abs - $base;
                $labels{$zone}->{$rel} = $4;
                $count++;
            }
        }
        close($fh);
    }
    printf STDERR "  Зона %s (%s): загружено %d меток из %s\n",
        $zone, $info->{name}, $count, $lst_path;
}

# ═══ Чтение трассы ═══
my @entries;
my %zone_count;
my %zone_addr_seen;  # zone => { "addrLR" => label }
my %zone_label_count; # zone => { label => count }

open(my $tf, '<', $trace_file) or die "Не могу открыть $trace_file: $!\n";
while (<$tf>) {
    chomp;
    if (/^(.+?):\s+(\d{4})\s+(\d{4})([LR])/i) {
        my ($cmd, $zone, $addr, $lr) = ($1, $2, $3, uc($4));
        next if $filter_zone && $zone ne $filter_zone;

        my $addr_oct = oct($addr);
        my $label = ($labels{$zone} && $labels{$zone}->{$addr_oct}) // '???';

        push @entries, {
            zone  => $zone,
            addr  => $addr,
            lr    => $lr,
            cmd   => $cmd,
            label => $label,
            addr_oct => $addr_oct,
        };

        $zone_count{$zone}++;
        $zone_addr_seen{$zone}->{"$addr$lr"} = $label;
        $zone_label_count{$zone}->{$label}++;
    }
}
close($tf);

# ═══ Сортировка ═══
if ($sort_mode eq 'count') {
    @entries = sort { $b->{zone} cmp $a->{zone} || $zone_count{$b->{zone}} <=> $zone_count{$a->{zone}} } @entries;
} elsif ($sort_mode eq 'addr') {
    @entries = sort { $a->{zone} cmp $b->{zone} || $a->{addr_oct} <=> $b->{addr_oct} } @entries;
} else {
    @entries = sort { $a->{zone} cmp $b->{zone} || $a->{addr_oct} <=> $b->{addr_oct} || $a->{lr} cmp $b->{lr} } @entries;
}

# ═══ Вывод ═══
print "\n";
print "═══════════════════════════════════════════════════════\n";
print "  АНАЛИЗ ТРАССЫ: $trace_file\n";
print "═══════════════════════════════════════════════════════\n";
print "  Всего записей: " . scalar(@entries) . "\n\n";

# Сводка по зонам
print "── СВОДКА ПО ЗОНАМ ──\n";
printf "  %-8s %-16s %6s %6s\n", 'ЗОНА', 'МОДУЛЬ', 'СТРОК', 'АДР.';
for my $z (sort keys %zone_count) {
    my $name = $ZONE_MODULE{$z} ? $ZONE_MODULE{$z}->{name} : '???';
    my $naddrs = scalar(keys %{$zone_addr_seen{$z}});
    printf "  %-8s %-16s %6d %6d\n", $z, $name, $zone_count{$z}, $naddrs;
}
print "\n";

exit 0 if $summary_only;

# Частота меток по зонам
print "── ЧАСТОТА МЕТОК ПО ЗОНАМ ──\n";
for my $z (sort keys %zone_label_count) {
    my $name = $ZONE_MODULE{$z} ? $ZONE_MODULE{$z}->{name} : '???';
    print "\n  [$z] $name:\n";
    for my $lbl (sort { $zone_label_count{$z}->{$b} <=> $zone_label_count{$z}->{$a} }
                 keys %{$zone_label_count{$z}}) {
        printf "    %-16s %5d\n", $lbl, $zone_label_count{$z}->{$lbl};
    }
}
print "\n";

exit 0 if $unique_only;

# Полный список
print "── ПОЛНАЯ ТРАССА ──\n";
my $prev_zone = '';
for my $e (@entries) {
    if ($e->{zone} ne $prev_zone) {
        my $name = $ZONE_MODULE{$e->{zone}} ? $ZONE_MODULE{$e->{zone}}->{name} : '???';
        print "\n  === [$e->{zone}] $name ===\n";
        $prev_zone = $e->{zone};
    }
    printf "  %s %s %-16s %s\n", $e->{addr}, $e->{lr}, $e->{label}, $e->{cmd};
}
print "\n";
