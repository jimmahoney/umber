#!/var/www/cs/bin/perl
###############################
#
# lookup.cgi
#
#   Creates a webpage of ID photos and other info pulled from
#   the LDAP directory server for various groups of people on campus.
#
# Usage:
#
#   Visiting http://cs.marlboro.edu/on-campus/people/lookup.cgi
#   with a browser shows a dialog and explanation.

#   Or options may be passed in the url, e.g. 
#   http://cs.marlboro.edu/on-campus/people/lookup.cgi?key=value&key=value
#
#      key       default                notes
#      ---       -------                -----
#      user(s)    ''                  comma separated list of usernames
#                                      or all first/last names that match
#      title      folks@marlboro      Use %20 for space character
#      emails     1                   0 => don't display link with all emails
#      sort       last                last, first, user
#      status     ''                  any of 
#                                      faculty, staff, student, alumni, guest,
#                                      current       = faculty,staff,student
#                                      everyone|all  = all in database
#                                      or comma-separated list
#      columns    6                   number of columns in table
#      rows       1000                (max) number of rows in table  
#      page       1                   show n'th page of multiple page result
#      size       normal | small      if small, 2x2 image table & small text
#      imgwidth  100                  width of images in pixels (100 x 125)
#      details    1                   0 => name only; no username/phone
#      bold       1                   0 => names not bold 
#      background white               name or e.g. ccc or 0c0c0c for hex code
#      spacing    10  (4 if 'small')  table cell spacing, in pixels
#      ldap_data  0                   1 => show all ldap data (debugging)
#      class      0                   1 => show class standing, e.g. 'sophomore 1'
#
#   Or it may be run from the command line to generate a static page, e.g.
#      $ ./lookup.cgi 'status=alumni,guest' > somefolks.html
#
#   If 'status' is set then entire categories of people are shown.  In that case,
#      * "emails" will be turned off - too many names.
#      * the default title is modified to something like faculty@marlboro
#
# Author
#   Jim Mahoney (mahoney@marlboro.edu)
#
# History
#  v 0.1  - original 9/1/2003
#  v 0.2  - merged with everyone.cgi
#  v 0.21 - tweaking options and layout
#  v 0.3  - changed status to use gidNumber rather than eduMarlboroStatus;
#           Jared says the other fields aren't current.
#           (note: faculty and staff have same gidNumber)
#  v 0.4  - 1/21/2005; edited home page look
#  v 0.5  - 1/10/2006; changed all .cgimp to .cgi
#           and changed Net::LDAPS to Net::LDAP
#           (any of the Net::LDAP's are crashing under my mod_perl)
#  v 0.6  - 1/20/2006  bruteforce sequential searches to avoid 25 person limit
#  v 0.7  - 1/22/2007  multiple small pages for handhelds (?size=small)
#  v 0.8  - 9/2007     more options and pictures from ./photos/<username>.jpg
#  v 0.9  - 10/2007    special pics for authorized folks
#  v 1.1  - 9/2008     changed static display page; added 'class' option
#  v 1.2  - 2/2010     ldap photo directory chnaged
#
#########################

my $modified_date = 'Feb 4 2010';

use warnings;
use strict;
use CGI qw(:standard);
use CGI::Carp qw(fatalsToBrowser);
require '.secure/access.pl';

# -- definitions and defaults --
## as of Sep 2 2008, photos are by username
# my $photo_directory = 'https://nook.marlboro.edu/directory_files/photos/';
## changed on Feb 4 2010 : to /id/photo/username (no .jpeg)
my $photo_directory = 'https://nook.marlboro.edu/id/photo/';
my $local_photo_folder = 'photos/';
my $local_photo2_folder = 'photos2/';

use Net::LDAP;
my $ldap_url = "ldaps://ldap.marlboro.edu";
my $ldap_dn  = "ou=people,dc=marlboro,dc=edu";

my $default_users           = '';
my $default_title           = 'folks@marlboro';
my $default_columns         = 5;
my $default_do_all_emails   = 1;
my $default_sort_order      = 'last';
my $default_status          = '';
my $default_size            = 'normal';
my $default_page            = 1;
my $default_rows            = 1000;  # i.e. everything on one page
my $small_rows              = 2;     # default rows if size='small'
my $small_columns           = 2;     # default cols if size='small'
my %sortMapping = ( first => 'givenName',
                    last  => 'sn',             # surname
                    user  => 'uid', );

# -- get the parameters passed to webpage.
my $users         = param('user')     || param('users')   || $default_users;
my $webpage_title = param('title')    || $default_title;
my $do_all_emails = param('emails')   || $default_do_all_emails;
my $sort_order    = param('sort')     || $default_sort_order;
my $status        = param('status')   || $default_status;
my $page          = param('page')     || $default_page;
my $size          = param('size')     || $default_size;
my $columns       = param('columns')  || ($size eq 'small' ? 
                                          $small_columns : $default_columns);
my $rows          = param('row')      || ($size eq 'small' ?
                                          $small_rows : $default_rows);
my $small         = (param('size') and (param('size') eq 'small')) ? 1 : 0;
my $imgwidth      = param('imgwidth') || 100;
my $details       = defined(param('details')) ? param('details') : 1;
my $background    = param('background') || '#FFF';
my $bold          = defined(param('bold')) ? param('bold') : 1;
my $special_param = param('special') || '';
my $spacing       = param('spacing') || ''; # default value(s) in code, below.

my $ldap_data     = param('ldap_data') || 0;

my $class         = param('class') || 0;

my $imgheight     = sprintf("%.0i", 125 * ($imgwidth/100));
my $photo_size    = qq{width="$imgwidth" height="$imgheight"};
if ($background !~ /^#/){
  if ($background !~ /maroon|red|orange|yellow|olive|purple|fuchsia|white|lime|green|navy|blue|aqua|teal|black|silver|gray/){
    $background = '#' . $background;
  }
}

# one more than number of commas in search string.
my $n_people = 1 + (() = $users =~ /,/g);  

# -- set status
if ($status){
  $do_all_emails = 0;
  $webpage_title = 'students@marlboro' if $status eq 'student';
  $webpage_title = 'faculty@marlboro'  if $status eq 'faculty';
  $webpage_title = 'staff@marlboro'    if $status eq 'staff';
  $webpage_title = 'alumni@marlboro'   if $status eq 'alumni';
  $status = "faculty,staff,student"    if $status eq 'current';
  $status = "faculty,staff,student,alumni,guest" if $status =~ /all|everyone/;
  $status =~ s/,/|/g;
}

# -- if no search was requested, just display a form page and exit --
unless ($users or $status){
  if ($size eq 'small'){
    print_small_query_page();
  }
  else {
    print_query_page();
  }
  exit;
}

# -- connect with the the ldap server --
my $ldaps = Net::LDAP->new($ldap_url) 
  or die "Couldn't connect to '" . $ldap_url . "': $@";
## auth connection looks like this :
#my $authuser="uid=mahoney,ou=people,dc=marlboro,dc=edu";
#my $passwd="****";
#my $msg = $ldaps->bind($authuser, password => $passwd);
# As of Dec 2005 version, anon bind must be without a $dn.
my $msg   = $ldaps->bind();  # anonymous bind
$msg->sync;                          # wait for the server to complete request
if ($msg->is_error){
  die "Couldn't bind to '" . $ldap_dn . "'. " . $msg->error;
}

## -- Legal status attributes includes facultystaff as one word,
##    so if either word is in the list to search, I'll look for
##    *faculty* or *staff*.
# $status =~ s/faculty/\*faculty\*/;
# $status =~ s/staff/\*staff\*/;

# as of Fall 2007, 
# eduMarlboroSatus is (faculty staff gcstaff gc-faculty faculty-staff)

# As of Fall 2010,
# 'eduMarlboroFacultyActive : true' is apparently another field

# -- choose what to return from the search
my $attributes = [qw( cn sn givenName eduMarlboroStatus gidNumber
                      mail telephoneNumber title uid uidNumber
		      eduMarlboroClass eduMarlboroCampusBox 
		      eduMarlboroCampusBuilding 
                    )];
# -- and what to look for
my $filter = '(|';
if ($status){
  $filter .= "(gidNumber=50001)"  if $status=~/faculty|staff/;
  $filter .= "(gidNumber=50003)"  if $status=~/student/;
  $filter .= "(gidNumber=50002)"  if $status=~/alumni/;
  $filter .= "(gidNumber=50004)"  if $status=~/guest/;
}
else {                # look for people by username
  map { $filter .= "(uid=$_)" } split /,/, $users;
}
$filter .= ')';


my @results;

# The ldap server only returns 25 names at a time.
# This avoids that limit by running successive searches
# that a include a "but not any of those guys" filter.
# The input and output is all through the globals; essentially
# this replaces
# my @results = $ldap->search( 
#     base     => $ldap_dn,     # Start search here.
#     password => $pass,        # with this access password
#     scope    => "one",        # Look one level deeper,
#     filter   => $filter,      # for these entries, and
#     attrs    => $attributes,  # return these fields
#			     )->entries;
sub bruteforce_search {
  my @entries = ();
  my $exclude = '';   # folks already found, eg '(uid=jsmith)(uid=joe)' etc
  my $max_loop = 80;  # at 25 names per loop is 2000 people maximum
  my $iter = 0;
  while (1){
    last if $iter++ > $max_loop;
    if (@entries){
      $exclude .= join('', map { '(uid='. $_->get_value('uid') .')' } @entries);
    }
    my $big_filter = $exclude ? "(&$filter(!(|$exclude)))" : $filter;
    my $result = $ldaps->search(base    => $ldap_dn,     # Start search here.
				scope   => "one",        # Look one level deeper,
				filter  => $big_filter,  # for these entries, and
				attrs   => $attributes,  # return these fields
			       );
    @entries = $result->entries;
    last unless @entries;
    push @results, @entries;
  }
}

bruteforce_search();  # uid matches to query.

my $debug_msg;
if (not $status){
  if ($n_people == 1 or not ($n_people == scalar(@results))){
    # $debug_msg = "
    #  \$n_people = $n_people
    #  scalar(\@results) = " . scalar(@results) . " 
    # ";
    # also matches within names if 1 person, or not 1-to-1 users/results.
    $filter = '(|';
    map { $filter .= "(username=*$_*)(cn=*$_*)" } split /,/,$users;
    $filter .= ')';
    bruteforce_search();
  }
}

# Remove duplicates. (Recipe 4.7 from Perl Cookbook.)
my %seen=();
@results = grep {! $seen{$_->get_value('uid')}++} @results;

# Keep only folks whose gidMarlboroStatus contains given status
if ($status){
  @results = grep {
    $_->get_value('eduMarlboroStatus') and
      $_->get_value('eduMarlboroStatus') =~ m/$status/} @results;
}

# -- sort results by chosen attribute (i.e. first name, last name, username)
my $sortKey = $sortMapping{$sort_order};
my @entries = sort { lc($a->get_value($sortKey)) cmp
                     lc($b->get_value($sortKey)) } @results;

# -- display the search results in a web page; essentially one big table --
print header if defined $ENV{SERVER_PORT};   # only if invoked from a browser.
print  start_html($webpage_title);
print "<pre>$debug_msg</pre>" if $debug_msg;
print  get_style($small);
print "<h1>" . $webpage_title . "</h1>\n" unless $size eq 'small';
my $table_cellspacing = $spacing ? $spacing : $size eq 'small' ? 4 : 10;
print "<table cellspacing='$table_cellspacing'>\n";
my $counter=0;                  # for keeping track of table columns
my %info;                       # convenient editable storage for the data
my $all_emails = "";            # group email address of all entries
my @ids = ();

my $n_results = scalar(@entries);
my $n_per_page = $rows * $columns;
my $n_pages = int($n_results / $n_per_page + 0.99999);
my $i = ($page - 1) * $n_per_page;
my $i_max = $i + $n_per_page < $n_results ? $i + $n_per_page : $n_results;
my $small_start = $size eq 'small' ? "<small>" : "";
my $small_end   = $size eq 'small' ? "</small>" : "";

if ($n_results==0 and $size eq 'small'){
  print "<tr><td>No results found.</td></tr>\n";
}

# foreach my $entry ( @entries ){
while ($i < $i_max){
  my $entry = $entries[$i];
  $i++;

  $info{$_} = $entry->get_value($_) || '' foreach (@$attributes);
  $info{telephoneNumber} =~ s/802 258 9/x/;         # on campus extensions

  my $class_standing = lc($info{eduMarlboroClass});
  if ($class_standing){
    for ($class_standing){
      s/fr(\d)/freshman $1/;
      s/so(\d)/sophomore $1/;
      s/ju(\d)/junior $1/;
      s/se(\d)/senior $1/;
    }
  }

  # if we're asking for class standing, and a student doesn't have one,
  # then skip them: they're probably not really students.
  #next if ($class and $info{eduMarlboroStatus} =~ /student/ and
  #	     (not $class_standing or $class_standing =~ /^\s*$/));
  
  if ($counter % $columns == 0){
    print "<tr>\n";
  }

  my $description = '';
  if ($info{title}){
    $description = $info{title};
  }
  elsif ($class){
    $description = $class_standing;
    if (not $description){
      $description = 'alumni' if $info{eduMarlboroStatus} =~ /alumni/;
    }
  }
  $description .= "<br/>" if $description;

  # The information displayed for each entry is
  #        image
  #        name  (in bold)
  #        title (if present)  --- small
  #        email phone         --- small
  push @ids, $info{uidNumber};
  my $special = special_photos($info{uid}, $special_param);
  my $local_photo = $local_photo_folder . $info{uid} . '.jpg';
  my $photo_uri = $special ? $special :
                  -e $local_photo ? $local_photo : 
		  $photo_directory . $info{uid};
  my $img = '<img src="' . $photo_uri . '" '. $photo_size  .' >';
  my ($bold_start, $bold_end) = ('<b>', '</b>');
  if (not $bold){ ($bold_start, $bold_end) = ('','') }
  print " <td align='center'>\n"
    . $img . "<br>\n"
    . $small_start
    . $bold_start . $info{cn} . $bold_end . "<br/>\n";
  if ($details){
    print "<small>";
    unless ($size eq 'small'){
      print $description
        . '<a href="mailto:' . $info{mail} . '">' . $info{uid}  .  "</a>"; }
    print "  " . $info{telephoneNumber} . "</small>";
  }
  elsif ($class){
    print "<small>" . $class_standing . "</small>";
    my $standing = lc($info{eduMarlboroClass});
  }
  print $small_end;
  if ($ldap_data){
    print '<br/>'
      . '<pre style="border:solid 1px black;font-size:small;text-align:left">'
      . "<b>ldap data</b>\n";
    for my $attribute (@$attributes){
      print " $attribute is '" . $info{$attribute} . "'\n";
    } 
    print '</pre>';
  }
  print '</td>';
  $all_emails .= $info{mail} . ",";
  #$all_emails .= $info{mail} . '@marlboro.edu,';
  $counter++;
  if ($counter % $columns == 0){
    print "</tr>\n";
  }
}
# fill out the rest of this last table row with blank cells
while ($counter % $columns != 0){
  print "<td>&nbsp;</td>";
  $counter++;
  if ($counter % $columns == 0){
    print "</tr>\n";
  }
}
my $uri = url(-relative => 1, -query => 1);
$uri =~ s/;/&/g;
$uri =~ s/&page=\d+//;  # remove any old page number
my $prev_link = $page == 1 ? 'prev' : 
               '<a href="' . $uri . "&page=" . ($page-1) . '">prev</a>';
my $next_link = $i_max == $n_results ? 'next' :
               '<a href="' . $uri . "&page=" . ($page+1) . '">next</a>';
if ($n_pages > 1){
  print qq{<tr><td align="center" colspan="$columns">
   <div style="float:left">$prev_link</div>
   <div style="float:right">$next_link</div>
   <div>page $page of $n_pages</div>
</td></tr>}
}
print "</table>\n";

unless ($size eq 'small'){
  print "<hr noshadow size=1>\n";  # ---- below this <hr> is the footer
  $all_emails =~ s/,$//;
  print qq{
  <table width="100%">
  <tr>
    <td align="left">};
  if ($do_all_emails){
    print qq{ &nbsp; <a href="mailto:} 
      . $all_emails . qq{">Send them email.</a>\n};
  }
  my $date = scalar localtime;
  my $results_summary = $n_results < 2 ? '' : "<br/>$n_results matches found.";
  print qq{
    </td>
    <td align="right">
      <small> 
      questions to: Jim Mahoney
      <a href="mailto:mahoney\@marlboro.edu">(mahoney\@marlboro.edu)</a><br/>
      page generated on $date
      $results_summary
      </small>
    </td>
  </tr>
  </table>};
}

## -- username/ids in html comment --
#print "<!-- ids: \n";
#print shift(@usernames) . " " . shift(@ids) . "\n" while @ids;
#print " -->\n";

$ldaps->unbind;

if (0){ # debugging
  chomp(my $pwd = `/bin/pwd`);
  my ($ldap_browser_dn, $ldap_browser_pass) = get_ldap_browser();
  print qq(
<pre>
 --- debug ---
 ldap_browser_dn   = '$ldap_browser_dn'
 ldap_browser_pass = '$ldap_browser_pass'
 /bin/pwd says '$pwd'
 \$ENV{REMOTE_ADDR} = '$ENV{REMOTE_ADDR}'
</pre>
);
}
print end_html . "\n";

# --- subroutines ----------------------------------------------------

sub print_small_query_page {
  print 
      header
    . start_html("folks\@marlboro")
    . get_style(1)
    . qq{
<table>
 <tr><td><h2>folks\@marlboro</h2></td></tr>
 <tr><td>
 <form method='GET'>
  <input type='hidden' name='size' value='small' />
  names: <input type='text' name='users' /> 
  <input type='submit' value="look 'em up" />
 </form>
 </td>
</tr></table>
<hr />
<ul>
<li><a href="lookup.cgi?size=small&status=student&sort=last">students</a></li>
</ul>
<hr />
<div align="right">
<small>
  Jim Mahoney
  <a href="mailto:mahoney\@marlboro.edu">(mahoney\@marlboro.edu)</a><br />
  last modified $modified_date<br />
  <a href="lookup.cgi_html?language=perl">source code</a>
</small>
</div>
    }
    . end_html;
}

sub get_style {
  my $small = shift;
  my $font = $small ? ';font-size:2.5em' : '';
  return qq{
<style type="text/css">
 body {background-color: $background $font} ;
 h2 { margin:0; padding:0; }
 hr { height:1px; border:0; background-color:darkgreen; color:darkgreen; }
 form { margin:0; text-align:right }
 input { border: 1px solid darkgreen; padding:2px; font-size:1em; }
 h3 { margin:0; padding:.5em; }
 ul { margin:0; }
 td { vertical-align: top; }
</style>
  };
}

sub print_query_page {
 # removed - problem generating on Oct 14 2009
 #   <li><a href="alumni.html">alumni</a></li> 
  print 
      header
    . start_html("folks\@marlboro")
    . get_style()
    . qq{
<table width="100%"><tr>
 <td><h2>folks\@marlboro</h2></td>
 <td>
 <form method='GET'>
  names: <input type='text' name='users' size=32 /> 
  <input type='submit' value="look 'em up" />
 </form>
 </td>
</tr></table>
<hr />

<h3>Groups (as of Sep 12 2013)</h3>
<ul>
 <li><a href="students.html">students</a> by first name</li>
 <li><a href="facultystaff.html">faculty and staff</a></li>
 <li><a href="current.html">everyone</a></li>
</ul>

<h3>Groups (as of this moment; may load slowly)</h3>
<ul>
 <li><a href="lookup.cgi?status=student&class=1&sort=first&title=students%20@%20marlboro">students</a> by first name</li>
 <li><a href="lookup.cgi?status=faculty,staff&title=faculty%20and%20staff%20@%20marlboro">faculty and staff</a> by last name</li>
 <li><a href="lookup.cgi?status=faculty,staff,student&title=students%20faculty%20staff@%20marlboro">students, faculty, and staff</a> by last name</li>
</ul>

<h3>Instructions</h3>
<ul>
<li>Type any part of a first name or last name, or a full username
in the "names" field, and then hit return.</li>
<li>To look for multiple people, put commas between the search strings.  
In that case, if the correct number of matches is found in usernames
then searches in parts of first and last names will be skipped.
<li>For example,
<ul>
<li><i>jim</i> finds both "Jim Mahoney (mahoney)" and "James Tober (jim)"</li>
<li><i>jim,mahone</i> finds "Jim Mahoney (mahoney)", "Lynn Mahoney (lynnmm)", "James Tober (jim)", etc.
<li><i>jim,mahoney</i> finds "Jim Mahoney (mahoney)" and "James Tober (jim)".</li>
</ul>
</li>
<li>There's a <a href="?size=small">small version</a> for PDA's, cell phones, and other handheld devices.</li>
</ul>

<h3>Caveats</h3>
<ul>
<li>These pages can only be seen from within marlboro.edu.</li>
<li>These lists are <i>not</i> completely accurate: they're based on the online LDAP database, not the registrar's system.</li>
</ul>

<h3>Tricky stuff</h3>
<ul>
 <li>You can generate pages for any group of people you want by putting extra stuff in the URL.</a>
 <li>For the details, 
     use <a href="lookup.cgi_html?language=perl">the source</a>, Luke.</li>
 <li>Examples
 <ul>
  <li>The IT staff.<br /><small>
<a href="lookup.cgi?users=iank,price,hbaker,tobiasg,johnnyb,johnny,elliot&title=IT%20Staff&columns=4">lookup.cgi?users=iank,price,hbaker,tobiasg,johnnyb,johnny,elliot&title=IT%20Staff&columns=4</a></small></li>
  <li>Alumni, sorted by first name (loads very slowly)<br /><small>
<a href="lookup.cgi?status=alumni&sort=first">lookup.cgi?status=alumni&sort=first</a></small></li>
 </ul></li>
</ul>

 <hr />
 <div align="right">
 <small>
   Question? Talk to Jim Mahoney<br/>
   <a href="mailto:mahoney\@marlboro.edu">(mahoney\@marlboro.edu)</a><br />
   last modified $modified_date<br />
   <a href="lookup.cgi_html">source code</a>
 </small>
 </div>

    }
    . end_html;
}
