#!/usr/bin/perl

# process candle debug log

use strict;
use warnings;
use Carp;
use Data::Dumper;
use Time::HiRes qw( );

$| = 1;

my @echo = ();
my @send = ();

printf "reading stdin...\n";
my $lcnt = 0;
while(<>){
	my $code = chomp($_);
	$lcnt++;
	push @send, $_  if /SEND/;
	push @echo, $_  if /RCVD/ && /echo/;
}
print "$lcnt lines read\n";

# now match

my $eidx = 0;

for( my $sidx=0; $sidx<= $#send; $sidx++ ){

	my $s = $send[$sidx];
	$s =~ s/SEND //;
	$s =~ s/\"//g;     # assumes no \" char in response
	
	next if $s =~ /\(.*\)/;   # comment has no matching echo
	next if $s =~ /\$G/;      # ignore $G

	printf "%-4d %-30s  ", $sidx, $s;

	# now search for matching echo
	while( $eidx <= $#echo ){
		my $e = $echo[$eidx++];
		chomp($e);
		$e =~ s/RCVD //;
		$e =~ s/echo//;
		$e =~ s/\"//g;

		$e =~ s/\[\: //;
		$e =~ s/\]//;
		#$e =~ s/\s//g;

		next if $e =~ /\$G/;      # ignore $G
		next if $e =~ /^\s+$/;
		
		printf "%s  ", $e  if length($e);

		my $sx = $s;
		$sx =~ s/\s+//g;
		$e  =~ s/\s+//g;

		if( $sx eq $e ){
			printf "\n";
			last;
		}
		else{
			printf "\t\tERROR |%s|%s|\n", $sx, $e;
			last if $e =~ substr( $sx, 0, 2 );
		}
		
		last if $e =~ substr( $s, 0, 2 );        # only match 2 chars, afraid 3rd may be misplaced
	}

}
