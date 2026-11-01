#!/usr/bin/perl -w
# === acpu_analyze.pl ===
# Анализ «подвала» распечатки АЦПУ ОС ДИСПАК
# Использование:
#   perl acpu_analyze.pl <output.txt>              — полный разбор
#   perl acpu_analyze.pl <output.txt> --summary    — краткая сводка
#   perl acpu_analyze.pl <output.txt> --jobs       — только список заданий
#   perl acpu_analyze.pl <output.txt> --errors     — только ошибки
#   perl acpu_analyze.pl <output.txt> --resources  — только ресурсы
#   perl acpu_analyze.pl <output.txt> --devices    — только устройства ВУ

use strict;
use utf8;
binmode(STDOUT, ':utf8');
binmode(STDERR, ':utf8');

my $MODE = 'full';
@ARGV = grep {
    if    ($_ eq '--summary')   { $MODE = 'summary';   0 }
    elsif ($_ eq '--jobs')      { $MODE = 'jobs';      0 }
    elsif ($_ eq '--errors')    { $MODE = 'errors';    0 }
    elsif ($_ eq '--resources') { $MODE = 'resources'; 0 }
    elsif ($_ eq '--devices')   { $MODE = 'devices';   0 }
    else { 1 }
} @ARGV;

my $FILE = shift @ARGV;
unless ($FILE && -f $FILE) {
    die "Использование: $0 <output.txt> [--summary|--jobs|--errors|--resources|--devices]\n";
}

open my $fh, '<:utf8', $FILE or die "Ошибка открытия $FILE: $!\n";
my @lines = <$fh>;
close $fh;
chomp @lines;

my @podvaly;
my $current = undef;

for my $i (0 .. $#lines) {
    my $line = $lines[$i];
    if ($line =~ /^\s*КОНЕЦ\s+ЗАДАЧИ/ || $line =~ /^\s*СБО[,.]/) {
        $current = { start => $i, lines => [] };
        push @podvaly, $current;
    }
    if ($current) {
        push @{$current->{lines}}, $line;
        if ($line =~ /^5{20,}/ || ($line =~ /^\*{10,}/ && scalar @{$current->{lines}} > 5)) {
            $current->{end} = $i;
            $current = undef;
        }
    }
}
if ($current) { $current->{end} = $#lines; }

sub parse_podval {
    my ($pval) = @_;
    my %result;
    my $got_reg = 0;
    my $got_tmh = 0;

    for my $line (@{$pval->{lines}}) {
        if ($line =~ /(\d*ОШ\.[\p{Cyrillic}\d.\x{2191}]+)/) {
            push @{$result{errors}}, $1;
        }
        if ($line =~ /^\s*СБО[,.](.*)/) {
            push @{$result{errors}}, "СБО: $1";
        }
        if ($line =~ /КОНЕЦ\s+ЗАДАЧИ\s+(\+\S+)\s+(\S+)/) {
            $result{exit_code} = $1;
            $result{exit_hex} = $2;
        }
        if ($line =~ /^\s*АП\s+Э\s+РК/) {
            $got_reg = 1;
        }
        if ($got_reg && !exists $result{registers}) {
            my @v = split /\s+/, $line;
            if (scalar @v >= 20) {
                $result{registers} = {
                    АП=>$v[0],Э=>$v[1],РК=>$v[2],
                    И1=>$v[3],И2=>$v[4],И3=>$v[5],И4=>$v[6],
                    И5=>$v[7],И6=>$v[8],И7=>$v[9],
                    И10=>$v[10],И11=>$v[11],И12=>$v[12],И13=>$v[13],
                    И14=>$v[14],И15=>$v[15],И16=>$v[16],И17=>$v[17],
                    КРА=>$v[18],ЗПСЧ=>$v[19],
                };
                $got_reg = 0;
            }
        }
        if ($line =~ /ДАТА\s+РЕШ\.\s+ВЕРСИЯ/) { $got_tmh = 1; }
        if ($got_tmh && !exists $result{timing}) {
            if ($line =~ /^\s*(\d{2}\.\d{2}\.\d{2})\s+(\S+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)/) {
                $result{timing} = {
                    дата=>$1,версия=>$2,сме=>$3,
                    начало_вв=>$4,начало_реш=>$5,конец_реш=>$6,
                    ком_время=>$7,э_реш=>$8,э_вв=>$9,
                };
                $got_tmh = 0;
            }
        }
        if ($line =~ /ЗАКАЗАНО:\s+(.*)/) {
            my @v = split /\s+/, $1;
            $result{ordered} = { озу=>$v[0]//'?',тракты=>$v[1]//'?',время=>$v[2]//'?',кат=>$v[3]//'?' };
        }
        if ($line =~ /ИСПОЛЬ-НО:\s+(.*)/) {
            my @v = split /\s+/, $1;
            $result{used} = {
                озу=>$v[0]//'?',тракты=>$v[1]//'?',время=>$v[2]//'?',кат=>$v[3]//'?',
                ацпу=>$v[4]//'?',ву=>$v[5]//'?',трв=>$v[6]//'?',
                пи=>$v[7]//'?',пл=>$v[8]//'?',терм=>$v[9]//'?',
                мб=>$v[10]//'?',мд=>$v[11]//'?',мл=>$v[12]//'?',
            };
        }
        if ($line =~ /БОБ:(.*)/) { my $b=$1; $b=~s/^\s+//; $result{bob}=$b; }
        if ($line =~ /^\s*(\d+)\s+\*(.+?)\*\s+\S+\s+S=\s*(\d+)\s+(.*)/) {
            $result{job} = { flag=>$1,name=>$2,s=>$3,detail=>$4 };
        } elsif ($line =~ /^\s*(\d+)\s+\*(.+?)\*\s+S=\s*(\d+)\s+(.*)/) {
            $result{job} = { flag=>$1,name=>$2,s=>$3,detail=>$4 };
        }
        if ($line =~ /\*АЦПУ-(\d+)\s+ЭВМ-\d+\s+(\S+)\*/) {
            $result{acpu} = { num=>$1,time=>$2 };
        }
        if ($line =~ /УСТРОЙСТВА\s+ВВОДА-ВЫВОДА\s*:\s*(.*)/) { $result{devices}=$1; }
        if ($line =~ /БУФЕР\s+ВВОДА-ВЫВОДА\s*:\s*(.*)/) { $result{buffer}=$1; }
        if ($line =~ /СВОБОДНЫЕ\s+РЕСУРСЫ\s*:\s*(.*)/) { $result{free_res}=$1; }
        if ($line =~ /РЕЖИМ\s+РАБОТЫ\s*:\s*(.*)/) { $result{mode}=$1; }
        if ($line =~ /(\d{2})\s+(\d{4})\s+(ОБЩ|СИС|ИНД|АРХ)\s+(СВОБОДЕН|СВОБОДНА|ЗАНЯТ|В\s+РЕШЕНИИ)(?:\s+(..))?/) {
            push @{$result{disks}}, { num=>$1,vol=>$2,type=>$3,st=>$4,defined $5?(flag=>$5):() };
        }
    }
    return \%result;
}

my @parsed = map { parse_podval($_) } @podvaly;

if ($MODE eq 'summary' || $MODE eq 'full') {
    print "╔══════════════════════════════════════════════════════════════╗\n";
    print "║  АНАЛИЗ РАСПЕЧАТКИ АЦПУ: $FILE\n";
    print "╚══════════════════════════════════════════════════════════════╝\n\n";
    print "  Всего подвалов (заданий): " . scalar(@parsed) . "\n\n";
}

if ($MODE eq 'full' || $MODE eq 'errors') {
    my @errs;
    for my $i (0 .. $#parsed) {
        next unless $parsed[$i]->{errors};
        push @errs, "  [" . ($i+1) . "] $_" for @{$parsed[$i]->{errors}};
    }
    if (@errs) { print "── ОШИБКИ ──\n" . join("\n",@errs) . "\n\n"; }
    elsif ($MODE eq 'errors') { print "  Ошибок нет.\n\n"; }
}

if ($MODE eq 'full' || $MODE eq 'jobs') {
    for my $i (0 .. $#parsed) {
        my $p = $parsed[$i]; my $n = $i+1;
        print "── ЗАДАНИЕ $n ──\n";
        if ($p->{job}) {
            my $j = $p->{job};
            printf "  Имя: %-20s S=%s\n", $j->{name}, $j->{s};
            if ($j->{detail} && $j->{detail} =~ /(\S+)\s+(\S+)\s+(\S+)\s+(\S+)/) {
                printf "  Время: %-15s Код: %s\n", $1, $4;
            }
        }
        printf "  Код завершения: %s (%s)\n", $p->{exit_code}//'?',$p->{exit_hex}//'?' if $p->{exit_code};
        printf "  АЦПУ-%s  %s\n", $p->{acpu}{num}, $p->{acpu}{time} if $p->{acpu};
        if ($p->{timing}) {
            my $t=$p->{timing};
            printf "  Дата: %s  Версия: %s\n", $t->{дата},$t->{версия};
            printf "  Начало вв: %s  Начало реш: %s  Конец: %s\n", $t->{начало_вв},$t->{начало_реш},$t->{конец_реш};
            printf "  Комм.время: %s  Э.реш: %s\n", $t->{ком_время},$t->{э_реш};
        }
        print "\n";
    }
}

if ($MODE eq 'full' || $MODE eq 'resources') {
    if (grep { $_->{ordered} || $_->{used} } @parsed) {
        print "── РЕСУРСЫ ──\n";
        printf "  %-5s %-8s %-8s %-12s\n", "#","ОЗУ","Тракты","Время";
        for my $i (0 .. $#parsed) {
            my $p=$parsed[$i]; my $n=$i+1;
            if ($p->{ordered}) { my $r=$p->{ordered}; printf "  %-5s %-8s %-8s %-12s ← заказ\n",$n,$r->{озу},$r->{тракты},$r->{время}; }
            if ($p->{used}) { my $r=$p->{used}; printf "  %-5s %-8s %-8s %-12s ← факт\n",$n,$r->{озу},$r->{тракты},$r->{время};
                if ($r->{ацпу} ne '?') { printf "  %-5s ВУ=%s ТРВ=%s ПИ=%s ПЛ=%s ТЕРМ=%s МБ=%s МД=%s\n",'',$r->{ву},$r->{трв},$r->{пи},$r->{пл},$r->{терм},$r->{мб},$r->{мд}; }
            }
        }
        print "\n";
    }
}

if ($MODE eq 'full' || $MODE eq 'devices') {
    my @d;
    for my $i (0 .. $#parsed) { push @d, @{$parsed[$i]->{disks}} if $parsed[$i]->{disks}; }
    if (@d) {
        print "── ДИСКОВОДЫ ──\n";
        printf "  %-4s %-6s %-6s %-16s\n","НУ","ТОМ","ТИП","СТАТУС";
        for my $dd (sort { $a->{num}<=>$b->{num} } @d) {
            my $f=defined $dd->{flag}?" $dd->{flag}":'';
            printf "  %-4s %-6s %-6s %-16s%s\n",$dd->{num},$dd->{vol},$dd->{type},$dd->{st},$f;
        }
        print "\n";
    }
    for my $i (0 .. $#parsed) {
        my $p=$parsed[$i];
        if ($p->{devices}||$p->{buffer}||$p->{mode}) {
            print "── ВУ задание ".($i+1)." ──\n";
            print "  Режим: $p->{mode}\n" if $p->{mode};
            print "  Буфер: $p->{buffer}\n" if $p->{buffer};
            print "  Устр-ва: $p->{devices}\n" if $p->{devices};
            print "  Свободные: $p->{free_res}\n" if $p->{free_res};
            print "\n";
        }
    }
}

if ($MODE eq 'full') {
    if (grep { $_->{registers} } @parsed) {
        print "── РЕГИСТРЫ ──\n";
        for my $i (0 .. $#parsed) {
            next unless $parsed[$i]->{registers};
            my $r=$parsed[$i]->{registers};
            printf "  [%d] АП=%s Э=%s РК=%s КРА=%s ЗПСЧ=%s\n",$i+1,$r->{АП},$r->{Э},$r->{РК},$r->{КРА},$r->{ЗПСЧ};
            printf "      И1-7: %s %s %s %s %s %s %s\n",map { $r->{$_} } qw(И1 И2 И3 И4 И5 И6 И7);
            printf "      И10-17: %s %s %s %s %s %s %s %s\n",map { $r->{$_} } qw(И10 И11 И12 И13 И14 И15 И16 И17);
        }
        print "\n";
    }
}

print "Готово. Подвалов: " . scalar(@parsed) . "\n" if $MODE eq 'full';
