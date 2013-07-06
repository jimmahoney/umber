#!/bin/env perl
############
# returns a random .png image
######################
use strict;
use warnings;
use GD;

# Usage: r($n) returns random from 0..($n-1)
sub rr {
  my $n = shift;
  return int($n*rand());
}

my $xsize = 1300;
my $ysize = 1000;
my $ncolors = 19;
my $nspots = 3e4;
my $spotsize_max = 10;
my $spotsize_min = 1;
my @darken = (8, 8, 8);
my @base = (220, 210, 195);
my $image = GD::Image->new($xsize,$ysize);

# allocate some colors.  First allocated is background.
my $background = $image->colorAllocate(@base);
my @colors;
for (1..$ncolors){
  push @colors, $image->colorAllocate(map {$base[$_] - rr($darken[$_])} 0..2);
}

# draw some spots
my $n=0;
while ($n<$nspots){
  my $size=$spotsize_min + rr($spotsize_max-$spotsize_min);
  my $x = rr($xsize);
  my $y = rr($ysize);
  my $which = rr(@colors);
  my $color = $colors[rr(scalar @colors)];
  $image->filledEllipse($x,$y,$size,$size,$color);
  $n++;
}

# output the image
print "Content-type: image/png\n\n" if caller();  # if from apache
print $image->png;

# -------------------------------------------------


#our $white    = $im->colorAllocate(255,255,255);
#our $black    = $im->colorAllocate(  0,  0,  0);     
#our $grey     = $im->colorAllocate(172,172,172);
#our $darkBlue = $im->colorAllocate(  0,  0,128);
