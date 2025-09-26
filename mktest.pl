#!/usr/bin/env perl
use utf8;
use feature 'unicode_strings';
use open ':encoding(UTF-8)';
use open ':std', ':encoding(UTF-8)';

# Making a copy of 2053 and writing files named S*-L? 
# to the corresponding locations of the copy

system('rm -f ./2053'); #
system('touch 2053'); # 
#system('cp /usr/local/share/besm6/2053 ~/Yandex.Disk/simh/BESM6/MD');  
system('besmtool dump 2053 --length=01744 --to-file=test2053.dump'); # 2053 from the standard location
#system('rm -f /home/besm-operator/Yandex.Disk/simh/BESM6/MD/2053'); # 
#system('ln -s -f test2053.bin ~/Yandex.Disk/simh/BESM6/MD/2453'); # Preparing a test 2053 in the current directory
system('env BESM6_PATH=. besmtool write 2053 --from-file=test2053.dump'); # Initializing the local copy

while (<S[0-7]*-L[0-7]>) {
    ($zone, $len) = /S(.*)-L(.)/;
    $zone = oct($zone);
    if ($zone < 0400 || $zone >= 01000) {
        print STDERR "Stray file $_\n";
        next;
    }
    # Writing all existing "silver" files to the disk
    system("env BESM6_PATH=. besmtool write 2053 --start=$zone --length=$len --from-file=$_; echo \$?");
}
	system('mv -fv ./2053 ~/Yandex.Disk/simh/BESM6/MD/2453'); # 

