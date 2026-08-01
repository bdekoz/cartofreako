#! /usr/bin/perl -w
#
# 2012-03-15 This is program "MegamapMaker-prep9" by Mary Jo Graça
#
# Licensed under Creative Commons for non-commercial use, with attribution
# to Mary Jo Graça and Gene Keyes. May be modified or reproduced or 
# redistributed. For commercial applications, contact gene.keyes at gmail.
#

# ADDITIONAL NOTES BY GENE KEYES, 2013-11-28
#
# As noted elsewhere, Gene Keyes did the overall design and calculations for the
# Cahill-Keyes Multi-scale Megamap, and Mary Jo Graça wrote these marvelous Perl
# (and Apache OpenOffice Draw) programs to produce a full-scale realization of the
# Cahill-Keyes, starting at 1/1 million, or smaller, whether printed, or on a monitor.
# (See www.genekeyes.com for many examples, and 
# http://www.genekeyes.com/MEGAMAP-BETA-2/Beta-2-preview.html for the Beta-2 in particular.)

# This Perl script prepares the Beta-2 version of the Megamap, which, unlike Beta-1,
# includes a re-united Antarctica; and extension tabs for the Kamchatka peninsula
# of Russia's Far East, Iceland, Greenland, and other split islands. 

# It also includes a method of rotating the octants so that they can be joined in any combination
# of layouts, including the Cahill-Keyes "standard" M-profile; or Cahill's original
# Butterfly; or Atlantic or Pacific edge joints; etc. The so-called "area codes"
# in the program specify which edges go together. 

# As of now, the rotational component has been
# tested with only the octant perimeters (and some sketchy continental outlines),
# because it takes many many hours to run a full map with coastlines and graticule.
# However, the entire Beta-2 Cahill-Keyes Multi-scale Megamap has already been 
# executed with the rest of the program. See links above for diagrams and examples,
# including a 45 MB C-K map pdf at 1/1 million (as well as some preliminary printouts of the 
# rotational aspect).

# For the original Beta-1 scripting and specifications, see
# http://www.genekeyes.com/CKOG-OOo/1-CKOG-principles.html
# and its following six pages.

# Mary Jo has always been reluctant to upload these programs in their somewhat rough
# and inefficient state; but after waiting 18 months for her to even start a "perfected"
# version, I take responsibility for presenting this script "as is", with the hope that others
# might find it useful, and/or improve upon it. Most of it is Greek to me, but it can certainly
# output some amazingly detailed Cahill-Keyes world maps or segments thereof, plus the 
# all-important one-degree graticule I've been aiming at since 1975. --GK


# ADDITIONAL NOTES BY MARY JO GRAÇA, 2013-11-28
#
# File "MegamapMaker-prep9.pl" is a plain text file -- the Perl program; 
# the ".pl" extension means Perl script.
#
# The references to "Duncan" in the script are for a collaborator in Australia, Duncan Webb, 
# who was working on a wall-map version.
#
# MJ coordinates, are template coordinates. MJ stands for Mary Jo Graça. Gene Keyes had wanted 
# one set of x and y axes; Mary Jo tried it and found it too cumbersome, and decided on a different set, 
# and to use only half an octant instead of a whole one. Mary Jo being the programmer, that is what ended 
# up being used. Since this was being done just between the two of us, it didn't matter if "MJ" showed up 
# in the program, and we didn't care to give them better names.
#
# The coordinates calculated in the subs are based on a set of axes with x positive to the right and y positive 
# upwards; to plot on a screen, one may need to have the y axis positive downwards, which must be adjusted 
# in the "Block".
#
# The program uses the distance from point M to point G as 10,000 -- see Figure 3: 
# http://www.genekeyes.com/CKOG-OOo/7-CKOG-illus-&-coastline.html (plus the whole set of 6
# construction diagrams there.)
#
# The final map coordinates have point (0,0) at the very centre of a Megamap layout; the M-shape Megamap 
# is 40,000 units wide (from -20,000 to +20,000) and less than 20,000 high. For the Butterfly layout, 
# the y axis is at the centre, but I think (it has been over one year since I did wrote this) that 
# the x axis passes through the centre of rotation, close to the top of the map if around the North Pole, 
# and close to the bottom of the map if around the South Pole. The Butterfly layout is less than 40,000 wide 
# and more than 20,000 high.
#
# The guts of the program, that is, what does all the coordinate conversions, start at line which has 
# "S U B R O U T I N E S", 
# and goes on to the end.
#
# The first many pages are what I call "Blocks"; they just call the subroutines to do specific things 
# I needed at the time, and they can be deleted or modified to do whatever one chooses: read one pair 
# longitude-latitude and convert it to a given projection; read a file of longitudes-latitudes and convert 
# them to a given projection; calculate coordinates to plot meridians and parallels...
# 
# In the Blocks, where I have lines such as:
# printf FILEXY ("%.0f,%.0f\n", $Xs[$i] * 100, -$Ys[$i] * 100);
# The multiplying by 100 and making Ys negative have to do with the program we used to plot, which 
# required coordinates in hundredths of a millimeter and positive y coordinates downwards.
#
# Check the Blocks for how the subs are called, and which checks might be necessary along the way.
#
# The way the program needs to work is:
#
# 0- Input data must be separated by octant. Because the map is not continuous, and points on octant 
# boundaries occur in two different places, the program must know for which octant (actually, for which
# "area-code" -- see below) the data are meant.
# 
# 1- Calculate the constant values, which will be used over and over, by calling sub Preliminary
# 
# 2- Read in real world (globe, Earth) longitude-latitude pairs and convert to half-template-octant 
# meridian-parallel coordinates. The idea is that the whole world is divided into 8 octants or 16 
# half-octants, but that calculations only need to be done on one single half-octant. For this, it 
# needs to know from which octant the data is; this is in order to place a border point on the east 
# or west side of the split between octants, to prevent later having points connect across the no-map area 
# between octants. -- sub CheckOctant to make sure data is indeed for the correct octant; sub LLtoMP to convert
#
# 3- Half-template-octant meridian-parallel coordinates are converted to template x-y coordinates -- sub MPtoXY
#
# 4- Transform template x-y coordinates to map x-y coordinates in the desired layout, and print them out -- 
# Can choose to use sub MJtoMM or sub MJtoMap for the conversion (see farther down about these).
#
# - - -

# The octants are numbered as follows, in any layout:
# 1 - North Pacific with West of North America: North Pole to Equator, 160 E to 110 W
# 2 - Most of North America and North Atlantic: North Pole to Equator, 110 W to 20 W
# 3- Europe, Middle East and most of Africa: North Pole to Equator, 20 W to 70 E
# 4- Most of Asia: North Pole to Equator, 70E to 160E
# 5- Australia: South Pole to Equator, 70E to 160 E
# 6- Most of South Pacific with New Zealand: South Pole to Equator, 160 E to 110 W
# 7- Most of South America: South Pole to Equator, 110 W to 20 W
# 8- South Africa: South Pole to Equator, 20 W to 70 E

# The "area code" to convert to. Possible area codes are:
# 1 2 3 4 5 6 7 8
# 1we 1wv 1wt 1wm 1wp 1pv 1ep 1et 1ev 1ee
# 2we 2wv 2wt 2wp 2pv 2ep 2em 2et 2ev 2ee
# 3we 3wv 3wt 3wm 3wp 3pv 3ep 3et 3ev 3ee
# 4we 4wv 4wt 4wp 4pv 4ep 4em 4et 4ev 4ee
# 5we 5wv 5wt 5wm 5wp 5pv 5ep 5em 5et 5ev 5ee
# 6we 6wv 6wt 6wm 6wp 6pv 6ep 6em 6et 6ev 6ee
# 7we 7wv 7wt 7wm 7wp 7pv 7ep 7et 7ev 7ee
# 8we 8wv 8wt 8wp 8pv 8ep 8em 8et 8ev 8ee
# 1em 2wm 3em 4wm 7em 8wm

# The numbers 1 to 8 are the octants in their proper positions.

# The other codes are for octants rotated to be adjacent to others, as to join Antarctica or join Kamchatka 
# to the rest of Russia. The number is the octant adjacent to which one wants to plot. The letters mean:

# - we/we= at west/east side of equator; e.g. 1we = west of octant 6 placed adjacent to segment EF of west oct. 1
# - wv/ev= across from west/east equatorial vertex (point E); e.g.1wv = oct. 5 touching point E of oct. 1
# - wt/et= at west/east tropical segment; e.g. 1et = oct. 2 adjacent to segment DE of oct. 1 (instead of adjacent 
# to segment BD, its normal position)
# - wm/em = west/east middle segment; e.g. 1em = oct. 2 in its usual position; 2em = oct. 3 adjacent to segment BD of oct. 2
# - wp/ep = west/east polar segment; e.g. 2ep = oct. 3 adjacent to seg. AB of oct. 2, to join Greenland
# - pv = across from polar vertex (point A); e.g. 7pv= oct. 5 placed touching pole of oct. 7

# - - - -

# You don't have to look at OpenOffice.org code. The Antarctica x-y coordinates are prepared in the program 
# MegamapMaker-prep9.pl. It is made by converting:
# - data from octant 6 using area code 7wp
# - data from octant 7 using area code 7
# - data from octant 8 using area code 7ep
# - data from octant 5 using area code 7vp

# Check block 1 and Sub MJtoMM. The part of interest is the last few lines of this sub, just before Sub MJtoMap (
# the rest is just setting up the arrays to take into consideration all the area codes):
    # # Now for the actual calculations
    # if ($North[$Area]) {$xUse = $x} else {$xUse = 20000 - $x}
    # $xUse = $xUse - $xRt[$Area];
    # $yUse = $y - $yRt[$Area];
    # $xNew =$xUse * $cos[$Area] + $yUse * $sin[$Area] + $xT[$Area];
    # $yNew = -$xUse * $sin[$Area] + $yUse * $cos[$Area] + $yT[$Area];
  # }
  # return ($xNew, $yNew);

# By the way, Sub MJtoMap, along with Sub EpiArea does the same thing as Sub MJtoMM, except that it allows 
# for more layouts. I prefer MJtoMap, in particular the way the arrays necessary for the calculations are prepared; 
# it makes it easier to understand where the numbers come from and what they mean. However, it requires the added 
# information (parameters) of whether to use M (Megamap) or B (Butterfly) layout and which octant number lies east 
# and adjacent to the center line. The layouts are of two kinds; Megamap or Butterfly, and each layout can start with 
# any of the octants, instead of always having octants 1 and 5 on the left. Look at the two silhouette maps on Gene's 
# page http://www.genekeyes.com/ for what is meant by Megamap [or M-shape] and Butterfly layouts.

# - - - -
# In answer to a query:
# We do not have the inverse transformation from x/y to lon/lat, although I would like to have one.

# It would require quite a few if-than-elses; I believe that for points on torrid segments it will 
# need some trial-and-error to determine the meridian -- something like a "bubble sort" until the 
# difference is small enough; off the top of my head, in that region I think one has to solve an equation 
# with "atan(....x...)" on one side and "x/3" on the other side, where x is the unknown angle for the meridian.


# BLOCK (1) : read file of longitude,latitude coordinates and convert to x,y coordinates
$Skip[1] = "YES";
# BLOCK (2): prepare graticule file of 15°, with joined Antarctica, for Duncan
$Skip[2] = "YES";
# BLOCK (3): prepare graticule file of 5°, with joined Antarctica, for Duncan
$Skip[3] = "YES";
# BLOCK (4): Prepare octant boundaries, with joined Antarctica, for Duncan
$Skip[4] = "YES";
# BLOCK (5): prepare graticule for whole megamap, with joined Antarctica
$Skip[5] = "YES";
# BLOCK (6): Prepare major circles of latitude, with joined Antarctica, for Duncan
$Skip[6] = "YES";
# BLOCK (7): Prepare partial graticule, for an extension
$Skip[7] = "YES";
# BLOCK (8):
$Skip[8] = "YES";
# BLOCK (9): Testing MJtoMap
$Skip[9] = "YES";

print "Type:\n- 1 to convert MAPGEN file (longitude, latitude) to Cahill-Keyes x,y coordinates;";
print "\n- 2 to prepare graticule file of 15 degrees, with joined Antarctica, for Duncan;";
print "\n- 3 to prepare graticule file of 5 degrees, with joined Antarctica, for Duncan;";
print "\n- 4 to prepare octant boundaries, with joined Antarctica, for Duncan";
print "\n- 5 to prepare file \"Graticule.txt\" for whole Megamap with joined Antarctica;";
print "\n- 6 to prepare major circles of latitude, with joined Antarctica, for Duncan;";
print "\n- 7 to prepare partial graticule, for an extension;";
print "\n- 8 to ;";
print "\n- 9 to test sub MJtoMap;";
print "\n- or anything else to do nothing.\n";
$Answer = <STDIN>;
chomp ($Answer);
if (($Answer =~ /[1-9]/ && length($Answer) == 1) ) {
 $Skip[$Answer] = "";
 use Math::Trig;
 # Calculate values that should be global, to minimize repeated calculations
 # ($sin60, $cos60, $MGcos30, @Prelims) = Preliminary();
 # Put ($sin60, $cos60, $MGcos30) into @Conv, and remaining variables into @Prelims
 (@Conv[0..2], @Prelims) = Preliminary();
 push(@Conv, @Prelims[0, 8, 9]);  # Add $xA, $xE and $yE to @Conv; @Prelims unchanged
}

# BLOCK (1) : read file of longitude,latitude coordinates and convert to x,y coordinates

unless ($Skip[1]) {  # Option to skip making x,y file of Coastal Data
  print "For which area code do you want to prepare data?\n";
  $Area = <STDIN>;
  chomp ($Area);
  ($WantedOctant, $flag) = CheckArea($Area);
  if ($flag) {die "Terminating.\n";}  # If area was not recognized, terminate program.
  print "Type in name of MAPGEN file with coastal data\n";
  $FileIn = <STDIN>;
  chomp ($FileIn);
  print "Type in name for output file to receive x,y coordinates.\n";
  $FileOut = <STDIN>;
  chomp ($FileOut);
  # *** NOTE: Adding the path for Gene's directory with coastal data.
  # *** THIS MUST BE CHANGED OR COMMENTED OUT TO RUN ON ANOTHER COMPUTER
#   $FileIn = "/media/D:/My Documents/CKOG/COASTLINE-DATA-2/" . $FileIn;
#   $FileOut = "/media/D:/My Documents/CKOG/COASTLINE-DATA-2/" . $FileOut;
  # Output will be a plain text file with the following for each segment:
  # line with "L,0" (without quotes), followed by lines of x,y (comma included) values.
  #
  # Read some Coastal Data, convert to M-map coordinates, and write to output file.
  # File read is a zipped or unzipped file of MAPGEN data format: two columns ASCII flat
  # file with: longitude tab latitude; at the start of each segment there is a line containing
  # only "# -b".
  # Variable $Map can be set to "M" to output coordinates in M-map system, or to
  # any other value, to output coordinates in Gene's one-octant system.
  $Map = "M";
  # Set up a few variables
  $maxX=-99999;  $maxY=-99999;  $minX=999999;  $minY=999999;
  $oldLong = 99999;  $oldLat = 99999;
  # Start output file
  $FileOut2 = "> " . $FileOut;
  # Open output file to receive x,y coordinates
  open (FILEXY, $FileOut2) || die "Sorry, I couldn't open output file, \"$FileOut\".\n";
  # Open coastal data file, taking into account whether or not it is compressed as .zip
  if ( $FileIn =~ /.\.zip$/i || $FileIn =~ /.\.gz$/i) {
   # If file ends in a letter plus a period plus "zip" or "ZIP" or gz
   $FileIn2 = "zcat \"" . $FileIn . "\" | ";  # Compressed file
  } else {
   $FileIn2 = $FileIn;  # normal, uncompressed file
  }
  open (DATA, $FileIn2) || die "Sorry, I couldn't open input file, \"$FileIn2\".\n";
  $nData = 0;
  $nWrite = 0;
  $nHead = 0;
  $flag2 = 0;
  print "This might take awhile. I'll let you know every 1,000 lines that I read.\n\n";
  while (<DATA>) {
    $Line = $_ ;
    chomp($Line);  # Remove new-line character from end of line of data read
    if ($Line =~ /\r$/ ) {
      chop($Line);  # removing a return character, if there is one
    }
    $nData ++;
    if ($nData % 1000 == 0) { print "Read $nData lines of land data so far.\n"; }
    if (index($Line,'#') < 0) {  # Process line with longitude, latitude
      ($Long,$Lat) = split(/\t/,$Line);
     if (defined($Long) && defined($Lat)) {  # Do only if there are two values on this line
      if ( ! ($Long == $oldLong && $Lat == $oldLat) ) {
        # If this point is a repeat of the previous point on this segment, this section is
        # not run, and this point is neither converted nor included in the output file.
        $oldLong = $Long;  $oldLat = $Lat;
        # COORDINATE CONVERSION
        # Convert real longitude, latitude to template half-octant meridian and parallel
        ($m, $p, $Sign, $flag) = CheckOctant ($Long, $Lat, $WantedOctant);
        if ($flag) {  # If flag is true, point is not in correct octant; terminate program
#          $ToWrite = "Error: Point $Long, $Lat would be meridian " . $m * $Sign;
#          $ToWrite .= ", parallel $p in octant $flag. To be in area code "; 
#          $ToWrite .= "\"$Area\", it needs to be in octant number $WantedOctant.\n";
#          $ToWrite .= "Terminating.\n";
#          close (FILEXY);
#          close (DATA);
#          die $ToWrite;
          $ToWrite = "Error at line $nData of input file:\n";
          $ToWrite .= "Point $Long, $Lat would be meridian " . $m * $Sign;
          $ToWrite .= ", parallel $p in octant $flag. To be in area code "; 
          $ToWrite .= "\"$Area\", it needs to be in octant number $WantedOctant.\n";
          $ToWrite .= "Type y to accept octant $flag and n to terminate.\n";
          print $ToWrite;
          $Answer = <STDIN>;
          chomp ($Answer);
          if ($Answer eq "y") {
            $flag2 = 1;
          } else {
            close (FILEXY);
            close (DATA);
            die "Terminating.\n";
          }
        }
        # Convert template meridian, parallel to template half-octant x, y coordinates
        ($x, $y) = MPtoXY ($m, $p, @Prelims);
        # Convert template x, y coordinates to M-map or G's x and y coordinates.
        # Variable $Map was set previously in this block.
        if ($Map eq "M") { # M-map coordinates
          if ($flag2) { # Point on a different octant
            ($xNew, $yNew) = MJtoMM ($x, $Sign*$y, $flag, $sin60, $cos60);
            $flag2 = 0;
          } else { # point where it should be
            ($xNew, $yNew) = MJtoMM ($x, $Sign*$y, $Area, $sin60, $cos60);
          }
        } else { # G's single octant coordinates
          ($xNew, $yNew) = MJtoMM ($x, $Sign*$y, "G", $sin60, $cos60);
        }
        # Keep track of maximum and minimum values
        if ($xNew < $minX) {$minX = $xNew;}
        if ($xNew > $maxX) {$maxX = $xNew;}
        if ($yNew < $minY) {$minY = $yNew;}
        if ($yNew > $maxY) {$maxY = $yNew;}
        # If this segment has already 1000 points, write it and start a new segment,
        # repeating the last point; new segment will have at least 2 points.
        if (@Xs == 999) {
          $nHead ++;
          $nPoints = @Xs - 1;
          print FILEXY ("L,0\n" );
          foreach $i (0 .. $nPoints) {
            # Values are multiplied by 100 to convert to 100ths of mm, and y-value is made
            # negative because OOo Draw uses y positive downwards.
            printf FILEXY ("%.0f,%.0f\n", $Xs[$i] * 100, -$Ys[$i] * 100);
          }
          @Xs = ($Xs[$nPoints]);  # Delete all values from arrays except the last one
          @Ys = ($Ys[$nPoints]);
          # Add one to the number of points, for the point that was written in this segment,
          # and will be rewritten on the next
          $nWrite ++;
        }
        # Make arrays of points for this segment to be written to output file
        push (@Xs,$xNew);
        push (@Ys,$yNew);
        $nWrite ++;
      }  # End of skipping if the last point read was the same as the previous one
     }  # End of doing if there really was data on the line, or skipping if there wasn't
    } elsif (defined(@Xs) ) {  # End of segment; write only if data points were read
      # Write this segment of coastline with arrays @Xs and @Ys
      $nHead ++;
      $nPoints = @Xs - 1;
      print FILEXY ("L,0\n" );
      foreach $i (0 .. $nPoints) {
        # Values are multiplied by 100 to convert to 100ths of mm, and y-value is made
        # negative because OOo Draw uses y positive downwards.
        printf FILEXY ("%.0f,%.0f\n", $Xs[$i] * 100, -$Ys[$i] * 100);
      }

      @Xs = ();  @Ys = ();  # Empty arrays, ready for next segment
      $oldLong = 99999;  $oldLat = 99999;  # Reset previous values to impossible values
    }
  }
  close (DATA);
  if ($Line ne "\# -b") { # Draw last segment, if it hasn't been drawn
    # Write this segment of coastline with arrays @Xs and @Ys
    $nHead ++;
    $nPoints = @Xs - 1;
    print FILEXY ("L,0\n" );
    foreach $i (0 .. $nPoints) {
      # Values are multiplied by 100 to convert to 100ths of mm, and y-value is made
      # negative because OOo Draw uses y positive downwards.
      printf FILEXY ("%.0f,%.0f\n", $Xs[$i] * 100, -$Ys[$i] * 100);
    }
  }
  close (FILEXY);
  $nWrite = $nWrite + $nHead;
  print "Read a total of $nData lines. Wrote $nWrite lines ($nHead segments) to file"; 
  print "\"$FileOut\". \n", $minX, ' <= x <= ',$maxX," and ",$minY, ' <= y <= ', $maxY, "\n";

}  # End of skipping making x,y file of Coastal Data

# BLOCK (2): prepare graticule file of 15°, with joined Antarctica, for Duncan
unless ($Skip[2]) { # Option to skip
  ($xA, $yA, $xB, $yB, $xC, $yC, $xD, $yD, $xE, $yE, $xF, $yF, $xG, $yG,
      $xM, $yM, $xT, $yT, $AG, $AB, $BD, $GF, $BDE, $GFE, $R, $DeltaMEq) = @Prelims;
  # Open file, write out meridians and parallels
  open (MACRO, ">Graticule15.txt");  # Name for output file with OOo macro
  # Calculate all whole degree points on template half-octant
  foreach $m (0 .. 45) {
    foreach $p (1 .. 89) {
      ($xP[$m][$p], $yP[$m][$p]) = MPtoXY ($m, $p, @Prelims);
    }
    # Calculate meridian joints. Array's index is: 0 = polar start (point A);
    # 1 = frigid joint; 2 = torrid joint; 3 = equator. Meridain 0° has no joints; it goes from
    # A to G.
    if ($m > 0 && ($m % 15 == 0) ) {
      ($xJ[$m][3], $yJ[$m][3], $xJ[$m][2], $yJ[$m][2], $xJ[$m][1], $yJ[$m][1], $Lt, $Lm) =
        Joints ($m, $xA, $xE, $yE, $xF, $yF, $xG, $AB, $GF, $DeltaMEq);
      # Start point of meridians
      ($xJ[$m][0], $yJ[$m][0]) = ($xA, $yA);
    }
  } # Now I have all needed x,y points
  # Prepare graticule for whole octants 1 to 7. Octant 8 is partial, and will be done later
  foreach $octant (1 .. 7) {
    # Prepare meridians, starting with 0°, which is a straight line from point A to point G.
    print "Doing octant $octant.\n";
    $Major = "L,2\n";
    ($xNew, $yNew) = MJtoMM ($xA, $yA, $octant, $sin60, $cos60);
    $Major .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    ($xNew, $yNew) = MJtoMM ($xG, $yG, $octant, $sin60, $cos60);
    $Major .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);    
    # Other than meridian 0°, do both positive and negative meridians (i.e. 15° and -15°).
    # Meridian 45° not done because it would be covered by the octant's boundary.
    foreach $m (15, 30 ) {
      $temp1 = ""; $temp2 = "";
      # Do the meridian in the positive half-octant
      foreach $i (0..3) {
        ($xNew, $yNew) = MJtoMM ($xJ[$m][$i], $yJ[$m][$i], $octant, $sin60, $cos60);
        $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      # Do the meridian in the negative half-octant
      foreach $i (0..3) {
        ($xNew, $yNew) = MJtoMM ($xJ[$m][$i], -$yJ[$m][$i], $octant, $sin60, $cos60);
        $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      $Major .= "L,2\n" . $temp1 . "L,2\n" . $temp2
    } # End of meridians
    # Prepare parallels; parallel 0° not done because it is on the octant's boundary.
    foreach $p (15, 30, 45, 60, 75) {  # Convert to wanted octant and write out values
      $temp1 = ""; $temp2 = "";
      # Positive half-octant
      foreach $m (0..45) {
        ($xNew, $yNew) = MJtoMM ($xP[$m][$p], $yP[$m][$p], $octant, $sin60, $cos60);
        $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      # Negative half-octant
      foreach $m (0..45) {
        ($xNew, $yNew) = MJtoMM ($xP[$m][$p], -$yP[$m][$p], $octant, $sin60, $cos60);
        $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      $Major .= "L,2\n" . $temp1 . "L,2\n" . $temp2
    }  # End of parallels
    # Write out meridians and parallels for this octant
    print MACRO $Major;
  } # End of graticule for octants 1 to 7
  # Now do octant 8 only from equator to 65°; part with Antarctica not done
  $octant = 8;
  print "Doing octant $octant from equator to 65°.\n";
  $Major = "L,2\n";
  ($xNew, $yNew) = MJtoMM ($xP[0][65], $yP[0][65], $octant, $sin60, $cos60);
  $Major .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
  ($xNew, $yNew) = MJtoMM ($xG, $yG, $octant, $sin60, $cos60);
  $Major .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);    
  # Other than meridian 0°, do both positive and negative meridians (i.e. 15° and -15°).
  # Meridian 45° not done because it would be covered by the octant's boundary.
  foreach $m (15, 30) {
    $temp1 = ""; $temp2 = "";
    # Do the meridian in the positive half-octant: parallel 65, torrid joint, equator;
    # start point ([0]) and frigid joint ([1]) not used because they are beyond parallel 65°.
    ($xNew, $yNew) = MJtoMM ($xP[$m][65], $yP[$m][65], $octant, $sin60, $cos60);
    $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    ($xNew, $yNew) = MJtoMM ($xJ[$m][2], $yJ[$m][2], $octant, $sin60, $cos60);
    $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    ($xNew, $yNew) = MJtoMM ($xJ[$m][3], $yJ[$m][3], $octant, $sin60, $cos60);
    $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    # Do the meridian in the negative half-octant
    ($xNew, $yNew) = MJtoMM ($xP[$m][65], -$yP[$m][65], $octant, $sin60, $cos60);
    $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    ($xNew, $yNew) = MJtoMM ($xJ[$m][2], -$yJ[$m][2], $octant, $sin60, $cos60);
    $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    ($xNew, $yNew) = MJtoMM ($xJ[$m][3], -$yJ[$m][3], $octant, $sin60, $cos60);
    $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    $Major .= "L,2\n" . $temp1 . "L,2\n" . $temp2
  } # End of meridians
  # Prepare parallels; parallel 0° not done because it is on the octant's boundary.
  foreach $p (15, 30, 45, 60) {  # Convert to wanted octant and write out values
    $temp1 = ""; $temp2 = "";
    # Positive half-octant
    foreach $m (0..45) {
      ($xNew, $yNew) = MJtoMM ($xP[$m][$p], $yP[$m][$p], $octant, $sin60, $cos60);
      $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    }
    # Negative half-octant
    foreach $m (0..45) {
      ($xNew, $yNew) = MJtoMM ($xP[$m][$p], -$yP[$m][$p], $octant, $sin60, $cos60);
      $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    }
    $Major .= "L,2\n" . $temp1 . "L,2\n" . $temp2
  }  # End of parallels
  # Write out meridians and parallels for this octant
  print MACRO $Major;
  # End of partial graticule for octant 8
  # Now do graticule for Antarctica sections of octants 5, 6, 8, rotated to join with
  # whole-octant 7; they are, respectively, areas "7pv", "7wp" and "7ep".
  foreach $octant ("7pv", "7wp", "7ep") {
    # Prepare meridians, starting with 0°, which is a straight line from point A to parallel 65°.
    print "Doing Antarctica section $octant.\n";
    $Major = "L,2\n";
    ($xNew, $yNew) = MJtoMM ($xA, $yA, $octant, $sin60, $cos60);
    $Major .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    ($xNew, $yNew) = MJtoMM ($xP[0][65], $yP[0][65], $octant, $sin60, $cos60);
    $Major .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    # Other than meridian 0°, do both positive and negative meridians (i.e. 15° and -15°).
    # Meridian 45° not done because it would be covered by the octant's boundary.
    foreach $m (15, 30) {
      $temp1 = ""; $temp2 = "";
      # Do the meridian in the positive half-octant: start point A to frigid joint ([1]),
      # to parallel 65°.
      ($xNew, $yNew) = MJtoMM ($xJ[$m][0], $yJ[$m][0], $octant, $sin60, $cos60);
      $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      ($xNew, $yNew) = MJtoMM ($xJ[$m][1], $yJ[$m][1], $octant, $sin60, $cos60);
      $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      ($xNew, $yNew) = MJtoMM ($xP[$m][65], $yP[$m][65], $octant, $sin60, $cos60);
      $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      # Do the meridian in the negative half-octant
      ($xNew, $yNew) = MJtoMM ($xJ[$m][0], -$yJ[$m][0], $octant, $sin60, $cos60);
      $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      ($xNew, $yNew) = MJtoMM ($xJ[$m][1], -$yJ[$m][1], $octant, $sin60, $cos60);
      $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      ($xNew, $yNew) = MJtoMM ($xP[$m][65], -$yP[$m][65], $octant, $sin60, $cos60);
      $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      $Major .= "L,2\n" . $temp1 . "L,2\n" . $temp2
    } # End of meridians
    # Prepare parallels; parallel 0° not done because it is on the octant's boundary.
    foreach $p (75) {  # Convert to wanted octant and write out values
      $temp1 = ""; $temp2 = "";
      # Positive half-octant
      foreach $m (0..45) {
        ($xNew, $yNew) = MJtoMM ($xP[$m][$p], $yP[$m][$p], $octant, $sin60, $cos60);
        $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      # Negative half-octant
      foreach $m (0..45) {
        ($xNew, $yNew) = MJtoMM ($xP[$m][$p], -$yP[$m][$p], $octant, $sin60, $cos60);
        $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      $Major .= "L,2\n" . $temp1 . "L,2\n" . $temp2
    }  # End of parallels
    # Write out meridians and parallels for this octant
    print MACRO $Major;
  } # End of graticule for Antarctica portions
  close (MACRO);
  print "File \"Graticule15.txt\" has been written.\n";
}  # End of block 2

# BLOCK (3): prepare graticule file of 5°, with joined Antarctica, for Duncan
unless ($Skip[3]) { # Option to skip
  ($xA, $yA, $xB, $yB, $xC, $yC, $xD, $yD, $xE, $yE, $xF, $yF, $xG, $yG,
      $xM, $yM, $xT, $yT, $AG, $AB, $BD, $GF, $BDE, $GFE, $R, $DeltaMEq) = @Prelims;
  # Open file, write out meridians and parallels
  open (MACRO, ">Graticule5.txt");  # Name for output file with OOo macro
  # Calculate all whole degree points on template half-octant
  foreach $m (0 .. 45) {
    foreach $p (1 .. 89) {
      ($xP[$m][$p], $yP[$m][$p]) = MPtoXY ($m, $p, @Prelims);
    }
    # Calculate meridian joints. Array's index is: 0 = polar start (point A);
    # 1 = frigid joint; 2 = torrid joint; 3 = equator. Meridain 0° has no joints; it goes from
    # A to G.
    if ($m > 0 && ($m % 5 == 0) ) {
      ($xJ[$m][3], $yJ[$m][3], $xJ[$m][2], $yJ[$m][2], $xJ[$m][1], $yJ[$m][1], $Lt, $Lm) =
        Joints ($m, $xA, $xE, $yE, $xF, $yF, $xG, $AB, $GF, $DeltaMEq);
      # Start point of meridians
      ($xJ[$m][0], $yJ[$m][0]) = ($xA, $yA);
    }
  } # Now I have all needed x,y points
  # Prepare graticule for whole octants 1 to 7. Octant 8 is partial, and will be done later
  foreach $octant (1 .. 7) {
    # Prepare meridians
    print "Doing octant $octant.\n";
    $Major = "";
    # o both positive and negative meridians (i.e. 5° and -5°).
    # Meridians multiple of 15 not done
    foreach $m (5, 10, 20, 25, 35, 40) {
      $temp1 = ""; $temp2 = "";
      # Do the meridian in the positive half-octant
      foreach $i (0..3) {
        ($xNew, $yNew) = MJtoMM ($xJ[$m][$i], $yJ[$m][$i], $octant, $sin60, $cos60);
        $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      # Do the meridian in the negative half-octant
      foreach $i (0..3) {
        ($xNew, $yNew) = MJtoMM ($xJ[$m][$i], -$yJ[$m][$i], $octant, $sin60, $cos60);
        $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      $Major .= "L,3\n" . $temp1 . "L,3\n" . $temp2
    } # End of meridians
    # Prepare parallels; multiples of 15° not done
    foreach $p (5, 10, 20, 25, 35, 40, 50, 55, 65, 70, 80, 85) {
      $temp1 = ""; $temp2 = "";
      # Positive half-octant
      foreach $m (0..45) {
        ($xNew, $yNew) = MJtoMM ($xP[$m][$p], $yP[$m][$p], $octant, $sin60, $cos60);
        $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      # Negative half-octant
      foreach $m (0..45) {
        ($xNew, $yNew) = MJtoMM ($xP[$m][$p], -$yP[$m][$p], $octant, $sin60, $cos60);
        $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      $Major .= "L,3\n" . $temp1 . "L,3\n" . $temp2
    }  # End of parallels
    # Write out meridians and parallels for this octant
    print MACRO $Major;
  } # End of graticule for octants 1 to 7
  # Now do octant 8 only from equator to 65°; part with Antarctica not done
  $octant = 8;
  print "Doing octant $octant from equator to 65°.\n";
  $Major = "";
  # Do both positive and negative meridians (i.e. 5° and -5°).
  foreach $m (5, 10, 20, 25, 35, 40) {
    $temp1 = ""; $temp2 = "";
    # Do the meridian in the positive half-octant: parallel 65, torrid joint, equator;
    # start point ([0]) and frigid joint ([1]) not used because they are beyond parallel 65°.
    ($xNew, $yNew) = MJtoMM ($xP[$m][65], $yP[$m][65], $octant, $sin60, $cos60);
    $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    ($xNew, $yNew) = MJtoMM ($xJ[$m][2], $yJ[$m][2], $octant, $sin60, $cos60);
    $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    ($xNew, $yNew) = MJtoMM ($xJ[$m][3], $yJ[$m][3], $octant, $sin60, $cos60);
    $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    # Do the meridian in the negative half-octant
    ($xNew, $yNew) = MJtoMM ($xP[$m][65], -$yP[$m][65], $octant, $sin60, $cos60);
    $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    ($xNew, $yNew) = MJtoMM ($xJ[$m][2], -$yJ[$m][2], $octant, $sin60, $cos60);
    $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    ($xNew, $yNew) = MJtoMM ($xJ[$m][3], -$yJ[$m][3], $octant, $sin60, $cos60);
    $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    $Major .= "L,3\n" . $temp1 . "L,3\n" . $temp2
  } # End of meridians
  # Prepare parallels
  foreach $p (5, 10, 20, 25, 35, 40, 50, 55, 65) {
    $temp1 = ""; $temp2 = "";
    # Positive half-octant
    foreach $m (0..45) {
      ($xNew, $yNew) = MJtoMM ($xP[$m][$p], $yP[$m][$p], $octant, $sin60, $cos60);
      $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    }
    # Negative half-octant
    foreach $m (0..45) {
      ($xNew, $yNew) = MJtoMM ($xP[$m][$p], -$yP[$m][$p], $octant, $sin60, $cos60);
      $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    }
    $Major .= "L,3\n" . $temp1 . "L,3\n" . $temp2
  }  # End of parallels
  # Write out meridians and parallels for this octant
  print MACRO $Major;
  # End of partial graticule for octant 8
  # Now do graticule for Antarctica sections of octants 5, 6, 8, rotated to join with
  # whole-octant 7; they are, respectively, areas "7pv", "7wp" and "7ep".
  foreach $octant ("7pv", "7wp", "7ep") {
    # Prepare meridians, from point A to parallel 65°.
    print "Doing Antarctica section $octant.\n";
    $Major = "";
    # Do both positive and negative meridians (i.e. 5° and -5°).
    foreach $m (5, 10, 20, 25, 35, 40) {
      $temp1 = ""; $temp2 = "";
      # Do the meridian in the positive half-octant: start point A to frigid joint ([1]),
      # to parallel 65°.
      ($xNew, $yNew) = MJtoMM ($xJ[$m][0], $yJ[$m][0], $octant, $sin60, $cos60);
      $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      ($xNew, $yNew) = MJtoMM ($xJ[$m][1], $yJ[$m][1], $octant, $sin60, $cos60);
      $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      ($xNew, $yNew) = MJtoMM ($xP[$m][65], $yP[$m][65], $octant, $sin60, $cos60);
      $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      # Do the meridian in the negative half-octant
      ($xNew, $yNew) = MJtoMM ($xJ[$m][0], -$yJ[$m][0], $octant, $sin60, $cos60);
      $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      ($xNew, $yNew) = MJtoMM ($xJ[$m][1], -$yJ[$m][1], $octant, $sin60, $cos60);
      $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      ($xNew, $yNew) = MJtoMM ($xP[$m][65], -$yP[$m][65], $octant, $sin60, $cos60);
      $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      $Major .= "L,3\n" . $temp1 . "L,3\n" . $temp2
    } # End of meridians
    # Prepare parallels
    foreach $p (65, 70, 80, 85) {  # Convert to wanted octant and write out values
      $temp1 = ""; $temp2 = "";
      # Positive half-octant
      foreach $m (0..45) {
        ($xNew, $yNew) = MJtoMM ($xP[$m][$p], $yP[$m][$p], $octant, $sin60, $cos60);
        $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      # Negative half-octant
      foreach $m (0..45) {
        ($xNew, $yNew) = MJtoMM ($xP[$m][$p], -$yP[$m][$p], $octant, $sin60, $cos60);
        $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      $Major .= "L,3\n" . $temp1 . "L,3\n" . $temp2
    }  # End of parallels
    # Write out meridians and parallels for this octant
    print MACRO $Major;
  } # End of graticule for Antarctica portions
  close (MACRO);
  print "File \"Graticule5.txt\" has been written.\n";
}  # End of  block 3

# BLOCK (4): 

unless ($Skip[4]) {	# Option to skip 
  # preparing octant outline for whole megamap, with joined Antarctica
  ($xA, $yA, $xB, $yB, $xC, $yC, $xD, $yD, $xE, $yE, $xF, $yF, $xG, $yG,
      $xM, $yM, $xT, $yT, $AG, $AB, $BD, $GF, $BDE, $GFE, $R, $DeltaMEq) = @Prelims;
  # Open file
  open (MACRO, ">Outline.txt");  # Name for output file with OOo macro
  # Calculate point (45°, 65°) on template half-octant
  ($xP, $yP) = MPtoXY (45, 65, @Prelims);
  # Prepare outline for whole octants 1 to 7. Octant 8 is partial, and will be done later
  foreach $octant (1 .. 7) {
    print "Doing octant $octant.\n";
    # Octant's outline (drawn with color 1)
    print MACRO "L,1\n";
    @xOct = ($xA, $xB, $xD, $xE, $xF, $xF, $xE, $xD, $xB, $xA);
    @yOct = ($yA, $yB, $yD, $yE, $yF, -$yF, -$yE, -$yD, -$yB, $yA);
    foreach $i (0..9) {
      ($xNew, $yNew) = MJtoMM ($xOct[$i], $yOct[$i], $octant, $sin60, $cos60);
      printf MACRO ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    }
  } # End of graticule for octants 1 to 7
  # Now do octant 8 only from equator to 65°; part with Antarctica not done
  $octant = 8;
  print "Doing octant $octant from equator to 65°.\n";
  print MACRO "L,1\n";
  @xOct = ($xP, $xD, $xE, $xF, $xF, $xE, $xD, $xP);
  @yOct = ($yP, $yD, $yE, $yF, -$yF, -$yE, -$yD, -$yP);
  foreach $i (0..7) {
    ($xNew, $yNew) = MJtoMM ($xOct[$i], $yOct[$i], $octant, $sin60, $cos60);
    printf MACRO ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
  } # End of partial graticule for octant 8
  # Now do outline for Antarctica sections of octants 5, 6, 8, rotated to join with
  # whole-octant 7; they are, respectively, areas "7pv", "7wp" and "7ep".
  foreach $octant ("7pv", "7wp", "7ep") {
    print MACRO "L,1\n";
    @xOct = ($xP, $xB, $xA, $xB, $xP);
    @yOct = ($yP, $yB, $yA, -$yB, -$yP);
    foreach $i (0..4) {
      ($xNew, $yNew) = MJtoMM ($xOct[$i], $yOct[$i], $octant, $sin60, $cos60);
      printf MACRO ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    }
  } # End of outline for Antarctica portions
  close (MACRO);
  print "File \"Outline.txt\" has been written.\n";
}  # End of block 4

# BLOCK (5): prepare graticule for whole megamap, with joined Antarctica; includes
# minor (1°) graticule, major (5°) graticule, and octant boundaries.

unless ($Skip[5]) { # Option to skip 
  # preparing graticule for whole megamap, with joined Antarctica
  ($xA, $yA, $xB, $yB, $xC, $yC, $xD, $yD, $xE, $yE, $xF, $yF, $xG, $yG,
      $xM, $yM, $xT, $yT, $AG, $AB, $BD, $GF, $BDE, $GFE, $R, $DeltaMEq) = @Prelims;
  # Open file, write out meridians and parallels, minor first and then the major ones.
  open (MACRO, ">Graticule.txt");  # Name for output file with OOo macro
  # Calculate all whole degree points on template half-octant
  foreach $m (0 .. 45) {
    foreach $p (1 .. 89) {
      ($xP[$m][$p], $yP[$m][$p]) = MPtoXY ($m, $p, @Prelims);
    }
    # Calculate meridian joints. Array's index is: 0 = polar start (point A or parallel 85°);
    # 1 = frigid joint; 2 = torrid joint; 3 = equator. Meridain 0° has no joints; it goes from
    # A to G.
    if ($m > 0) {
      ($xJ[$m][3], $yJ[$m][3], $xJ[$m][2], $yJ[$m][2], $xJ[$m][1], $yJ[$m][1], $Lt, $Lm) =
        Joints ($m, $xA, $xE, $yE, $xF, $yF, $xG, $AB, $GF, $DeltaMEq);
      # Start point of meridians
      if ($m %5 == 0) {  # Every 5th meridian starts at point A
        ($xJ[$m][0], $yJ[$m][0]) = ($xA, $yA);
      } else {  # Minor meridians start at 85° of latitude
        ($xJ[$m][0], $yJ[$m][0]) = ($xP[$m][85], $yP[$m][85]);
      }
    }
  } # Now I have all needed x,y points
  # Prepare graticule for whole octants 1 to 7. Octant 8 is partial, and will be done later
  foreach $octant (1 .. 7) {
    # Prepare meridians, starting with 0°, which is a straight line from point A to point G.
    print "Doing octant $octant.\n";
    $Minor = "";
    $Major = "L,2\n";
    ($xNew, $yNew) = MJtoMM ($xA, $yA, $octant, $sin60, $cos60);
    $Major .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    ($xNew, $yNew) = MJtoMM ($xG, $yG, $octant, $sin60, $cos60);
    $Major .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);    
    # Other than meridian 0°, do both positive and negative meridians (i.e. 5° and -5°).
    # Meridian 45° not done because it would be covered by the octant's boundary.
    foreach $m (1 .. 44) {
      $temp1 = ""; $temp2 = "";
      # Do the meridian in the positive half-octant
      foreach $i (0..3) {
        ($xNew, $yNew) = MJtoMM ($xJ[$m][$i], $yJ[$m][$i], $octant, $sin60, $cos60);
        $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      # Do the meridian in the negative half-octant
      foreach $i (0..3) {
        ($xNew, $yNew) = MJtoMM ($xJ[$m][$i], -$yJ[$m][$i], $octant, $sin60, $cos60);
        $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      if ($m %5 == 0) { # Major meridian, drawn with color 2
        $Major .= "L,2\n" . $temp1 . "L,2\n" . $temp2
      } else { # Minor meridian, drawn with color 3
        $Minor .= "L,3\n" . $temp1 . "L,3\n" . $temp2
      }
    } # End of meridians
    # Prepare parallels; parallel 0° not done because it is on the octant's boundary.
    foreach $p (1 .. 89) {  # Convert to wanted octant and write out values
      $temp1 = ""; $temp2 = "";
      # Positive half-octant
      foreach $m (0..45) {
        ($xNew, $yNew) = MJtoMM ($xP[$m][$p], $yP[$m][$p], $octant, $sin60, $cos60);
        $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      # Negative half-octant
      foreach $m (0..45) {
        ($xNew, $yNew) = MJtoMM ($xP[$m][$p], -$yP[$m][$p], $octant, $sin60, $cos60);
        $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      if ($p %5 == 0) { # Major parallel, drawn with color 2
        $Major .= "L,2\n" . $temp1 . "L,2\n" . $temp2
      } else { # Minor parallel, drawn with color 3
        $Minor .= "L,3\n" . $temp1 . "L,3\n" . $temp2
      }
    }  # End of parallels
    # Write out meridians and parallels for this octant, minor first and then the major ones.
    print MACRO $Minor, $Major;
    # Octant's outline (drawn with color 1)
    print MACRO "L,1\n";
    @xOct = ($xA, $xB, $xD, $xE, $xF, $xF, $xE, $xD, $xB, $xA);
    @yOct = ($yA, $yB, $yD, $yE, $yF, -$yF, -$yE, -$yD, -$yB, $yA);
    foreach $i (0..9) {
      ($xNew, $yNew) = MJtoMM ($xOct[$i], $yOct[$i], $octant, $sin60, $cos60);
      printf MACRO ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    }
  } # End of graticule for octants 1 to 7
  # Now do octant 8 only from equator to 65°; part with Antarctica not done
  $octant = 8;
  print "Doing octant $octant from equator to 65°.\n";
  $Minor = "";
  $Major = "L,2\n";
  ($xNew, $yNew) = MJtoMM ($xP[0][65], $yP[0][65], $octant, $sin60, $cos60);
  $Major .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
  ($xNew, $yNew) = MJtoMM ($xG, $yG, $octant, $sin60, $cos60);
  $Major .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);    
  # Other than meridian 0°, do both positive and negative meridians (i.e. 5° and -5°).
  # Meridian 45° not done because it would be covered by the octant's boundary.
  foreach $m (1 .. 44) {
    $temp1 = ""; $temp2 = "";
    # Do the meridian in the positive half-octant: parallel 65, torrid joint, equator;
    # start point ([0]) and frigid joint ([1]) not used because they are beyond parallel 65°.
    ($xNew, $yNew) = MJtoMM ($xP[$m][65], $yP[$m][65], $octant, $sin60, $cos60);
    $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    ($xNew, $yNew) = MJtoMM ($xJ[$m][2], $yJ[$m][2], $octant, $sin60, $cos60);
    $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    ($xNew, $yNew) = MJtoMM ($xJ[$m][3], $yJ[$m][3], $octant, $sin60, $cos60);
    $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    # Do the meridian in the negative half-octant
    ($xNew, $yNew) = MJtoMM ($xP[$m][65], -$yP[$m][65], $octant, $sin60, $cos60);
    $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    ($xNew, $yNew) = MJtoMM ($xJ[$m][2], -$yJ[$m][2], $octant, $sin60, $cos60);
    $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    ($xNew, $yNew) = MJtoMM ($xJ[$m][3], -$yJ[$m][3], $octant, $sin60, $cos60);
    $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    if ($m %5 == 0) { # Major meridian, drawn with color 2
      $Major .= "L,2\n" . $temp1 . "L,2\n" . $temp2
    } else { # Minor meridian, drawn with color 3
      $Minor .= "L,3\n" . $temp1 . "L,3\n" . $temp2
    }
  } # End of meridians
  # Prepare parallels; parallel 0° not done because it is on the octant's boundary.
  foreach $p (1 .. 65) {  # Convert to wanted octant and write out values
    $temp1 = ""; $temp2 = "";
    # Positive half-octant
    foreach $m (0..45) {
      ($xNew, $yNew) = MJtoMM ($xP[$m][$p], $yP[$m][$p], $octant, $sin60, $cos60);
      $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    }
    # Negative half-octant
    foreach $m (0..45) {
      ($xNew, $yNew) = MJtoMM ($xP[$m][$p], -$yP[$m][$p], $octant, $sin60, $cos60);
      $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    }
    if ($p %5 == 0) { # Major parallel, drawn with color 2
      $Major .= "L,2\n" . $temp1 . "L,2\n" . $temp2
    } else { # Minor parallel, drawn with color 3
      $Minor .= "L,3\n" . $temp1 . "L,3\n" . $temp2
    }
  }  # End of parallels
  # Write out meridians and parallels for this octant, minor first and then the major ones.
  print MACRO $Minor, $Major;
  # Octant's outline (drawn with color 1)
  print MACRO "L,1\n";
  @xOct = ($xP[45][65], $xD, $xE, $xF, $xF, $xE, $xD, $xP[45][65]);
  @yOct = ($yP[45][65], $yD, $yE, $yF, -$yF, -$yE, -$yD, -$yP[45][65]);
  foreach $i (0..7) {
    ($xNew, $yNew) = MJtoMM ($xOct[$i], $yOct[$i], $octant, $sin60, $cos60);
    printf MACRO ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
  } # End of partial graticule for octant 8
  # Now do graticule for Antarctica sections of octants 5, 6, 8, rotated to join with
  # whole-octant 7; they are, respectively, areas "7pv", "7wp" and "7ep".
  foreach $octant ("7pv", "7wp", "7ep") {
    # Prepare meridians, starting with 0°, which is a straight line from point A to parallel 65°.
    print "Doing Antarctica section $octant.\n";
    $Minor = "";
    $Major = "L,2\n";
    ($xNew, $yNew) = MJtoMM ($xA, $yA, $octant, $sin60, $cos60);
    $Major .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    ($xNew, $yNew) = MJtoMM ($xP[0][65], $yP[0][65], $octant, $sin60, $cos60);
    $Major .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    # Other than meridian 0°, do both positive and negative meridians (i.e. 5° and -5°).
    # Meridian 45° not done because it would be covered by the octant's boundary.
    foreach $m (1 .. 44) {
      $temp1 = ""; $temp2 = "";
      # Do the meridian in the positive half-octant: start point (A or 85°, which is in [0]) to
      # frigid joint ([1]), to parallel 65°.
      ($xNew, $yNew) = MJtoMM ($xJ[$m][0], $yJ[$m][0], $octant, $sin60, $cos60);
      $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      ($xNew, $yNew) = MJtoMM ($xJ[$m][1], $yJ[$m][1], $octant, $sin60, $cos60);
      $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      ($xNew, $yNew) = MJtoMM ($xP[$m][65], $yP[$m][65], $octant, $sin60, $cos60);
      $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      # Do the meridian in the negative half-octant
      ($xNew, $yNew) = MJtoMM ($xJ[$m][0], -$yJ[$m][0], $octant, $sin60, $cos60);
      $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      ($xNew, $yNew) = MJtoMM ($xJ[$m][1], -$yJ[$m][1], $octant, $sin60, $cos60);
      $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      ($xNew, $yNew) = MJtoMM ($xP[$m][65], -$yP[$m][65], $octant, $sin60, $cos60);
      $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      if ($m %5 == 0) { # Major meridian, drawn with color 2
        $Major .= "L,2\n" . $temp1 . "L,2\n" . $temp2
      } else { # Minor meridian, drawn with color 3
        $Minor .= "L,3\n" . $temp1 . "L,3\n" . $temp2
      }
    } # End of meridians
    # Prepare parallels; parallel 0° not done because it is on the octant's boundary.
    foreach $p (65 .. 89) {  # Convert to wanted octant and write out values
      $temp1 = ""; $temp2 = "";
      # Positive half-octant
      foreach $m (0..45) {
        ($xNew, $yNew) = MJtoMM ($xP[$m][$p], $yP[$m][$p], $octant, $sin60, $cos60);
        $temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      # Negative half-octant
      foreach $m (0..45) {
        ($xNew, $yNew) = MJtoMM ($xP[$m][$p], -$yP[$m][$p], $octant, $sin60, $cos60);
        $temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
      if ($p %5 == 0) { # Major parallel, drawn with color 2
        $Major .= "L,2\n" . $temp1 . "L,2\n" . $temp2
      } else { # Minor parallel, drawn with color 3
        $Minor .= "L,3\n" . $temp1 . "L,3\n" . $temp2
      }
    }  # End of parallels
    # Write out meridians and parallels for this octant, minor first and then the major ones.
    print MACRO $Minor, $Major;
    # Octant's outline (drawn with color 1)
    print MACRO "L,1\n";
    @xOct = ($xP[45][65], $xB, $xA, $xB, $xP[45][65]);
    @yOct = ($yP[45][65], $yB, $yA, -$yB, -$yP[45][65]);
    foreach $i (0..4) {
      ($xNew, $yNew) = MJtoMM ($xOct[$i], $yOct[$i], $octant, $sin60, $cos60);
      printf MACRO ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    }
  } # End of graticule for Antarctica portions
  close (MACRO);
  print "File \"Graticule.txt\" has been written.\n";
}  # End of block 5

# BLOCK (6): Prepare major circles of latitude, with joined Antarctica, for Duncan
unless ($Skip[6]) { # Option to skip 
  ($xA, $yA, $xB, $yB, $xC, $yC, $xD, $yD, $xE, $yE, $xF, $yF, $xG, $yG,
      $xM, $yM, $xT, $yT, $AG, $AB, $BD, $GF, $BDE, $GFE, $R, $DeltaMEq) = @Prelims;
  # Calculate Arctic Circle (66° 33' 44") and Tropic of Capricorn (23° 26'16") in MJ's template
  $Circ = 66 + 33 / 60 + 44 / 3600;
  $Trop = 23 + 26 / 60 + 16 / 3600;
  foreach $m (0 .. 45) {
    ($xCirc[$m], $yCirc[$m]) = MPtoXY ($m, $Circ, @Prelims);
    ($xTrop[$m], $yTrop[$m]) = MPtoXY ($m, $Trop, @Prelims);
  }
  # Convert Tropic to each half octant and Circle to each half-octant, except in octant 8
  $Temp1 = "";  # for eastern half-octant tropics
  $Temp2 = "";  # for western half-octant tropics
  $Temp3 = "";  # for eastern half-octant circles
  $Temp4 = "";  # for western half-octant circles
  foreach $octant (1 .. 8) {
    $Temp1 .= "L,4\n";
    $Temp2 .= "L,4\n";
    foreach $m (0 .. 45) {
      ($xNew, $yNew) = MJtoMM ($xTrop[$m], $yTrop[$m], $octant, $sin60, $cos60);
      $Temp1 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      ($xNew, $yNew) = MJtoMM ($xTrop[$m], -$yTrop[$m], $octant, $sin60, $cos60);
      $Temp2 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    }
    unless ($octant == 8) { # Octant 8 is truncated at 65°; don't do the circle for it
      $Temp3 .= "L,4\n";
      $Temp4 .= "L,4\n";
      foreach $m (0 .. 45) {
        ($xNew, $yNew) = MJtoMM ($xCirc[$m], $yCirc[$m], $octant, $sin60, $cos60);
        $Temp3 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
        ($xNew, $yNew) = MJtoMM ($xCirc[$m], -$yCirc[$m], $octant, $sin60, $cos60);
        $Temp4 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      }
    }
  }
  # Now do the circles in the 3 Antarctica extensions
  foreach $octant ("7pv", "7wp", "7ep") {
    $Temp3 .= "L,4\n";
    $Temp4 .= "L,4\n";
    foreach $m (0 .. 45) {
      ($xNew, $yNew) = MJtoMM ($xCirc[$m], $yCirc[$m], $octant, $sin60, $cos60);
      $Temp3 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
      ($xNew, $yNew) = MJtoMM ($xCirc[$m], -$yCirc[$m], $octant, $sin60, $cos60);
      $Temp4 .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    }
  }
  # Open file
  open (MACRO, ">MajorCircles.txt");  # Name for output file with OOo macro
  print MACRO $Temp1, $Temp2, $Temp3, $Temp4;
  close (MACRO);
  print "File \"MajorCircles.txt\" has been written.\n";
} # End block 6

# BLOCK (7): Prepare partial graticule, for an extension
unless ($Skip[7]) { # Option to skip
  # NOTE: This expects all the partial graticule to be entirely within either the eastern
  #   or western half of an octant, but does not check if this is so.
  print "For which region do you want to prepare partial graticule?\n";
  print "(longitude, longitude, latitude, latitude)\n";
  $Line = <STDIN>;
  chomp ($Line);
  ($MinLong,$MaxLong,$MinLat,$MaxLat) = split(/,/,$Line);
  print "For which area code do you want to prepare partial graticule?\n";
  $Area = <STDIN>;
  chomp ($Area);
  ($WantedOctant, $flag) = CheckArea($Area);
  if ($flag) {die "Terminating.\n";}  # If area was not recognized, terminate program.
  print "Type in name for output file to receive x,y coordinates.\nWill prepare up to 5 files:";
  print " for octant boundary, major circles, 1, 5 and 15 degree graticule;\n";
  print "filenames will reflect this.\n";
  $FileOut = <STDIN>;
  chomp ($FileOut);
  # Convert real longitude, latitude to template half-octant meridian and parallel
  ($xA, $yA, $xB, $yB, $xC, $yC, $xD, $yD, $xE, $yE, $xF, $yF, $xG, $yG,
      $xM, $yM, $xT, $yT, $AG, $AB, $BD, $GF, $BDE, $GFE, $R, $DeltaMEq) = @Prelims;
  ($mMin, $pMin, $Sign1, $flag) = CheckOctant ($MinLong, $MinLat, $WantedOctant);
  if ($flag) {
    $ToWrite = "Error: Point $MinLong, $MinLat would be meridian " . $mMin * $Sign1;
    $ToWrite .= ", parallel $pMin in octant $flag. To be in area code "; 
    $ToWrite .= "\"$Area\", it needs to be in octant number $WantedOctant.\n";
    $ToWrite .= "Terminating.\n";
    die $ToWrite;
  }  # If flag is true, point is not in correct octant; terminate program
  ($mMax, $pMax, $Sign2, $flag) = CheckOctant ($MaxLong, $MaxLat, $WantedOctant);
  if ($flag) {
    $ToWrite = "Error: Point $MaxLong, $MaxLat would be meridian " . $mMax * $Sign2;
    $ToWrite .= ", parallel $pMax in octant $flag. To be in area code "; 
    $ToWrite .= "\"$Area\", it needs to be in octant number $WantedOctant.\n";
    $ToWrite .= "Terminating.\n";
    die $ToWrite;
  }  # If flag is true, point is not in correct octant; terminate program
  @Temp = ("","","","","");
  @Color = (3,2,2,1,4); # 3-minor, 2-major, 1-octant boundary, 4-major circle
  if ($mMin > $mMax) {($mMin, $mMax) = ($mMax, $mMin);}
  if ($pMin > $pMax) { ($pMin, $pMax) = ($pMax, $pMin);}
  # Do parallels
  foreach $p ($pMin .. $pMax) {
    if ($p % 15 == 0) {
      $i = 2;
      if ($p == 0) {$i = 3; } # octant boundary
    } elsif ($p % 5 == 0) {
      $i = 1;
    } else {  # 1 degree graticule, i.e., minor graticule
      $i = 0;
    }
    $Temp [$i] .= "L," . $Color[$i] . "\n";
    foreach $m ($mMin .. $mMax) {
      ($x, $y) = MPtoXY ($m, $p, @Prelims);
      ($xNew, $yNew) = MJtoMM ($x, $Sign1*$y, $Area, $sin60, $cos60);
      $Temp[$i] .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    }
  }
  # Do meridians
  foreach $m ($mMin .. $mMax) {    
    if ($m % 15 == 0) {
      $i = 2;
      if ($m == 45) { $i = 3; }  # Octant boundary
    } elsif ($m % 5 == 0) {
      $i = 1;
    } else {
      $i = 0;
    }
    $Temp [$i] .= "L," . $Color[$i] . "\n";
    foreach $p ($pMin .. $pMax) {
      ($x, $y) = MPtoXY ($m, $p, @Prelims);
      ($xNew, $yNew) = MJtoMM ($x, $Sign1*$y, $Area, $sin60, $cos60);
      $Temp[$i] .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    }
  }
  # Do major circles, if any
  # Calculate Arctic Circle (66° 33' 44") and Tropic of Capricorn (23° 26'16") in MJ's template
  $Circ = 66 + 33 / 60 + 44 / 3600;
  $Trop = 23 + 26 / 60 + 16 / 3600;
  $i = 4; # Index for major circles
  if ($pMin <= $Circ && $Circ <= $pMax) {
    $Temp [$i] .= "L," . $Color[$i] . "\n";
    foreach $m ($mMin .. $mMax) {
      ($x, $y) = MPtoXY ($m, $Circ, @Prelims);
      ($xNew, $yNew) = MJtoMM ($x, $Sign1*$y, $Area, $sin60, $cos60);
      $Temp[$i] .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    }
  }
  if ($pMin <= $Trop && $Trop <= $pMax) {
    $Temp [$i] .= "L," . $Color[$i] . "\n";
    foreach $m ($mMin .. $mMax) {
      ($x, $y) = MPtoXY ($m, $Trop, @Prelims);
      ($xNew, $yNew) = MJtoMM ($x, $Sign1*$y, $Area, $sin60, $cos60);
      $Temp[$i] .= sprintf ("%.0f,%.0f\n", 100*$xNew,-100*$yNew);
    }
  }
  # Write output files
  $File[0] = "> " .  $FileOut . "1.txt";
  $File[1] = "> " .  $FileOut . "5.txt";
  $File[2] = "> " .  $FileOut . "15.txt";
  $File[3] = "> " .  $FileOut . "Oct.txt";
  $File[4] = "> " .  $FileOut . "Circ.txt";
  $Flag = 0;
  $NewTemp = "";
  foreach $i (0 .. 4) {
    if ($Temp[$i] ne "") {
      open (FILE, $File[$i]) || die "Sorry, I couldn't open output file, \"$File[$i]\".\n";
      print FILE $Temp[$i];
      close (FILE);
      substr($File[$i],0,2) = "";  # Delete "> " from file name
      if ($Flag) { $NewTemp .=  ", "; }
      $NewTemp .= "\"$File[$i]\"";
      $Flag ++;
    }
  }
  if ($Flag == 0) {
    print "Nothing written.\n";
  } elsif ($Flag == 1) {
    print "File $NewTemp has been written.\n";
  } else {
    print "Files $NewTemp have been written.\n";
  }
} # End block 7, which prepares graticule for whole megamap with joined Antarctica

# BLOCK (8): prepare graticule for whole megamap, with joined Antarctica; includes
# minor (1°) graticule, major (5°) graticule, and octant boundaries.

unless ($Skip[8]) { # Option to skip
      ($xNew, $yNew)= MJtoMap(0, 0, 3,8, "M", @Conv);

#  print "Nothing to do in block 8.\n";
} # End block 8

# BLOCK (9): 
unless ($Skip[9]) { # Option to skip
#  print "Which layout? Type M for Megamap (M or W) or B for Butterfly.\n";
#  $Layout = <STDIN>;
#  chomp ($Layout);
#  $Layout = "\U$Layout";  # Capitalize it, in case it was typed lower case
#  if ($Layout ne "M" && $Layout ne "B") {
#    die ", You should have typed either M or B, not $Layout. Terminating.\n";
#  }
#  print "Type in number of octant which is flat against east of centre line of layout.\n";
#  $OctantCenterEast = <STDIN>;
#  chomp ($OctantCenterEast);
#  if (!($OctantCenterEast =~ /[1-8]/ && length($OctantCenterEast) == 1) ) {
#    die "Octant number should be between 1 and 8. Terminating.\n";
#  }
#  print "Type in name of MAPGEN file with coastal data.\n";
#  $FileIn = <STDIN>;
#  chomp ($FileIn);
#  print "Type in name for output file to receive x,y coordinates.\n";
#  $FileOut = <STDIN>;
#  chomp ($FileOut);
  # Output will be a plain text file with the following for each segment:
  # line with "L,0" (without quotes), followed by lines of x,y (comma included) values.
  #
  # Read some Coastal Data, convert to M-map coordinates, and write to output file.
  # File read is a zipped or unzipped file of MAPGEN data format: two columns ASCII flat
  # file with: longitude tab latitude; at the start of each segment there is a line containing
  # only "# -b".
  # Set up a few variables
  # Octant boundaries (points A, B, D, E, F, -F, -E, -D, -B, A, G)
  @xBorder = (@Prelims[0,2,6,8,10,10,8,6,2,0], 10000);
  @yBorder = (@Prelims[1,3,7,9,11],-$Prelims[11],-$Prelims[9],-$Prelims[7],
     -$Prelims[3],$Prelims[1], 0);
  foreach $Layout ("M","B") {
  foreach $OctantCenterEast (1 .. 8) {
    $FileIn = "Continents.txt";
  $FileOut = "XY" . $Layout . $OctantCenterEast;
  $maxX=-99999;  $maxY=-99999;  $minX=999999;  $minY=999999;
  $oldLong = 99999;  $oldLat = 99999;
  # Start output file
  $FileOut2 = "> " . $FileOut;
  # Open output file to receive x,y coordinates
  open (FILEXY, $FileOut2) || die "Sorry, I couldn't open output file, \"$FileOut\".\n";
  # Open coastal data file, taking into account whether or not it is compressed as .zip
  if ( $FileIn =~ /.\.zip$/i || $FileIn =~ /.\.gz$/i) {
   # If file ends in a letter plus a period plus "zip" or "ZIP" or gz
   $FileIn2 = "zcat \"" . $FileIn . "\" | ";  # Compressed file
  } else {
   $FileIn2 = $FileIn;  # normal, uncompressed file
  }
  open (DATA, $FileIn2) || die "Sorry, I couldn't open input file, \"$FileIn2\".\n";
  $nData = 0;
  $nWrite = 0;
  $nHead = 0;
  $flag2 = 0;
  # print "This might take awhile. I'll let you know every 1,000 lines that I read.\n\n";
  foreach $Area (1 .. 8) {  # for each octant
    print FILEXY ("L,3\n" );
    foreach $i (0 .. 10) {  # for each point on the boundary
      ($xNew, $yNew)= MJtoMap($xBorder[$i], $yBorder[$i], $Area,
        $OctantCenterEast, $Layout, @Conv);
      printf FILEXY ("%.0f,%.0f\n", $xNew * 100, -$yNew * 100);
    }
  }

  while (<DATA>) {
    $Line = $_ ;
    chomp($Line);  # Remove new-line character from end of line of data read
    if ($Line =~ /\r$/ ) {
      chop($Line);  # removing a return character, if there is one
    }
    $nData ++;
    if ($nData % 1000 == 0) { print "Read $nData lines of land data so far.\n"; }
    if (index($Line,'#') < 0) {  # Process line with longitude, latitude
     ($Long,$Lat) = split(/\t/,$Line);
     if (defined($Long) && defined($Lat)) {  # Do only if there are two values on this line
      if ( ! ($Long == $oldLong && $Lat == $oldLat) ) {
        # If this point is a repeat of the previous point on this segment, this section is
        # not run, and this point is neither converted nor included in the output file.
        $oldLong = $Long;  $oldLat = $Lat;
        # COORDINATE CONVERSION
        # Convert real longitude, latitude to template half-octant meridian and parallel
        ($m, $p, $Sign, $flag) = CheckOctant ($Long, $Lat, $WantedOctant);
        if ($flag) {  # If flag is true, point is not in correct octant; terminate program
#          $ToWrite = "Error: Point $Long, $Lat would be meridian " . $m * $Sign;
#          $ToWrite .= ", parallel $p in octant $flag. To be in area code "; 
#          $ToWrite .= "\"$Area\", it needs to be in octant number $WantedOctant.\n";
#          $ToWrite .= "Terminating.\n";
#          close (FILEXY);
#          close (DATA);
#          die $ToWrite;
          $ToWrite = "Error at line $nData of input file:\n";
          $ToWrite .= "Point $Long, $Lat would be meridian " . $m * $Sign;
          $ToWrite .= ", parallel $p in octant $flag. To be in area code "; 
          $ToWrite .= "\"$Area\", it needs to be in octant number $WantedOctant.\n";
          $ToWrite .= "Type y to accept octant $flag and n to terminate.\n";
          print $ToWrite;
          $Answer = <STDIN>;
          chomp ($Answer);
          if ($Answer eq "y") {
            $flag2 = 1;
          } else {
            close (FILEXY);
            close (DATA);
            die "Terminating.\n";
          }
        }
        # Convert template meridian, parallel to template half-octant x, y coordinates
        ($x, $y) = MPtoXY ($m, $p, @Prelims);
        # Convert template x, y coordinates to M-map or G's x and y coordinates.
        if ($flag2) { # Point on a different octant
          ($xNew,$yNew) = MJtoMap($x, $Sign*$y, $flag, $OctantCenterEast, $Layout, @Conv);
          $flag2 = 0;
        } else { # point where it should be
          ($xNew, $yNew)= MJtoMap($x, $Sign*$y, $Area, $OctantCenterEast, $Layout, @Conv);
        }
        # Keep track of maximum and minimum values
        if ($xNew < $minX) {$minX = $xNew;}
        if ($xNew > $maxX) {$maxX = $xNew;}
        if ($yNew < $minY) {$minY = $yNew;}
        if ($yNew > $maxY) {$maxY = $yNew;}
        # If this segment has already 1000 points, write it and start a new segment,
        # repeating the last point; new segment will have at least 2 points.
        if (@Xs == 999) {
          $nHead ++;
          $nPoints = @Xs - 1;
          print FILEXY ("L,0\n" );
          foreach $i (0 .. $nPoints) {
            # Values are multiplied by 100 to convert to 100ths of mm, and y-value is made
            # negative because OOo Draw uses y positive downwards.
            printf FILEXY ("%.0f,%.0f\n", $Xs[$i] * 100, -$Ys[$i] * 100);
          }
          @Xs = ($Xs[$nPoints]);  # Delete all values from arrays except the last one
          @Ys = ($Ys[$nPoints]);
          # Add one to the number of points, for the point that was written in this segment,
          # and will be rewritten on the next
          $nWrite ++;
        }
        # Make arrays of points for this segment to be written to output file
        push (@Xs,$xNew);
        push (@Ys,$yNew);
        $nWrite ++;
      }  # End of skipping if the last point read was the same as the previous one
     }  # End of doing if there really was data on the line, or skipping if there wasn't
    } else  { # Start of next segment
      if (defined(@Xs) ) {  # Write previous segment if data points were read
        # Write this segment of coastline with arrays @Xs and @Ys
        $nHead ++;
        $nPoints = @Xs - 1;
        print FILEXY ("L,0\n" );
        foreach $i (0 .. $nPoints) {
          # Values are multiplied by 100 to convert to 100ths of mm, and y-value is made
          # negative because OOo Draw uses y positive downwards.
          printf FILEXY ("%.0f,%.0f\n", $Xs[$i] * 100, -$Ys[$i] * 100);
        }
      }
      @Xs = ();  @Ys = ();  # Empty arrays, ready for next segment
      $oldLong = 99999;  $oldLat = 99999;  # Reset previous values to impossible values
      ($Area, $Area, $Coast) = split(/\t/,$Line);  # First part is "#"; ignore it by overwriting
      print "Starting coastline $Coast in area $Area\n";
      $Area = "\L$Area";  # Make it lower case, if perchance it wasn't
      ($WantedOctant, $flag) = CheckArea($Area);
      if ($flag) {  # If area was not recognized, terminate program.
        close (DATA);
        close (FILEXY);
        die "Terminating at line $nData of input file.\n";
      }
    }
  }
  close (DATA);
    if (index($Line,'#') < 0) { # Draw last segment, if it hasn't been drawn
    # Write this segment of coastline with arrays @Xs and @Ys
    $nHead ++;
    $nPoints = @Xs - 1;
    print FILEXY ("L,0\n" );
    foreach $i (0 .. $nPoints) {
      # Values are multiplied by 100 to convert to 100ths of mm, and y-value is made
      # negative because OOo Draw uses y positive downwards.
      printf FILEXY ("%.0f,%.0f\n", $Xs[$i] * 100, -$Ys[$i] * 100);
    }
  }
  close (FILEXY);
  $nWrite = $nWrite + $nHead;
  print "Read a total of $nData lines. Wrote $nWrite lines ($nHead segments) to file"; 
  print "\"$FileOut\". \n", $minX, ' <= x <= ',$maxX," and ",$minY, ' <= y <= ', $maxY, "\n";
  } # End for each octant at east of center
  } # End for each Layout, M or B
} # End block 9

if (($Answer =~ /[1-9]/ && length($Answer) == 1) ) {
  print "All done.\n";
} else {
  print "Nothing done.\n";
}

# -  -  -  -  -  -  -  -  -  S U B R O U T I N E S  -  -  -  -  -  -  -  -
sub Preliminary{
  # Calculates and returns an array with 29 values (0 to 28), in this order:
  # (for use of subs MJtoG and Rotate) $sin60, $cos60, $MGcos30,
  # (x and y coordinates of points) $xA, $yA, $xB, $yB, $xC, $yC, $xD, $yD, $xE, $yE,
  # $xF, $yF, $xG, $yG, $xM, $yM, $xT, $yT, (lengths) $AG, $AB, $BD, $GF, $BDE, $GFE,
  # $R, $DeltaMEq.

  use Math::Trig;
  # Values that will be returned
  my ($sin60, $cos60, $MGcos30);
  my ($xA, $yA, $xB, $yB, $xC, $yC, $xD, $yD, $xE, $yE, $xF, $yF, $xG, $yG, $xM, $yM);
  my ($xT, $yT, $AG, $AB, $BD, $GF, $BDE, $GFE, $R, $DeltaMEq);
  # Variables temporary to this sub
  my ($xN, $yN, $MB, $MN, $xU, $yU, $k, $xV, $yV);

  # Some constants for use by subs MJtoG and Rotate, which do coordinate axis
  # transformation. Angle of rotation is 60°.  Point G is (10000,0) in MJ, and (5000,0) in G
  $sin60 = sin (deg2rad(60));
  $cos60 = cos (deg2rad(60));
  # Distance between points M and G times cos 30°; cos 30° = sin 60°
  $MGcos30 = 10000 * $sin60; 

  # Given input
  $xM = 0;      $yM = 0;      # Point M is the origin of the axes
  $xG = 10000;      $yG = 0;      # Point G, at center of base of octant
  $xA = 940;      $yA = 0;      # Point A at apex of octant
  # Other points and lengths of interest, relating to scaffold triangle and half-octant
  $xN = $xG;      $yN = $xG * tan (deg2rad(30));      # Point N, point of triangle MNG
  ($xB, $yB) = LineIntersection ($xM, $yM, 30, $xA, $yA, 45);      # Point B
  $AG = $xG - $xA;
  $AB = Length ($xA, $yA, $xB, $yB);
  $MB = Length ($xM, $yM, $xB, $yB);
  $MN = Length ($xM, $yM, $xN, $yN);
  # Calculate point D, considering that length DN = MB
  $xD = Interpolate ($MB, $MN, $xN, $xM);      # D is away from N as B is away from M
  $yD = Interpolate ($MB, $MN, $yN, $yM);
  $xF = $xG;
  $yF = $yN - $MB;
  # Distance from point E to point N = distance from point A to point M = xA; calculate E
  $xE = $xN - $xA * sin (deg2rad(30));
  $yE = $yN - $xA * cos (deg2rad(30));
  $GF = $yF;
  $BD = Length ($xB, $yB, $xD, $yD);
  $BDE = $BD + $AB;      # Length AB = length DE
  $GFE = $AB + $GF;      # Length AB = length FE
  $DeltaMEq = $GFE / 45;      # 45 meridian spacings along equator for half an octant
  # Calculate Point T: First calculate point U = (30°,73°). Radius to circular arc of 73° =
  # 15° x 104mm/° + 2° x 100 mm/° = 1760 mm.
  $xU = $xA + 1760 * cos (deg2rad(30));
  $yU = 1760 * sin (deg2rad(30));
  # Point T is at intersection of line BD with line from point U perpendicular to BD.
  # Since line BD is 30° from horizontal, perpendicular line is -60° from horizontal.
  ($xT, $yT) = LineIntersection ( $xU, $yU, -60, $xB, $yB, 30);

  # To calculate point C, must first calculate point V = (29°, 15°).
  # First calculate joints of meridian 29°
  ($xJe, $yJe, $xJt, $yJt, $xJf, $yJf, $Lt, $Lm) =
      Joints (29, $xA, $xE, $yE, $xF, $yF, $xG, $AB, $GF, $DeltaMEq);
  # Next need point on parallel 73° for this meridian 29°; really, only $Lf is needed.
  ($xP73, $yP73, $Lf) = Parallel73 (29, $xA, $xT, $yT, $xJf, $yJf);
  # Do something with $xP73 and $yP73, only so that the compiler doesn't complain
  # that they were used only once; I really don't need them now.
  $xP73 = 1 * $xP73; $yP73 = 1 * $yP73;
  # Parallels are equally spaced between the equator and latitude 73° in this zone.
  # Both torrid and frigid joints are at latitudes lower than 73° in this region.
  # To find point V, calculate length from equator to parallel 15°, along meridian.
  # ($Lt + $Lm + $Lf) = length from equator to parallel 73° on meridian 29°.
  $L = 15 * ($Lt + $Lm + $Lf) / 73;
  if ($L <= $Lt) {
    # Measure length along the torrid segment, from the equator
    $xV = Interpolate ($L, $Lt, $xJe, $xJt);
    $yV = Interpolate ($L, $Lt, $yJe, $yJt);
  } else {
    # Measure length along the middle segment, from the torrid joint
    $L = $L - $Lt;
    $xV = Interpolate ($L, $Lm, $xJt, $xJf);
    $yV = Interpolate ($L, $Lm, $yJt, $yJf);
  }
  # Point C is the center of circular arc for parallel 15° with ends at points D and V, and,
  # therefore, it is equidistant from both. Radius, R = CD = CV. Thus:
  # $R^2 = ($xD - $xC)^2 + ($yD - $yC)^2 = ($xV - $xC)^2 + ($yV - $yC)^2
  # Point C is also on line MD, which has angle 30° with horizontal. M = (0 mm, 0 mm).
  # Thus, $yC / $xC = tan(deg2rad(30)) = 1 / sqrt(3) ; letting $k = sqrt(3), last equation is
  # equivalent to $xC = $k * $yC. Replacing this in the first equation and solving for $yC,
  # yields:
  $k = sqrt(3);
  $yC = ($xV * $xV + $yV  * $yV - $xD * $xD - $yD * $yD) /
        (2 * ($k * $xV + $yV  - $k * $xD - $yD ) );
  $xC = $k * $yC;
  $R = Length ($xC, $yC, $xD, $yD);

  # Return values needed by main program
  return ($sin60, $cos60, $MGcos30, $xA, $yA, $xB, $yB, $xC, $yC, $xD, $yD, $xE, $yE,
      $xF, $yF, $xG, $yG, $xM, $yM, $xT, $yT, $AG, $AB, $BD, $GF, $BDE, $GFE, $R,
      $DeltaMEq);
} # End of sub Preliminary

sub Equator {
  # Sub calculates equatorial point for a meridian, and returns ($xJe, $yJe).
  # Input is the wanted meridian, $m, and the following values calculated in sub Preliminary:
  # $xE, $yE, $xF, $yF, $xG, $AB, $GF, $DeltaMEq
  use Math::Trig;
  my ($m,  $xE, $yE, $xF, $yF, $xG, $AB, $GF, $DeltaMEq) = @_;  # Input arguments
  my ($xJe, $yJe);  # Values to be returned
  my ($L);  # Variable used just within this sub

  # Calculate point Je, the Intersection of meridian with equator, as in zone (d)
  $L = $DeltaMEq * $m;
  if ($L <= $GF) {
    $xJe = $xG;
    $yJe = $L
  } else {
    # Past point F; find point on line FE, a distance L from point G, along equator.
    # Length FE = length AB
   $L = $L - $GF;    # Part of length on segment FE
    $xJe = Interpolate ($L, $AB, $xF, $xE);
    $yJe = Interpolate ($L, $AB, $yF, $yE);
  }
  return ($xJe, $yJe);
}  # End sub Equator

sub Joints {
  # Sub calculates equatorial, torrid and frigid joints for given meridian, and lengths of
  # middle segments. Returns are array: ($xJe, $yJe, $xJt, $yJt, $xJf, $yJf, $Lt, $Lm).
  # $xJe and $yJe are calculated by calling sub Equator.
  # Input is the wanted meridian, $m, and the following values calculated in sub Preliminary:
  # $xA, $xE, $yE, $xF, $yF, $xG, $AB, $GF, $DeltaMEq
  use Math::Trig;
  my ($m, $xA, @Prelims) = @_;  # Input arguments
  # Parse the input arguments
  my ($xE, $yE, $xF, $yF, $xG, $AB, $GF, $DeltaMEq) = @Prelims ;

  my ($xJe, $yJe, $xJt, $yJt, $xJf, $yJf, $Lt, $Lm);  # Values to be returned
  my ($L);  # Variable just within this sub
  
  # Calculate point Je, the Intersection of meridian with equator
  ($xJe, $yJe) = Equator ($m, @Prelims);

  # Calculate torrid joint, Jt, the intersection of line of angle ($m/3) starting at point Je
  # with line of angle (2/3 * $m) starting at point M = (0 mm, 0 mm)
  ($xJt, $yJt) = LineIntersection (0, 0, 2*$m/3, $xJe, $yJe, $m/3);

  # Calculate frigid joint, Jf, the intersection of line of angle ($m) starting at point A
  # with line of angle (2/3 * $m) starting at point M. Point A = ($xA mm, 0 mm).
  ($xJf, $yJf) = LineIntersection ($xA, 0, $m, 0, 0, 2*$m/3);

  # Calculate lengths of torrid segment, $Lt = Je to Jt, and of middle segment, $Lm = Jt to Jf
  $Lt = Length ($xJe, $yJe, $xJt, $yJt);
  $Lm = Length ($xJt, $yJt, $xJf, $yJf);

    return ($xJe, $yJe, $xJt, $yJt, $xJf, $yJf, $Lt, $Lm);
} # End sub Joints

sub Parallel73 {
  # Sub calculates parallel 73° for a meridian, and length from that point to the frigid joint.
  # Note: if the point is on the middle segment, the length, Lf, to the frigid joint is given as
  # a negative number; this only happens for some of the meridians between 44° and 45°.
  # Returns are ($xP73, $yP73, $Lf).
  # Input is the wanted meridian, $m; $xA, $xT, and $yT, calculated in sub Preliminary;
  # $xJf, and $yJf, the frigid joint, calculated in sub Joints.
  use Math::Trig;
  my ($m, $xA, $xT, $yT, $xJf, $yJf) = @_;  # Input arguments
  my ($xP73, $yP73, $Lf);  # Values to be returned
  my ($x, $y);  # Values used only in this sub
  # Calculate point P73 = ($m, 73°) and length $Lf = distance from Jf to P73 (negative if
  # on middle segment).
  if ($m <= 30) {
    # Circular arc portion:
    # Radius to circular arc of 73° = 15° x 104mm/° + 2° x 100 mm/° = 1760 mm.
    $xP73 = $xA + 1760 * cos (deg2rad($m));
    $yP73 = 1760 * sin (deg2rad($m));
    # Calculate length $Lf = distance from point Jf to point P73
    $Lf = Length ($xJf, $yJf, $xP73, $yP73);
  } else {
    # Straight portion of parallel 73°. Calculate point P73, at the intersection of line UT
    # (angled -60° with the horizontal) with frigid segment of meridian $m, which is
    # angled +$m ° and passes through point . Point U = (30°, 73°) was
    # used to calculate point T, in sub Preliminary.
    ($xP73, $yP73) = LineIntersection($xT, $yT, -60, $xJf, $yJf, $m);

    # Calculate length $Lf, from point Jf to point P73
    $Lf = Length ($xJf, $yJf, $xP73, $yP73);
    if ($m > 44) {
      # Point P73 is on middle meridian segment for some of these meridians; check if it is.
      # Calculate intersection of line UT with middle segment, angled +(2/3*$m)°.
      ($x, $y) = LineIntersection ($xT, $yT, -60, $xJf, $yJf, (2/3*$m) );
      if ($x > $xP73) {
        # Correct intersection is on middle segment; correct point and length
        $xP73 = $x;
        $yP73 = $y;
        $Lf = - Length ($xJf, $yJf, $xP73, $yP73);  # Recalculating length and making it negative
      }  # End of correction
    }  # End of checking if it is on middle segment
  }
  return ($xP73, $yP73, $Lf);
}  # End sub Parallel73

sub MPtoXY {
  # Sub converts half-octant meridian,parallel to x,y coordinates.
  # Arguments are meridian, parallel, and array output by sub Preliminary not including
  # its first 3 values.
  # Sub returns (x,y).
  use Math::Trig;
  my ($m, $p, @Prelims) = @_;  # Input arguments
  # Parse the input arguments
  my ($xA, $yA, $xB, $yB, $xC, $yC, $xD, $yD, $xE, $yE, $xF, $yF, $xG, $yG,
      $xM, $yM, $xT, $yT, $AG, $AB, $BD, $GF, $BDE, $GFE, $R, $DeltaMEq) = @Prelims ;
  my ($x, $y);  # Variables to be returned

  # Extra variables used in this sub
  my ($L, $xP73, $yP73, $xP75, $yP75, $xJe, $yJe, $xJt, $yJt, $xJf, $yJf, $f73, $f75,
      $Lt, $Lm, $Lf, $L73, $xPm, $yPm, $flag);

  if ($m == 0) {  # Zones (a) and (b) on the center line of octant, on the base of
    # scaffold half-triangle
    $y = 0;
    if ($p >= 75) {  # Zone (a) – frigid center line
      # Parallel spacing is 104 mm/° from 75° to 90° of latitude, measured from point A (pole)
      $x = $xA + (90 - $p) * 104;

    } else {  # Zone(b) – torrid/temperate center line
      # Parallel spacing is 100 mm/° from 0° to 75° of latitude; measure from equator, that is
      # from point G.
      $x = $xG - $p * 100;
    }

  } elsif ($p >= 75) {  # Zone (c) – polar region with circular parallels spaced 104 mm/°
    # Meridian $m starts at point A and makes angle $m (in degrees) with line AG
      $L = 104 * (90 - $p);
      $x = $xA + $L * cos ( deg2rad($m) );
      $y = $L * sin( deg2rad($m) );

  } elsif ($p == 0) {  # Zone (d) – equator
    ($x, $y) = Equator ($m, $xE, $yE, $xF, $yF, $xG, $AB, $GF, $DeltaMEq);

  } elsif ($p >= 73 && $m <= 30) {  # Zone (e) – frigid region with circular parallels
    # spaced 100 mm/° between 73° and 75° of latitude; meridian $m starts at point A
    # and makes angle $m with line AG.
    # Length from A to parallel 75° = 1560 mm = 104 mm/° x (90° - 75°).
    $L = 1560 + (75 - $p) * 100;
    $x = $xA + $L * cos ( deg2rad($m) );
    $y = $L * sin ( deg2rad($m) );

  } elsif ($m == 45) {  # Outer boundary of octant, zones (f), (g), and (h)
    if ($p <= 15) {  # Zone (f) – torrid zone of outer boundary, that is, along line ED
      # E = 0° and D = 15° of latitude. Parallels are equally spaced within this zone.
      $x = Interpolate ($p, 15, $xE, $xD);
      $y = Interpolate ($p, 15, $yE, $yD);

    } elsif ($p <= 73) {  # Zone (g) – temperate zone of outer boundary, that is, along DT.
      # D = 15°; T = 73°. Parallels are equally spaced within this zone. 73° - 15° = 58°
      $L = $p - 15;
      $x = Interpolate ($L, 58, $xD, $xT);
      $y = Interpolate ($L, 58, $yD, $yT);

    } else {  # Zone (h) – frigid supple zone of outer boundary
      # Calculate point P75 = (45 °, 75°), point at parallel 75° on this meridian
      # Length from A to parallel 75° = 1560 mm = 104 mm/° x (90° - 75°).
      $xP75 = $xA + 1560 * cos (deg2rad(45));
      $yP75 = 1560 * sin (deg2rad(45));

      # Calculate length $Lf = parallel 73 (which is point T) to frigid joint (point B)
      $Lf = Length ($xT, $yT, $xB, $yB);
      # Calculate length from $Lf75 = distance from frigid joint (point B) to point P75
      $Lf75 = Length ($xB, $yB, $xP75, $yP75);
      # Length from P75 to P73 covers 2°
      $L = (75 - $p) * ($Lf75 + $Lf) / 2;  # Distance from parallel 75° to parallel p°
      if ($L <= $Lf75) {
        # Wanted latitude is on frigid segment, parallel 75° (P75) to B
        $x = Interpolate ($L, $Lf75, $xP75, $xB);
        $y = Interpolate ($L, $Lf75, $yP75, $yB);
      } else {
        # Wanted latitude is on segment B to T
        $L = $L - $Lf75;
        $x = Interpolate ($L, $Lf, $xB, $xP73);
        $y = Interpolate ($L, $Lf, $yB, $yP73);
      }
    }  # End of zones (f), (g), and (h); more specifically, end of zone (h)
  } else {  # Zones (i), (j), (k), and (l) which require more complicated calculations
    # Need to calculate meridian joints and segment lengths for this meridian.
    ($xJe, $yJe, $xJt, $yJt, $xJf, $yJf, $Lt, $Lm) =
        Joints ($m, $xA, $xE, $yE, $xF, $yF, $xG, $AB, $GF, $DeltaMEq);

    # Calculate point P73 = ( $m, 73°), point at latitude 73° on this meridian and distance
    # from that point to frigid joint, $Lf. These may later be modified for zones (j), (k) and (l).
    ($xP73, $yP73, $Lf) = Parallel73 ($m, $xA, $xT, $yT, $xJf, $yJf);

    if ($m <= 29) {  # Zone (i) – torrid and temperate areas of central two-thirds of octant
      # Parallels are equally spaced between the equator and latitude 73° in this zone.
      # Both torrid and frigid joints are at latitudes lower than 73° in this region.
      # Calculate length from equator to point ($m, $p), along this meridian $m.
      $L = $p * ($Lt + $Lm + $Lf) / 73;
      if ($L <= $Lt) {
        # Measure length along the torrid segment, from the equator
        $x = Interpolate ($L, $Lt, $xJe, $xJt);
        $y = Interpolate ($L, $Lt, $yJe, $yJt);
      } elsif ($L <= ($Lt + $Lm)) {
        # Measure length along the middle segment, from the torrid joint
        $L = $L - $Lt;
        $x = Interpolate ($L, $Lm, $xJt, $xJf);
        $y = Interpolate ($L, $Lm, $yJt, $yJf);
      } else {
        # Measure length along the frigid segment
        $L = $L - $Lt - $Lm;
        $x = Interpolate ($L, $Lf, $xJf, $xP73);
        $y = Interpolate ($L, $Lf, $yJf, $yP73);
      }    # end of area (i)

    } else {  # Supple zones (j), (k), and (l): 29° < $m < 45° and 0° < $p < 73

      if ($p >= 73) {  # Zone (j) – frigid supple zone
        # Calculate point P75 = ($m °, 75°), point at parallel 75° on this meridian
        # Length from A to parallel 75° = 1560 mm = 104 mm/° x (90° - 75°).

        $xP75 = $xA + 1560 * cos (deg2rad($m));
        $yP75 = 1560 * sin (deg2rad($m));
        # Calculate length from $Lf75 = distance from frigid joint, Jf, to point P75
        $Lf75 = Length ($xJf, $yJf, $xP75, $yP75);
        # Length from P75 to P73 covers 2°; remember that Lf, from P73 to Jf is sometimes
        # negative for a few meridians between 44° and 45°.
        $L = (75 - $p) * ($Lf75 - $Lf) / 2;  # Distance from parallel 75° to parallel p°
        if ($L <= $Lf75) {
          # Wanted latitude is on frigid segment
          $x = Interpolate ($L, $Lf75, $xP75, $xJf);
          $y = Interpolate ($L, $Lf75, $yP75, $yJf);
        } else {
          # Wanted latitude is on middle segment
          $L = $L - $Lf75;
          $x = Interpolate ($L, -$Lf, $xJf, $xP73);
          $y = Interpolate ($L, -$Lf, $yJf, $yP73);
        }

      } else {  # Zones (k) and (l)
        # Calculate point P15 = (m, 15°), that is, point on this meridian at latitude 15°, which
        # is at intersection of meridian with circular arc of center C and radius R. Also
        # calculate length L15 = distance from equator (Je) to P15.
        # Try middle segment first, since most, if not all, parallel 15° points are in this segment
        ($flag, $xP15, $yP15) = CircleLineIntersection ($xC, $yC, $R, $xJt, $yJt, $xJf, $yJf);
        if ($flag == 1) {    # Found the intersection point in middle segment
          $L15 = $Lt + Length ($xJt, $yJt, $xP15, $yP15);
        } else {    # Intersection point is in torrid segment
          ($flag, $xP15, $yP15) = CircleLineIntersection ($xC, $yC, $R, $xJe, $yJe, $xJt, $yJt);
          if ($flag==0) {    # Hmmm... no intersection!
            die " No line-circular arc intersection for M $m, at parallel 15! Terminating.\n";
          }
          $L15 = $Lt - Length ($xJt, $yJt, $xP15, $yP15);
        }

        if ($p <= 15) {  # Zone (k) – torrid supple zone
          # Parallels equally spaced between equator and 15°
          $L = $p * $L15 / 15;
          if ($L <= $Lt) {  # Point is in torrid segment
            $x = Interpolate ($L, $Lt, $xJe, $xJt);
            $y = Interpolate ($L, $Lt, $yJe, $yJt);
          } else {  # Point is in middle segment
            $L = $L - $Lt;
            $x = Interpolate ($L, $Lm, $xJt, $xJf);
            $y = Interpolate ($L, $Lm, $yJt, $yJf);
          }

        } else {  # Zone (l) – middle supple zone
          # Parallels equally spaced between 15° and 73°.
          # Will measure from the equator. ($Lt+$Lm+$Lf) = equator to P73. 58° = 73° - 15°
          $L = $L15 + ($p - 15) * (($Lt + $Lm + $Lf) - $L15) / 58;
          if ($L <= $Lt) {  # On torrid segment
            $x = Interpolate ($L, $Lt, $xJe, $xJt);
            $y = Interpolate ($L, $Lt, $yJe, $yJt);
          } elsif ($L <= $Lt + $Lm) {  # On middle segment
            $L = $L - $Lt;
            $x = Interpolate ($L, $Lm, $xJt, $xJf);
            $y = Interpolate ($L, $Lm, $yJt, $yJf);
          } else {  # On frigid segment
            $L = $L - $Lt - $Lm;
            $x = Interpolate ($L, $Lf, $xJf, $xP73);
            $y = Interpolate ($L, $Lf, $yJf, $yP73);
          }

        } # end zones (k) and (l)
      } # end zones (j), (k), and (l)
    } # end zones (i), (j), (k), and (l)
  } # end all zones
  return ($x, $y);
} # End of sub MPtoXY

sub LineIntersection {  # Written 2010-02-28; modified 2010-11-28
# Subroutine/function to calculate coordinates of point of intersection of two lines which
# are given by a point on the line and the line's slope angle in degrees.
#
# 2010-11-28 – Modified to assume that the lines do intersect, neither is either horizontal
#  or vertical, the arguments are the correct number and are all defined, and the
#  angles are within [-180,180].
#  Unlike on the previous version, this one has no checks and doesn't return a flag.
#
# Return is an array of two values, the x and y coordinates of the point of intersection.
#
# Arguments should be 6, in this order:
#  x and y coordinates of point of first line; slope of first line in degrees;
#  x and y coordinates of point of second line; slope of second line in degrees;
#
# Equations used are from: slope of line = tangent angle = delta-y / delta-x, and the fact
#  that intersection point x,y is on both lines.
  use Math::Trig;
  my ($nArguments,$xp,$yp,$m1,$m2);
  $nArguments=@_ ;
  my ($x1,$y1,$angle1,$x2,$y2,$angle2) = @_ ;

  $m1 = tan(deg2rad($angle1));
  $m2 = tan(deg2rad($angle2));
  $xp = ($m1 * $x1 - $m2 * $x2 - $y1 + $y2) / ($m1 - $m2);
  $yp = $m1 * $xp - $m1 * $x1 + $y1;
  return ($xp,$yp);
} # End of sub LineIntersection

sub Length {
  # Input are x1,y1,x2,y2
  my ($x1,$y1,$x2,$y2) = @_;
  return sqrt( ($x1-$x2)**2 + ($y1-$y2)**2);
} # End of sub Length

sub Interpolate {
# Inputs are 4: length wanted, of total-segment-length, start, end;
# Total-segment-length is different from (end - start); end and start may be x-coordinates,
# or y-coordinates, while length takes into account the other coordinates.
# (End - Start ) / Length = (Wanted - Start) / NewLength
# Returns single value: Wanted.
  my ($NewLength, $Length, $Start, $End) = @_;
  my ($Wanted);
  $Wanted = $Start + ($End - $Start) * $NewLength / $Length;
  $Skip = "YES";
  unless ($Skip) {  # Option to skip printing arguments
    foreach $i ($NewLength, $Length, $Start, $End, $Wanted) {printf "\t%.5f", $i;}
    print "\n";
  } # End of skipping printing arguments and result
  return $Wanted;
}  # End of sub Interpolate

sub CircleLineIntersection {
  # Subroutine to calculate intersection of circle with line segment. Equations from
  # http://local.wasp.uwa.edu.au/~pbourke/geometry/sphereline/
  # Arguments are 7, in the following order:
  # Circle given as x-center, y-center, radius; line segment given as (x1,y1), (x2,y2).
  # If line segment does not intersect circle, return is 0; else, return is 1,x,y of
  # point of intersection; it is assumed that circle only intersects line segment at one
  # point. If you want a subroutine for other purposes, read that website.
  my ($n);
  $n = @_;
  if ( $n != 7) {
    print "Sub CircleLineIntersection requires 7 arguments but got $n.\n";
    return 0;
  }
  my ($xc,$yc,$r,$x1,$y1,$x2,$y2) = @_;
  my ($u1,$u2,$a,$b,$c,$d,$x,$y);
  # Check if there is a point of intersection
  $a = ($x2-$x1)**2 + ($y2-$y1)**2;
  $b = 2 * ( ($x2-$x1) * ($x1-$xc) + ($y2-$y1) * ($y1-$yc) );
  $c = $xc**2 + $yc**2 + $x1**2 + $y1**2 - 2 * ($xc*$x1 + $yc*$y1) - $r**2;
  $d = $b**2 - 4*$a*$c;	# Determinant
  if ($a == 0) {
    # print "In sub CircleLineIntersection: line given is just one point!\n";
    return 0;
  }elsif ($d < 0) {
    # Determinant is negative: circle does not intersect the line, much less the segment
    # print "In sub CircleLineIntersection: line doesn't intersect circle.\n";
    return 0;
  }
  # $u1 and $u2 are the roots to a quadratic equation
  $u1 = (-$b + sqrt($d) ) / (2*$a);	# + of +/- of the solution to the quadratic equation
  $u2 = (-$b - sqrt($d) ) / (2*$a);	# - of +/- of the solution to the quadratic equation

  # Check if there is an intersection and if it is within the line segment (not only the line)
  # If $u1=$u2, line is tangent to the circle; if $u1 != $u2, line intersects circle at two
  # points; however, point or points of intersection are within the line segment only if
  # the root is within interval [0,1].
  if (0 <= $u1 && $u1 <= 1) {  # This root is on the line segment; use it
    $x = $x1 + $u1 * ($x2 - $x1);
    $y = $y1 + $u1 * ($y2 - $y1);
    return 1,$x,$y;
  } elsif (0 <= $u2 && $u2 <= 1) {
    # 1st root was not on line segment but 2nd one is; use it
    $x = $x1 + $u2 * ($x2 - $x1);
    $y = $y1 + $u2 * ($y2 - $y1);
    return 1,$x,$y;
  } else {  # neither root is on line segment
    # print "In sub CircleLineIntersection: line segment doesn't intersect circle.\n";
    return 0;
  }
}  # End of sub CircleLineIntersection

# -  -  -  -  -  -  -  -  -    SUBROUTINES For Coordinate conversion   -  -  -  -  -  -  -  -  -  -

sub LLtoMP {
  # Arguments are real world longitude and latitude for one point, in decimal degrees.
  # West longitudes and south latitudes have negative values.
  # Returns corresponding meridian ($m) and parallel ($p) in MJ's template half-octant,
  # sign for meridian (-1 for western half octant and +1 for eastern one), and octant
  # number. Returned values of $m and $p are always positive.

  my ($Long, $Lat) = @_ ;  # Input values

  # $m and $p are the meridian and parallel numbers in template half-octant setting;
  # $Octant is the M-map octant of the real point; $Sign is for east or west side of
  # template octant;
  my ($m, $p, $Sign, $Octant);  # Values to be returned

  # @South are southern octants corresponding to northern octants 1, 2, 3 and 4; the 0
  # is just a place holder to facilitate correspondence.
  my (@South) = (0,6,7,8,5);  # Variables used only in this sub

  # Determine the correct octant; Octant 1 is +160° to -110°; octant 4 is 70° to 160°
  $Octant = int ( ($Long + 200) / 90 ) + 1;
  # Make longitude fit within template half-octant, and determine if y value should
  # be positive or negative.
  $m = ( ($Long + 200) - (90*($Octant - 1))) - 45;
  if ($m < 0) {
    $Sign = -1;
    $m = -$m;
  } else {
    $Sign = 1;
  }
  # Fix the octant number, if necessary
  if ($Octant == 5) { $Octant = 1; }
  if ($Lat < 0) {
    $Octant = $South [$Octant];
    $p = -$Lat;
  } else {
    $p = $Lat;
  }
  return ($m, $p, $Sign, $Octant);
}  # End sub LLtoMP

sub MJtoMM {
# Subroutine to convert (that is, do coordinate transformation of) x and y coordinates
# from Mary Jo's (MJ) whole-octant coordinates* to Megamap's coordinates for any of the 91
# areas (which include Gene's template octant, and the standard position of the 8 octants).
#
# * Mary Jo's whole-octant coordinates are the same as the half-octant template's ones,
# except that the y-coordinate is negative on the western half; for the eastern half, the
# whole-octant coordinates are the same as in the half-octant.
# 
# Subroutine returns converted x and y coordinates.
#
# Arguments are:
# - x and y coordinates of point to convert. (y-coordinate should be positive for eastern
# half and negative for western half).
# - Third argument is the Octant to convert to:
#   - G – Gene's single-octant system, with y-axis on its left;
#   - 1, 2, 3 or 4 – convert to M-map coordinates, respectively to first, second, third or
#     fourth northern octant, from the left;
#   - 5, 6, 7 or 8 – convert to M-map coordinates, respectively to fourth, first, second or
#     third southern octant from the left.
#   - #we, #wv, #wt, #wm, #wp, #pv, #ep, #em, #ev, #et, #ev, #ee, where # is a number
#     from 1 to 8 – convert to M-map coordinates of area adjacent to the following side of
#     octant #:
#     we/ee = west/east-equatorial segment; wv/ev = across from west/east point E;
#     wt/et = west/east-torrid segment; wm/em = west/east-middle segment;
#     wp/ep = west/east-polar segment; wpv = across from polar vertex, point A.
#     These areas are used to "rotate" portions of octants to become adjacent to octants
#     from which they are split.
#     For example, to plot Antarctica joined in one piece plot:
#     octant7, 7pw (octant 6), 7pv (octant 5), 7pe (octant8).
#
# - $sin60, $cos60 – values calculated once, in sub Interpolate, to minimize computations.
#      ($sin60 = sin 60°, $cos60 = cos 60°).
#
# - In MJ's coordinates, point M is the origin, at (0,0), points M, A and G are on the positive
# x-axis, and point G is at (10000, 0).
# - In G's system, point M, L, J and P are on the positive y-axis, and point G is on the
# positive x-axis; in this system, point G is at coordinates (5000, 0).
# - From MJ's system to G's, there is a +60° rotation, and also a translation.
# - The M-map coordinate system is like G's system, except that the y-axis is 10000mm
# to the right, that is, the x-coordinates for the start octant are 10000mm smaller.
#
# I got the equations for rotation and translation from my pocketbook "The Universal
# Encyclopedia of Mathematics, with a Foreword by James R. Newman", ©1964 by
# George Allen and Unwin, Ltd.; translated from original German language edition,
# pages 152, 153.

  my ($nArgs, $xNew, $yNew);
  my ($x, $y, $Code, $sin60, $cos60) = @_ ;
  my (%Areas, $Area, $xUse, $yUse, @North, @xRt, @yRt, @cos, @sin, @xT, @yT);
  @Areas {qw( G 1 2 3 4 5 6 7 8
    1we 1wv 1wt 1wm 1wp 1pv 1ep 1et 1ev 1ee
    2we 2wv 2wt 2wp 2pv 2ep 2em 2et 2ev 2ee
    3we 3wv 3wt 3wm 3wp 3pv 3ep 3et 3ev 3ee
    4we 4wv 4wt 4wp 4pv 4ep 4em 4et 4ev 4ee
    5we 5wv 5wt 5wm 5wp 5pv 5ep 5em 5et 5ev 5ee
    6we 6wv 6wt 6wm 6wp 6pv 6ep 6em 6et 6ev 6ee
    7we 7wv 7wt 7wm 7wp 7pv 7ep 7et 7ev 7ee
    8we 8wv 8wt 8wp 8pv 8ep 8em 8et 8ev 8ee
    1em 2wm 3em 4wm 7em 8wm)} = (0 .. 90, 2, 1, 4, 3, 8, 7);
  # Note that the last line of @Areas, refer to octants in their standard Megamap positions;
  # e.g. 1em is the octant adjacent to middle segment of octant 1, which is octant 2 in its
  # standard position.
  if (not defined ($Areas{$Code} ) ) {
    print "Error converting to M-map coordinates; there is no area $Code!\n";
    $xNew = $x;
    $yNew = $y;
  } else {
    $Area = $Areas{$Code};

    # Arrays with values for each area:

    # On southern hemisphere octants, $xUse = 20000 - $x, while in northern octants
    # $xUse = $x. To automate, will use $North as a flag to use $x or (20000 - $x).
    @North=(1, 1,1,1,1,0,0,0,0, 0,0,1,1,1,1,1,1,0,0, 0,0,1,1,1,1,1,1,0,0,
      0,0,1,1,1,1,1,1,0,0, 0,0,1,1,1,1,1,1,0,0, 1,1,0,0,0,0,0,0,0,1,1,
      1,1,0,0,0,0,0,0,0,1,1, 1,1,0,0,0,0,0,0,1,1, 1,1,0,0,0,0,0,0,1,1);
    # @xRt and @yRt are translation coordinates of the point around which to rotate, that is,
    # the x-y origin for rotation.
    @xRt = (10000, 10000,10000,10000,10000,10000,10000,10000,10000,
      10000,10470,7775.93612,0,940,940,940,7775.93612,10470,10000,
      10000,10470,7775.93612,940,940,940,0,7775.93612,10470,10000,
      10000,10470,7775.93612,0,940,940,940,7775.93612,10470,10000,
      10000,10470,7775.93612,940,940,940,0,7775.93612,10470,10000,
      10000,9530,12224.06388,20000,19060,19060,19060,20000,12224.06388,9530,10000,
      10000,9530,12224.06388,20000,19060,19060,19060,20000,12224.06388,9530,10000,
      10000,9530,12224.06388,20000,19060,19060,19060,12224.06388,9530,10000,
      10000,9530,12224.06388,19060,19060,19060,20000,12224.06388,9530,10000);
    @yRt = (0, 0,0,0,0,0,0,0,0,
      -3205.37493,4959.43881,4489.43881,0,0,0,0,-4489.43881,-4959.43881,3205.37493,
      -3205.37493,4959.43881,4489.43881,0,0,0,0,-4489.43881,-4959.43881,3205.37493,
      -3205.37493,4959.43881,4489.43881,0,0,0,0,-4489.43881,-4959.43881,3205.37493,
      -3205.37493,4959.43881,4489.43881,0,0,0,0,-4489.43881,-4959.43881,3205.37493,
      -3205.37493,4959.43881,4489.43881,0,0,0,0,0,-4489.43881,-4959.43881,3205.37493,
      -3205.37493,4959.43881,4489.43881,0,0,0,0,0,-4489.43881,-4959.43881,3205.37493,
      -3205.37493,4959.43881,4489.43881,0,0,0,0,-4489.43881,-4959.43881,3205.37493,
      -3205.37493,4959.43881,4489.43881,0,0,0,0,-4489.43881,-4959.43881,3205.37493);
    # @cos and @sin are the cosines and sines of the rotation angle; all the angles are
    # multiples of 30°, so that the previously calculated values of $cos60 and $sin60 are
    # used, instead of recalculating each time.
    @cos = ($cos60, -$cos60,$cos60,-$cos60,$cos60,$cos60,-$cos60,$cos60,-$cos60,
      -$sin60,-$cos60,-$sin60,-1,-$sin60,$cos60,$sin60,0,-$cos60,0,
      0,$cos60,0,-$sin60,-$cos60,$sin60,1,$sin60,$cos60,$sin60,
      -$sin60,-$cos60,-$sin60,-1,-$sin60,$cos60,$sin60,0,-$cos60,0,
      0,$cos60,0,-$sin60,-$cos60,$sin60,1,$sin60,$cos60,$sin60,
      $sin60,$cos60,$sin60,1,$sin60,-$cos60,-$sin60,-$cos60,0,$cos60,0,
      0,-$cos60,0,$cos60,$sin60,$cos60,-$sin60,-1,-$sin60,-$cos60,-$sin60,
      $sin60,$cos60,$sin60,1,$sin60,-$cos60,-$sin60,0,$cos60,0,
      0,-$cos60,0,$sin60,$cos60,-$sin60,-1,-$sin60,-$cos60,-$sin60);
    @sin = ($sin60, $sin60,$sin60,$sin60,$sin60,$sin60,$sin60,$sin60,$sin60,
      $cos60,$sin60,$cos60,0,-$cos60,-$sin60,$cos60,1,$sin60,1,
      1,$sin60,1,$cos60,-$sin60,-$cos60,0,$cos60,$sin60,$cos60,
      $cos60,$sin60,$cos60,0,-$cos60,-$sin60,$cos60,1,$sin60,1,
      1,$sin60,1,$cos60,-$sin60,-$cos60,0,$cos60,$sin60,$cos60,
      $cos60,$sin60,$cos60,0,-$cos60,-$sin60,$cos60,$sin60,1,$sin60,1,
      1,$sin60,1,$sin60,$cos60,-$sin60,-$cos60,0,$cos60,$sin60,$cos60,
      $cos60,$sin60,$cos60,0,-$cos60,-$sin60,$cos60,1,$sin60,1,
      1,$sin60,1,$cos60,-$sin60,-$cos60,0,$cos60,$sin60,$cos60);
    # @xT and @yT are the coordinates to which to translate the origin, after the rotation
    @xT = (5000, -15000,-5000,5000,15000,15000,-15000,-5000,5000,
      -17775.93612,-19060,-17775.93612,-10000,-10470,
      -10470,-10470,-10000,-10470,-12224.06388,
      -7775.93612,-9530,-10000,-9530,-9530,
      -9530,-10000,-2224.06388,-940,-2224.06388,
      2224.06388,940,2224.06388,10000,9530,
      9530,9530,10000,9530,7775.93612,
      12224.06388,10470,10000,10470,10470,
      10470,10000,17775.93612,19060,17775.93612,
      12224.06388,10940,12224.06388,20000,19530,19530,
      19530,20000,20000,19530,17775.93612,
      -17775.93612,-19530,-20000,-20000,-19530,-19530,
      -19530,-20000,-12224.06388,-10940,-12224.06388,
      -7775.93612,-9060,-7775.93612,0,-470,
      -470,-470,0,-470,-2224.06388,
      2224.06388,470,0,470,470,
      470,0,7775.93612,9060,7775.93612);
    @yT = (0, 0,0,0,0,0,0,0,0,
      1602.68747,2886.75135,4170.81523,8660.25404,7846.19016,
      7846.19016,7846.19016,-318.62359,-2072.68747,-1602.68747,
      -1602.68747,-2072.68747,-318.62359,7846.19016,7846.19016,
      7846.19016,8660.25405,4170.81523,2886.75135,1602.68747,
      1602.68747,2886.75135,4170.81523,8660.25404,7846.19016,
      7846.19016,7846.19016,-318.62359,-2072.68747,-1602.68747,
      -1602.68747,-2072.68747,-318.62359,7846.19016,7846.19016,
      7846.19016,8660.25404,4170.81523,2886.75135,1602.68747,
      -1602.68747,-2886.75135,-4170.81523,-8660.25404,-7846.19016,-7846.19016,
      -7846.19016,-8660.25404,318.62359,2072.68747,1602.68747,
      1602.68747,2072.68747,318.62359,-8660.25404,-7846.19016,-7846.19016,
      -7846.19016,-8660.25404,-4170.81523,-2886.75135,-1602.68747,
      -1602.68747,-2886.75135,-4170.81523,-8660.25404,-7846.19016,
      -7846.19016,-7846.19016,318.62359,2072.68747,1602.68747,
      1602.68747,2072.68747,318.62359,-7846.19016,-7846.19016,
      -7846.19016,-8660.25404,-4170.81523,-2886.75135,-1602.68747);

    # Now for the actual calculations
    if ($North[$Area]) {$xUse = $x} else {$xUse = 20000 - $x}
    $xUse = $xUse - $xRt[$Area];
    $yUse = $y - $yRt[$Area];
    $xNew =$xUse * $cos[$Area] + $yUse * $sin[$Area] + $xT[$Area];
    $yNew = -$xUse * $sin[$Area] + $yUse * $cos[$Area] + $yT[$Area];
  }
  return ($xNew, $yNew);
}  # End of sub MJtoMM, which converts coordinates to one of 91 areas on Megamap

sub MJtoMap {
  # Sub to convert template octant coordinates to megamap coordinates, in any of the
  # layouts, including M, W, right-side up butterfly and upside-down butterfly shapes, with
  # any octant right of center. It also converts to octants placed around other octants,
  # intended to be used as extensions (also called "tabs"), by calling "sub EpiArea".
  # Requires eleven (11) arguments:
  # Nine (8) Arguments:
  #  - x, y: coordinates of point to be converted
  #  - Area: string. First character is the number of the octant against which to plot the
  #     octant to which the point belongs. The string may be only this single character or
  #     it may include two more characters:
  #     (in, we, wv, wt, wm, wp, pv, ep, em, ev, et, ev, ee) indicating area adjacent to the
  #     following side of template octant.
  #     in = point is in the base template octant (this code can be ommitted);
  #     we/ee = west/east-equatorial segment; wv/ev = across from west/east point E;
  #     wt/et = west/east-torrid segment; wm/em = west/east-middle segment;
  #     wp/ep = west/east-polar segment; wpv = across from polar vertex, point A.
  #     These areas are used to "rotate" portions of octants to become adjacent to octants
  #     from which they are split.
  #  - Number of octant flat against east side of center line of layout.
  #  - Code for layout: "M" for megamap (M or W layout), or "B" for butterfly layout (either
  #    turned up or turned down);
  #  - $sin60, $cos60, $MGcos30, $xA, $xE, $yE – Values calculated in sub Preliminary,
  #     so that they don't have to be calculated each time; these are only passed to sub
  #     EpiArea.
  # Using point M at (0,0), point A has y value of 0, southern point M is at (20000,0) and
  # points on western half of octants have negative y coordinate.
  #
  my ($xGiven, $yGiven, $Area, $OctEastCenter, $Layout, $sin60, $cos60, $MGcos30,
    $xA, $xE, $yE) = @_;
  my (@Pair, @H20K, @HS, @Sin, @Cos, @xR, @xT, @yT, %LayoutPlus);
  my ($x, $y, $EC, $Octant, $Oct, $xNew, $yNew);
  # Arrays
  @Pair[1..8] = (1, 2, 3, 4, 4, 1, 2, 3);  # Pairing of southern octants to northern ones
  # x-coordinates of southern octants are (20000 - x); @H20K and @HS is to handle that;
  # zero-th element is just a placeholder.
  @H20K = (0,  0, 0, 0, 0,  20000, 20000, 20000, 20000); 
  @HS = (0, 1, 1, 1, 1,  -1, -1, -1, -1);
  # Sin and Cos depend on octant being converted, and on octant east of center and on
  #  Megamap (first 8) or Butterfly (last 8) layout.
  # Zero-th element of each row, and zero-th row are just placeholders.
  @Sin = ([0],
    [0, $sin60,$sin60,$sin60,$sin60,$sin60,$sin60,$sin60,$sin60,
      $sin60,$sin60,0,0,0,$sin60,$sin60,0],
    [0,$sin60,$sin60,$sin60,$sin60,$sin60,$sin60,$sin60,$sin60,
      0,$sin60,$sin60,0,0,0,$sin60,$sin60],
    [0, $sin60,$sin60,$sin60,$sin60,$sin60,$sin60,$sin60,$sin60,
      0,0,$sin60,$sin60,$sin60,0,0,$sin60],
    [0, $sin60,$sin60,$sin60,$sin60,$sin60,$sin60,$sin60,$sin60,
      $sin60,0,0,$sin60,$sin60,$sin60,0,0]);
  @Cos = ([0],
    [0, $cos60,-$cos60,$cos60,-$cos60,$cos60,-$cos60,$cos60,-$cos60,
      $cos60,-$cos60,-1,1,-1,-$cos60,$cos60,1],
    [0, -$cos60,$cos60,-$cos60,$cos60,-$cos60,$cos60,-$cos60,$cos60,
      1,$cos60,-$cos60,-1,1,-1,-$cos60,$cos60],
    [0, $cos60,-$cos60,$cos60,-$cos60,$cos60,-$cos60,$cos60,-$cos60,
      -1,1,$cos60,-$cos60,$cos60,1,-1,-$cos60],
    [0, -$cos60,$cos60,-$cos60,$cos60,-$cos60,$cos60,-$cos60,$cos60,
      -$cos60,-1,1,$cos60,-$cos60,$cos60,1,-1]);
  # Point for rotation is M = (0,0), G = (10000, 0) or M-south = (20000, 0); all have y=0;
  # It depends on octant east of center and on Megamap (first 8) or Butterfly (last 8) layout.
  # Zero-th element is just a placeholder.
  @xR = (0, 10000,10000,10000,10000,10000,10000,10000,10000,
      0,0,0,0,20000,20000,20000,20000);
  # Point to translate to, after rotation.
  # X-translation depends both on octant being converted, and on octant east of center and
  # on Megamap (first 8) or Butterfly (last 8) layout. Y-translation does not depend on octant
  # being converted.
  # Zero-th element of each row, and zero-th row are just placeholders.
  @xT = ([0],
    [0, 5000,-5000,-15000,15000, 15000,5000,-5000,-15000, 0,0,0,0, 0,0,0,0],
    [0, 15000,5000,-5000,-15000, -15000,15000,5000,-5000, 0,0,0,0, 0,0,0,0],
    [0, -15000,15000,5000,-5000, -5000,-15000,15000,5000, 0,0,0,0, 0,0,0,0],
    [0, -5000,-15000,15000,5000, 5000,-5000,-15000,15000, 0,0,0,0, 0,0,0,0]);
  @yT = (0, 0,0,0,0, 0,0,0,0, $MGcos30,$MGcos30,$MGcos30,$MGcos30,
    -$MGcos30,-$MGcos30,-$MGcos30,-$MGcos30);  # Same for all octants; varies center oct.
  @LayoutPlus{"M","B"} = (0,8); # To choose index for wanted layout
#print "\n\nIn MJtoMap\n\nPair\n@Pair\n\nH20K\n@H20K\n\nHS\n@HS\n";
#print "\nSin\n";
#foreach $i (1 .. 4) {
#foreach $j (0 .. 16) {print "$Sin[$i][$j] ";}
#print "\n";}
#print "\nCos\n";
#foreach $i (1 .. 4) {
#foreach $j (0 .. 16) {print "$Cos[$i][$j] ";}
#print "\n";}
#print "\nxT\n";
#foreach $i (1 .. 4) {
#foreach $j (0 .. 16) {print "$xT[$i][$j] ";}
#print "\n";}
#print "xR\n@xR\n\n";
#print "yT\n@yT\n\n";
#@AAA = keys (%LayoutFactor);
#@BBB = values (%LayoutFactor);
#print "LayoutFactor\n@AAA\n@BBB\n";
  # Now for the actual calculations
  # Place octant at correct position around a standard octant
  ($x, $y) = EpiArea ($xGiven, $yGiven, substr($Area."in",1,2), $sin60, $cos60,$xA,$xE,$yE);
  $Octant = substr($Area,0,1);  # octant number is first character in area code
  # Get indeces for arrays
  $Oct = $Pair[$Octant];  # southern octants mostly use same values as northern ones
  # Index for Butterfly layout is 8 more than that for Megamap (M or W shaped) layout
  $EC = $LayoutPlus{$Layout} + $OctEastCenter;
  # Adjust to northern or southern x-coordinate and translate to point of rotation; $Oct does
  # not have southern octants; thus, need to use $Octant. No y-displacement is needed.
  $x = $H20K[$Octant] + $HS[$Octant] * $x - $xR[$EC];
  # Rotate and do final translation
  $xNew = $x * $Cos[$Oct][$EC] + $y * $Sin[$Oct][$EC] + $xT[$Oct][$EC];
  $yNew = -$x * $Sin[$Oct][$EC] + $y * $Cos[$Oct][$EC] + $yT[$EC];
  return ($xNew, $yNew);
} # End of sub MJtoMap, which converts template to megamap coordinates

sub EpiArea {
  # Sub to convert template octant coordinates to coordinates as if this octant were adjacent
  # to the template octant. These coordinates are used to plot extensions ("tabs") to octants.
  # Examples: to be able to plot Antarctica in one piece instead of four or to plot Kamchatka
  # Peninsula attached to the octant with Russia.
  # (Calling it EpiArea, for being similar to the concept of epicycle).
  #
  # This sub does not take octant number into consideration, nor does it return megamap
  # coordinates. The coordinate system of the results is the same as the template octant
  # one, that is, MJ coordinates. Sub MJtoMap, which calls this sub, converts these
  # coordinates to Megamap.
  #
  # To understand what this sub does, imagine two template octants, with point M at the
  # origin of the set of axes, and point G at (10000, 0). This sub receives, as arguments,
  # the coordinates of a point on one of those octants. This octant is flipped, rotated and/or
  # translated it as necessary to be adjacent to the other one. Then the sub returns the
  # new coordinates of the point. The x-axis is still along line MG, and the origin is still at
  # point M of the octant that wasn't moved.
  #
  # Nine (8) Arguments:
  #   x, y: coordinates of point to be converted
  #   Area: Two-letter code (in, we, wv, wt, wm, wp, pv, ep, em, ev, et, ev, ee) area adjacent
  #     to the following side of template octant.
  #     in = no conversion; point is in the base template octant
  #     we/ee = west/east-equatorial segment; wv/ev = across from west/east point E;
  #     wt/et = west/east-torrid segment; wm/em = west/east-middle segment;
  #     wp/ep = west/east-polar segment; wpv = across from polar vertex, point A.
  #     These areas are used to "rotate" portions of octants to become adjacent to octants
  #     from which they are split.
  #
  #   $sin60, $cos60, $xA, $xE, $yE – Values calculated in sub Preliminary,
  #     so that they don't have to be calculated each time.
  # Using point M at (0,0), point A has y value of 0, southern point M is at (20000,0) and
  # points on western half of octants have negative y coordinate.
  my ($xGiven, $yGiven, $Area, $sin60, $cos60, $xA, $xE, $yE) = @_;
  my (%Areas, @H20K, @HS, @Sin, @Cos, @xR, @yR, @xT, @yT);
  my ($x, $y, $xES, $Z, $xNew, $yNew);
  $xES = 20000 - $xE;  # x value of point E on southern octant
  @Areas {qw( in we wv wt wm wp pv ep em et ev ee)} = (0..11);
  $Z = $Areas{$Area};  # zone (that is, area) wanted
  @H20K = (0,  20000, 20000, 0, 0, 0,  0,  0, 0, 0, 20000, 20000); 
  @HS = (1,  -1, -1, 1, 1, 1,  1,  1, 1, 1, -1, -1);
  @Sin = (0,  $cos60, 0, $cos60, $sin60, 1,  0,  -1, -$sin60, -$cos60, 0, -$cos60);
  @Cos = (1,  $sin60, 1, $sin60, $cos60, 0,  -1,  0, $cos60, $sin60, 1, $sin60);
  @xR = (0,  $xES, $xES, $xE, 0, $xA, $xA, $xA, 0, $xE, $xES, $xES);
  @yR = (0,  -$yE, $yE, $yE, 0, 0,  0,  0, 0, -$yE, -$yE, $yE);
  @xT = (0,  $xE, -$xE, -$xE, 0, $xA,  $xA,  $xA, 0, $xE, $xE, $xE);
  @yT = (0,  -$yE, -$yE, -$yE, 0, 0,  0,  0, 0, $yE, $yE, $yE);
#@AAA = keys (%Areas); @BBB = values (%Areas);
#print "In EpiArea\n\nAreas\n@AAA\n@BBB\n\nH20K\n@H20K\n\nHS\n@HS\n\n";
#print "Sin\n@Sin\n\nCos\n@Cos\n\nxR\n@xR\n\nyR\n@yR\n\nxT\n@xT\n\nyT\n@yT\n\n";
  # Placing origin at point of rotation
  $x = $H20K[$Z] + $HS[$Z] * $xGiven - $xR[$Z];
  $y = $yGiven - $yR[$Z];
  # Rotate and place origin at point M (0,0) of octant against which this one was rotated
  $xNew = $x * $Cos[$Z] + $y * $Sin[$Z] + $xT[$Z];
  $yNew = -$x * $Sin[$Z] + $y * $Cos[$Z] + $yT[$Z];
  return ($xNew, $yNew);
} # End of sub EpiArea, wich converts template coordinates to extensions/tabs

sub CheckArea {
  # Sub to check if the area code entered is a recognizable area code to be used with
  # sub MJtoMap.
  # One argument: area code.
  # Returns:
  #   1) corresponding octant number; if area was not recognized this value is the input area;
  #   2) 1 if code was "0" or wasn't recognized; 0 if it is an acceptable code.
  my ($Area) = @_ ;
  my (@Octants, $toTell, $Octant, $flag);
  $flag = 0;
  @Octants {qw(1 2 3 4 5 6 7 8
    1we 1wv 1wt 1wm 1wp 1pv 1ep 1et 1ev 1ee
    2we 2wv 2wt 2wp 2pv 2ep 2em 2et 2ev 2ee
    3we 3wv 3wt 3wm 3wp 3pv 3ep 3et 3ev 3ee
    4we 4wv 4wt 4wp 4pv 4ep 4em 4et 4ev 4ee
    5we 5wv 5wt 5wm 5wp 5pv 5ep 5em 5et 5ev 5ee
    6we 6wv 6wt 6wm 6wp 6pv 6ep 6em 6et 6ev 6ee
    7we 7wv 7wt 7wm 7wp 7pv 7ep 7et 7ev 7ee
    8we 8wv 8wt 8wp 8pv 8ep 8em 8et 8ev 8ee
    1em 2wm 3em 4wm 7em 8wm)} =
    (1 .. 8,
    6, 5, 4, 4, 4, 3, 2, 2, 7, 6,
    7, 6, 1, 1, 4, 3, 3, 3, 8, 7,
    8, 7, 2, 2, 2, 1, 4, 4, 5, 8,
    5, 8, 3, 3, 2, 1, 1, 1, 6, 5,
    4, 3, 8, 8, 8, 7, 6, 6, 6, 1, 4,
    1, 4, 5, 5, 5, 8, 7, 7, 7, 2, 1,
    2, 1, 6, 6, 6, 5, 8, 8, 3, 2,
    3, 2, 7, 7, 6, 5, 5, 5, 4, 3,
    2, 1, 4, 3, 8, 7);
  if ( not defined ($Octants{$Area} ) ) {
    $toTell = "\nError: I don't recognize area code \"$Area\"!\n";
    $toTell .= "Area code must be a digit from 1 to 8, or such digit followed by:\n";
    $toTell .= "pv (for polar vertex), or followed by e or w (for east, west), followed by ";
    $toTell .= "e, v, t, m or p (for equator, vertex, tropic, middle, or polar).\n";
    $toTell .= "Four examples: 5, 3pv, 2wm, 8ee.\n";
    print $toTell;
    $flag = 1;
    $Octant = $Area;
  } else {
    $Octant = $Octants{$Area};
  }
  return ($Octant, $flag);
} # End of sub CheckArea, which checks if area code is recognizable. 

sub CheckOctant {
  # Sub to convert a point given as (longitude, latitude) to template (meridian, parallel), and
  # to check if it is in a specific octant.
  # Notice that this is octant number, not area code; it should be within 1 to 8.
  # Arguments: Longitude, Latitude, expected octant
  # Returns: template meridian and parallel;
  #   sign: 1 for eatern half-octant or -1 for western octant;
  #   flag: 0 if in correct octant, or an octant number if not.
  my ($Long, $Lat, $WantedOctant) = @_ ;
  my ($m, $p, $Sign, $Octant, $flag);
  $flag = 0;
  ($m, $p, $Sign, $Octant) = LLtoMP ($Long, $Lat);
  if ($Octant != $WantedOctant) {
    if (($Lat >= 0 && $WantedOctant < 5) || ($Lat <= 0 && $WantedOctant > 4) ) {
      # Point is in the correct norther or southern hemisphere
      @Pairs = (0,6,7,8,5,4,1,2,3);
      @WestLong = (0,160,-110,-20,70,70,160,-110,-20);
      @EastLong = (0,-110,-20,70,160,160,-110,-20,70);
      if ($p == 0 && $Octant == $Pairs[$WantedOctant] ) {
        $Octant = $WantedOctant; # On boundary with its southern or northern octant
      } elsif ($p == 90) { # Checking the poles
        $Octant = $WantedOctant;
      } elsif ($m == 45) { # Check eastern and western boundaries
        if ($Long == $WestLong[$WantedOctant]) {
          $Octant = $WantedOctant;
          $Sign = -1;
        } elsif ($Long == $EastLong[$WantedOctant]) {
          $Octant = $WantedOctant;
          $Sign = 1;
        }
      }  # End of if $p == 0 or $p == 45
    }  # End of checking if it is on the correct hemisphere
    # If none of the above fixed the octant, then this point is not on the wanted octant,
    # not even right on its boundary.
    if ($Octant != $WantedOctant) {
      $flag = $Octant;
    }
  } # End of correcting octant number
  return ($m, $p, $Sign, $flag);
} # End of sub CheckOctant, which converts long-lat to m-p and checks if it is in 
   # expected octant

# -  -  -  -  -  -  -  -  -       End SUBROUTINES         -  -  -  -  -  -  -  -  -  -  -  -  -