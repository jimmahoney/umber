package JimWiki;
our @ISA    = qw(Exporter);
our @EXPORT_OK = qw(_wiki2html);

# --- May 2017 ----
# Taken from wikiacademia perl/cs/Wiki.pm
# with some small changes (see '2017' below) and omissions,
# to convert from wiki to html using my wikiacademia conventions.

# ===================================================================

# Used to mark removed text; this sequence shouldn't be one that
# occurs in the text.  For example: 
#   "this that <nowiki>[[stuff]]</nowiki> other" 
# temporarily becomes something like
#   "this that $FS1 other"
my $FS  = "\x1e\xff\xfe\x1e"; # field seperator

# external link pattern definitions
my $UrlProtocol  = qr{http|https|ftp|afs|mailto};
## was: my $UrlChar      = qr{[A-Za-z0-9.+_~\-\\/%&#?!=()@\x80-\xFF]};
# RFC 3986 gives the syntax of URIS, which is fairly elaborate.
# I'm not trying to match exactly; however, I do need the legal chars :
#     unreserved    a-z A-Z 0-9 - . _ ~
#     reserved      : / ? # [ ] @ ! $ & ' ( ) * + , ; =
#     escaped       % hex hex
my $UrlChar      = qr{[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]};
my $AbsoluteURI  = qr{$UrlProtocol:$UrlChar+};
my $link_name    = qr{[^ \t\n\|\]][\|\]]*?};  # not | or ] and non-white start

# 2017 : Taken from test/test_wiki.pl folder ;
# these lines as they were from cs/Wiki.pm were throwing errors.
my $bracket_delim= qr{\s*(?:\s|\|)\s*};      # | or space
my $beforeBareURI= qr{(?<!=")}i;
my $afterBareURI = qr{(?!</a>)((?:&!lt;)|([ \t\n\f\r<>'"]))};

# What follows is my version of some wiki stuff.
# Yeah, it's too much re-inventing the wheel - 
# but I wasn't finding quite what I wanted in any of the others.
#
# The syntax is close to (but not quite identical to) 
# the Wikipedia's MediaWiki software.
# Some of this is adapted from the UseMod wiki code, which is
# what the MediaWiki was originally based on.
#
# I'm not doing anything fancy with marking page links that do or don't exist;
# this is a self-contained processing of indentation, lists, and so on.
#

# Syntax rules :
# --------------------
#
# 1. initial processing
#
#   <nowiki>...</nowiki>     =>   ...                No wiki processing at all.
#                                                    Can cross multiplie lines.
#
#   this \                   =>   this that          Continue on next line.
#    that                                            (Leading whitespace on  
#                                                    doesn't give <code><pre>.)
# 2. blocks
#
#   = header1 =              =>   <h1>header1</h1>
#   == header2 ==
#   etc.
#
#   ----                     =>   <hr />             start of line only
#
#
#   * a                      =>   <ul> and <ol>      Use \ to span lines.
#   * b
#   ** c.a
#   ** c.b  \
#      more c.b
#   * d
#   *# a.1
#   *# a.2
#   * e
#
#   \n                       =>  <div>text</div>     newline => new paragarph
#   text
#   \n
#
#      leading spaces        =>  <code><pre> ... </pre></code>
#       means leave as is
#
#   : indent                 =>  <div class="indent">...</div>
#   : these lines 
#
#   :: doubly indented       => <div class="indent"><div class="indent">
#   :: paragraph                 ...</div></div>
#
# 3. character markup
#
#   ''italic''               => <i>...</i>
#   '''bold'''                  <b>...</b>
#   ''''bold italic''''         <b><i>...</i></b>
#                                ... but html markup is probably just as easy.
#
# 4. links and urls
#
# external :
#   
#   http://...                       =>  <a href="http://...">http://...</a>
#   [ http://... ]                       same
#   [[ http://... ]]                     same
#
#   [ http://... display this ]    =>  <a href="http://...">display this</a>
#   [ http://...  | displayed this ]    same
#   [ displayed text http://... ]       same
#   [[ http://...  | displayed this ]]  same
#   <a href="...">...</a>               this works too
#
#   external URL's 
#     * must not be preceded by  = ' " 
#     * must end with whitespace or ]
#     * must start with one of (http: https: ftp: afp: mailto:
#   The wikipedia convention distinguishes between
#   [ external link ] and  [[ internal link ]]; however,
#   I'm allowing either for form for externals.
#   See $UrlProtocol, $UrlChar, $BareUrlDelimeter
#
# internal :
#
#   [[ some page ]]                 =>  <a href="some_page.html">some page</a>
#   [[link name | show this]]       =>  <a href="link_name.html">show this</a>
#                                 
# namespace mappings :
#
#   [[ wikipedia: some page ]]      => <a href="...">wikipedia: some page</a>
#   [[ wikipedia: article | link]]  => <a href="wikipedia ...article">link</a>
#                                      (Page names can contain "-" besides \w)

# Coming (maybe) :
# ------------------------
#
#   {{ macro | arg1 | arg2 }}
#
#   __COMMAND__ (mediawiki: __TOC__ __NOTOC__ __NOEDITSECTION__
#
#   ISBN, RFC, ... expansion
#

sub _wiki2html {
  my ($text, $editsection) = @_;

  my %fields;                        # hash of temporarily removed text

  # Remove any $FS chars. (Hopefully there aren't any.)
  $text =~ s/$FS//g;

  # Temporarily remove the <nowiki>..</nowiki> sections.
  my $nfield = 1;
  while ( $text =~ s{<nowiki>(.*?)</nowiki>}{$FS$nfield}s ){
    # print " $nfield : '$1' \n";
    $fields{"$FS$nfield"} = $1;
    $nfield++;
  }

  for ($text){

    # ----------------------------------------------------------
    # -- 1. initial setup                                     

    # End it with a newline if it doesn't already.
    #  (My algorithms assume this.)
    $text .= "\n" unless $text=~m/\n$/;

    # Convert prior html markup tags ( < > )  to ( &gt; &lt; )
    $text =~ s/>/$FS&gt;/g;
    $text =~ s/</$FS&lt;/g;

    # Join lines with backslash at end
    $text =~ s&\\ *\r?\n& &g;                   

    # --- macros --------------------------------------
    # Macros have the form {{ name | arg1 | arg2 | arg3 }}
    # and turn into something else depending on the macro.
    # If name isn't found, then no replacement is done.
    # The "name" is made of perl \w chars, [A-Za-z0-9_].
    s[{{due(.*?)}}][<h3 class="due">due $1</h3>]g;

    # ----------------------------------------------------------------
    # -- 2. blocks : headers, hr, lists, paragraphs, preformatted

    # Convert lines like "== header ==" to "<h2>header</h2>'
    for my $n (5,4,3,2,1){
      s&^ ={$n} \s* (.*?) \s* ={$n} \s* $&<h$n>$1</h$n>&mgx;
    }

    # Convert ---- to <hr />  (must start the line)
    s&^-{4,}&<hr />&mg;

    # Turn *'s and #'s to bullet and numbered lists.
    # (The following is messy but seems to work.)
    #  1. Put <li>..</li> around each '* ...' or '# ...' line
    s&^(\*|#)\s*(.*)$&<li>$1$2</li>&mg;       
    #  2a. Put <ul>...</ul> around adjacent '<li>* ...' lines
    #  (e.g. <ul>..</ul> around '* ...' block)
    s&((^<li>\*(.*)\n)+)&<ul>\n$1</ul>\n&mg;  
    #  2b. .. and then turn those '<li>*' to '<li>'
    s&^(<li>)\*(.*)$&$1$2&mg;                 # remove leading *
    #  3a. Put <ol>...</ol> around adjacent '<li># ...' lines
    #  (e.g. <ol>..</ol> around '# ...' block)
    s&((^<li>#(.*)\n)+)&<ol>\n$1</ol>\n&mg;   
    #  3b. .. and then turn those '<li>#' to '<li>'
    s&^(<li>)#(.*)$&$1$2&mg;                  # remove leading #
    # debug: print " after first pass:\n ----------------- \n";
    # debug: print $text . "\n ------------ \n";
    #  4. while there are deeper lists to worry about,
    while ( m&^<li>(\*|#)&m ){
      #  5a. Put <ul>..</ul></li> around consectuve '<li>*' lines
      #      and remove preceding li
      s&</li>\n((^<li>\*(.*)\n)+)&<ul>\n$1</ul></li>\n&mg;
      #  5b. ... and then convert those '<li>*' to '<li>'
      s&^(<li>)\*(.*)$&$1$2&mg;
      #  5a. Put <ol>..</ol></li> around consectuve '<li>#' lines
      #      and remove preceding li
      s&</li>\n((^<li>#(.*)\n)+)&<ol>\n$1</ol></li>\n&mg; 
      #  5b. ... and then convert those '<li>#' to '<li>'
      s&^(<li>)#(.*)$&$1$2&mg; 
     }

    # Put <div>...</div> around paragraph blocks.
    # Here lines in paragraphs start with something that's not ( < $FS \n \s ).
    #
    #  ... Jan 28 re-think ...
    #  This definition is a bit problematic, since right now this text
    #      Please watch
    #      <i>The Tango Lesson</i>
    #      sometime during the term.
    #  will be treated as 3 paragarphs, since the middle line 
    #  will begin $FS after the initial translation.
    #  Perhaps I should to have a list of tags that are allowed to do this,
    #  even though I definitely don't want <div ...> stuff within paragraphs.
    #  Hmmm.  I need to think about this - why do I have $FS in this list?
    #  ......................
    #  I'' try *with* $FS (\x1e).
    #  That is, <...> tags input by user are in paragraphs.
    #
    s{^((?:[^<\s\n].*\n)+)}{<div>\n$1</div>\n}gm;

    # Put <code><pre>..</pre></code> around indented blocks
    # (i.e. around consecutive lines that start with tab or space)
    s{^((?:[ \t].*\n)+)}{<code><pre>\n$1</pre></code>\n}gm;

    # Put <div class="indent">...</div> around blocks where each line starts
    # with the ":" character.  
    # This can be done multiple times; thus :: is doubly indented.
    # Example:
    #    This is normal.
    #    : This is a 
    #    : single indented paragarph.
    #    :: This is a doubly
    #    :: indented paragraph.
    my $continue=1;     # stop this when we fail to find anything to indent.
    while ($continue){
      # First wrap the <div.. >...</div> around the block
      $continue = s{^((?::.*\n)+)}{<div class="indent">\n$1</div>\n}gm;
      # then remove the leading : from all lines.
      s{^:}{}gm if $continue;
    }

    # Clean up empty lines between blocks, i.e.
    #    ...
    #    </div>
    #
    #    <code>
    #    ...
    # becomes
    #    ...
    #    </div>
    #    <code>
    #    ...
    # 
    # If there's more than one empty line then put in a <p /> marker 
    # since the intention is presumably to get more vertical space.
    s{>(?:\n\s*){2,}\n<}{>\n<p />\n<}mg;
    s{>\n\s*\n<}{>\n<}mg;

    # ----------------------------------------------------------------
    # -- 3. character markup 

    # bold and italic emphasis
    s{''(.*)''}{<i>$1</i>}gm;   # can cross lines
    s{'''(.*)'''}{<b>$1</b>}gm;   # can cross lines
    s{''''(.*)''''}{<b><i>$1</i></b>}gm;   # can cross lines

    # ----------------------------------------------------------------
    # -- 4. external and internal links

    # bracketed absolute URIs
    #  [[http:...]] or  [http:...]
    s{\[\[ \s* ($AbsoluteURI) \s* \]\] }{<a href="$1">$1</a>}gxm;
    s{\[   \s* ($AbsoluteURI) \s* \]   }{<a href="$1">$1</a>}gxm;

    # bracketed absolute URIs with display text
    # [[http:... | display_text ]] or  [[http:... display_text ]]
    # [http:... | display_text ] or  [http:... display_text ]
    s{\[\[ \s* ($AbsoluteURI) $bracket_delim ($link_name) \s* \]\] }
     {<a href="$1">$2</a>}gxm;
    s{\[ \s* ($AbsoluteURI) $bracket_delim ($link_name) \s* \] }
     {<a href="$1">$2</a>}gxm;
    # [[display_text | http:... ]] or  [[display_text http:...]]
    # [display_text | http:... ] or  [display_text http:...]
    s{\[\[ \s* ($link_name) $bracket_delim ($AbsoluteURI) \s* \]\] }
     {<a href="$2">$1</a>}gxm;
    s{\[ \s* ($link_name) $bracket_delim ($AbsoluteURI) \s* \] }
     {<a href="$2">$1</a>}gxm;

    # bracket external URLS with display strings into links
    # [ http:... name ]   or [ name http:... ] or 
    # [[ http:... name ]  or [[ name http:... ]] or 
    # [ http:... | name ] or [[ http:... | name ]]
    # was #   s{\[\[ \s* ([:-_.\w\s]*?) \s* ($UrlProtocol  :  $UrlChar*) 
    #     #     \s* \|? \s* ([:-_.\w\s]*?) \s* \]\]}{<a href="$2">$1$3</a>}gxm;
    #     #   s{\[   \s* ([.\w\s]*?) \s* ($UrlProtocol : $UrlChar*) 
    #     #     \s* \|? \s* ([:-_.\w\s]*?) \s* \]}{<a href="$2">$1$3</a>}gxm;

    # bare URLs into links
    #  (Note that any original user's <a href="URI">URI</a> have been $FS'ed, 
    #   so there's no need to worry about those - I only have to avoid
    #   matching the ones created above.)
    s{$beforeBareURI($AbsoluteURI)($afterBareURI)}{<a href="$1">$1</a>$2}ogm;

    # double bracket internal links.  
    # Only perl word chars and spaces; \w is [a-zA-Z0-9_]
    # [[ local / new page ]]  =>  <a href="local/new_page">new page</a>
    s{\[\[ \s* ([\w\s]+?) \s* \]\]}{<a href="$1.html">$1</a>}gmx;

    # [[ link name | display name ]] 
    # =>   <a href="link name.html">display name</a>
    s{\[\[ \s* ([\w\s]+?) \s* \| 
           \s* ([\w\s]+?) \s* \]\]}{<a href="$1.html">$2</a>}gmx;

    # Namespace links which look internal but go elsewhere.
    # This'll prob'ly turn into a loop over a hash eventually.
    # But for now, with only one ... I'll just put 'em in.
    #  my %namespace_mappings = 
    #     ( Wikipedia => 'http://en.wikipedia.org/wiki/' );
    #  foreach my $namespace (keys %namespace_mappings){
    #    my $urlPrefix = $namespace_mappings{$namespace};
    # [[ wikipedia: some page ]] 
    # =>   <a href="http://en.wikipedia...">some page</a>
    my $namespace = 'wikipedia';
    my $urlPrefix = 'http://en.wikipedia.org/wiki/';
    s{\[\[ \s* ($namespace: \s* ([\w\s-]+?)) \s* \]\]}
     {<a href="$urlPrefix$2">$1</a>}gmxi;
    s{\[\[ \s* $namespace: \s* ([\w\s-]+?) \s* \| \s* ([\w\s-]+?) \s* \]\]}
     {<a href="$urlPrefix$1">$2</a>}gmxi;
    # };
    
    # <a href="link name.html"> => <a href="link_name.html">
    # (Note that the user's <a > tags are all $FS'ed, 
    #  so this doesn't match those.)
    1 while s{<a href="([\w\s\/:.]+)\s([\w\s.?&]+?)">}{<a href="$1_$2">}mg;

    #   Hmmm.  
    #   I was thinking of doing {{modified}} and having it turn into
    #     <div id="modified">last modified <% lastmodified() %></div>
    #   but that won't work in a model where this wiki processing is 
    #   done as a Mason filter, since <% lastmodified %> is called before
    #   the filter.
    #   I think I'll just ignore this for now; I haven't really figured
    #   how to divide up the properties and priveleges between
    #    (a) config files (i.e. autohandler)
    #    (b) current_comp files (i.e. home.html)
    #    (c) the database

    # ------------------------------
    # Restore prior html markup tags ( < > )  to ( &gt; &lt; )
    # (Limit which tags are allowed?  Hmm.  
    # This isn't a full public wiki right now.)
    $text =~ s/$FS&gt;/>/g;
    $text =~ s/$FS&lt;/</g;

  }

  # Restore the temporarily removed <nowiki> blocks.
  foreach my $key (reverse sort keys %fields){  # longest to shortest
    #print " key = '$key' \n";
    #print " field = '".$fields{$key}."'\n";
    $text =~ s/$key/$fields{$key}/;
  }

  return $text;
}

1;

__END__

== random notes =====================================================

# from usemod1.0
 
# Names of sites.  (The first entry is used for the number link.)
@IsbnNames = ('bn.com', 'amazon.com', 'search');
# Full URL of each site before the ISBN
@IsbnPre = ('http://shop.barnesandnoble.com/bookSearch/isbnInquiry.asp?isbn=',
            'http://www.amazon.com/exec/obidos/ISBN=',
            'http://www.pricescan.com/books/BookDetail.asp?isbn=');
# Rest of URL of each site after the ISBN (usually '')
@IsbnPost = ('', '', '');

Note that in the following (?:   ) is non-capture grouping.

# Url-style links are delimited by one of:
#   1.  Whitespace                           (kept in output)
#   2.  Left or right angle-bracket (< or >) (kept in output)
#   3.  Right square-bracket (])             (kept in output)
#   4.  A single double-quote (")            (kept in output)
#   5.  A $FS (field separator) character    (kept in output)
#   6.  A double double-quote ("")           (removed from output)
$UrlProtocols = "http|https|ftp|afs|news|nntp|mid|cid|mailto|wais|"
  . "prospero|telnet|gopher";
$UrlProtocols .= '|file'  if ($NetworkFile || !$LimitFileUrl);
$UrlPattern = "((?:(?:$UrlProtocols):[^\\]\\s\"<>$FS]+)$QDelim)";
$ImageExtensions = "(gif|jpg|png|bmp|jpeg)";
$RFCPattern = "RFC\\s?(\\d+)";
$ISBNPattern = "ISBN:?([0-9- xX]{10,})";
$UploadPattern = "upload:([^\\]\\s\"<>$FS]+)$QDelim";

====================================================

wikipedia :
http://en.wikipedia.org/wiki/Wikipedia%3AHow_to_edit_a_page

* Three ways to link to external (non-wiki) sources:
  # Bare URL: http://www.nupedia.com/                  (bad style)
  # Unnamed link: [http://www.nupedia.com/]            (bad style)
  # Named link: [http://www.nupedia.com Nupedia]       (good style)

  Note that there is *not* a pipe between URL and displayed text.

  In the URL, all symbols must be among
  A-Z a-z 0-9 . + \ / ~ % - + & # ? ! = ( ) @ \x80-\xFF

* Linking to other wikis
  [[Wiktionary:Hello]]
  
* internal links (many variations)
  [[public transport]]                 wiki/Public_transport
  [[public transport | stuff]]         same link; different display
  [[taxi]]s                            wiki/Taxi shown as "taxis"  (ugh)
  [[#example]]                         current page at <div id="example">..</div>
                                       (or that id in nearly any html element)

* When adding a comment to a Talk page,
  you should sign it by adding
  three tildes to add your user name:
  : ~~~
  or four for user name plus date/time:
  : ~~~~
  Five tildes gives the date/time alone:
  : ~~~~~

* #REDIRECT [[United States]] 

* Comments just use html markup.  Seems a bit awkward to me.
  <!-- comment here -->

* At the current status of the wiki markup language, having at least
  four headers on a page triggers the TOC to appear in front of the
  first header (or after introductory sections). Putting __TOC__
  anywhere forces the TOC to appear at that point (instead of just
  before the first header). Putting __NOTOC__ anywhere forces the TOC
  to disappear.

===================================================

http://tools.ietf.org/html/rfc3986
RFC 3986, Jan 2005, Uniform Resource Identifier (URI): Generic Syntax

 * This supercedes several older versions, and adds some new allowed chars.)
 * The ABNF notation here is described at http://tools.ietf.org/html/rfc4234

Appendix A.  Collected ABNF for URI

   URI           = scheme ":" hier-part [ "?" query ] [ "#" fragment ]

   hier-part     = "//" authority path-abempty
                 / path-absolute
                 / path-rootless
                 / path-empty

   URI-reference = URI / relative-ref

   absolute-URI  = scheme ":" hier-part [ "?" query ]

   relative-ref  = relative-part [ "?" query ] [ "#" fragment ]

   relative-part = "//" authority path-abempty
                 / path-absolute
                 / path-noscheme
                 / path-empty

   scheme        = ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )

   authority     = [ userinfo "@" ] host [ ":" port ]
   userinfo      = *( unreserved / pct-encoded / sub-delims / ":" )
   host          = IP-literal / IPv4address / reg-name
   port          = *DIGIT

   IP-literal    = "[" ( IPv6address / IPvFuture  ) "]"

   IPvFuture     = "v" 1*HEXDIG "." 1*( unreserved / sub-delims / ":" )

   IPv6address   =                            6( h16 ":" ) ls32
                 /                       "::" 5( h16 ":" ) ls32
                 / [               h16 ] "::" 4( h16 ":" ) ls32
                 / [ *1( h16 ":" ) h16 ] "::" 3( h16 ":" ) ls32
                 / [ *2( h16 ":" ) h16 ] "::" 2( h16 ":" ) ls32
                 / [ *3( h16 ":" ) h16 ] "::"    h16 ":"   ls32
                 / [ *4( h16 ":" ) h16 ] "::"              ls32
                 / [ *5( h16 ":" ) h16 ] "::"              h16
                 / [ *6( h16 ":" ) h16 ] "::"

   h16           = 1*4HEXDIG
   ls32          = ( h16 ":" h16 ) / IPv4address
   IPv4address   = dec-octet "." dec-octet "." dec-octet "." dec-octet

   dec-octet     = DIGIT                 ; 0-9
                 / %x31-39 DIGIT         ; 10-99
                 / "1" 2DIGIT            ; 100-199
                 / "2" %x30-34 DIGIT     ; 200-249
                 / "25" %x30-35          ; 250-255

   reg-name      = *( unreserved / pct-encoded / sub-delims )

   path          = path-abempty    ; begins with "/" or is empty
                 / path-absolute   ; begins with "/" but not "//"
                 / path-noscheme   ; begins with a non-colon segment
                 / path-rootless   ; begins with a segment
                 / path-empty      ; zero characters

   path-abempty  = *( "/" segment )
   path-absolute = "/" [ segment-nz *( "/" segment ) ]
   path-noscheme = segment-nz-nc *( "/" segment )
   path-rootless = segment-nz *( "/" segment )
   path-empty    = 0<pchar>

   segment       = *pchar
   segment-nz    = 1*pchar
   segment-nz-nc = 1*( unreserved / pct-encoded / sub-delims / "@" )
                 ; non-zero-length segment without any colon ":"

   pchar         = unreserved / pct-encoded / sub-delims / ":" / "@"

   query         = *( pchar / "/" / "?" )

   fragment      = *( pchar / "/" / "?" )

   pct-encoded   = "%" HEXDIG HEXDIG

   unreserved    = ALPHA / DIGIT / "-" / "." / "_" / "~"
   reserved      = gen-delims / sub-delims
   gen-delims    = ":" / "/" / "?" / "#" / "[" / "]" / "@"
   sub-delims    = "!" / "$" / "&" / "'" / "(" / ")"
                 / "*" / "+" / "," / ";" / "="

Appendix B.  Parsing a URI Reference with a Regular Expression

   As the "first-match-wins" algorithm is identical to the "greedy"
   disambiguation method used by POSIX regular expressions, it is
   natural and commonplace to use a regular expression for parsing the
   potential five components of a URI reference.

   The following line is the regular expression for breaking-down a
   well-formed URI reference into its components.

      ^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?
       12            3  4          5       6  7        8 9

   The numbers in the second line above are only to assist readability;
   they indicate the reference points for each subexpression (i.e., each
   paired parenthesis).  We refer to the value matched for subexpression
   <n> as $<n>.  For example, matching the above expression to

      http://www.ics.uci.edu/pub/ietf/uri/#Related

   results in the following subexpression matches:

      $1 = http:
      $2 = http
      $3 = //www.ics.uci.edu
      $4 = www.ics.uci.edu
      $5 = /pub/ietf/uri/
      $6 = <undefined>
      $7 = <undefined>
      $8 = #Related
      $9 = Related

   where <undefined> indicates that the component is not present, as is
   the case for the query component in the above example.  Therefore, we
   can determine the value of the five components as

      scheme    = $2
      authority = $4
      path      = $5
      query     = $7
      fragment  = $9

   Going in the opposite direction, we can recreate a URI reference from
   its components by using the algorithm of Section 5.3.

Appendix C.  Delimiting a URI in Context

   URIs are often transmitted through formats that do not provide a
   clear context for their interpretation.  For example, there are many
   occasions when a URI is included in plain text; examples include text
   sent in email, USENET news, and on printed paper.  In such cases, it
   is important to be able to delimit the URI from the rest of the text,
   and in particular from punctuation marks that might be mistaken for
   part of the URI.

   In practice, URIs are delimited in a variety of ways, but usually
   within double-quotes "http://example.com/", angle brackets
   <http://example.com/>, or just by using whitespace:

      http://example.com/

   These wrappers do not form part of the URI.

   In some cases, extra whitespace (spaces, line-breaks, tabs, etc.) may
   have to be added to break a long URI across lines.  The whitespace
   should be ignored when the URI is extracted.

   No whitespace should be introduced after a hyphen ("-") character.
   Because some typesetters and printers may (erroneously) introduce a
   hyphen at the end of line when breaking it, the interpreter of a URI
   containing a line break immediately after a hyphen should ignore all
   whitespace around the line break and should be aware that the hyphen
   may or may not actually be part of the URI.

   Using <> angle brackets around each URI is especially recommended as
   a delimiting style for a reference that contains embedded whitespace.

   The prefix "URL:" (with or without a trailing space) was formerly
   recommended as a way to help distinguish a URI from other bracketed
   designators, though it is not commonly used in practice and is no
   longer recommended.

   For robustness, software that accepts user-typed URI should attempt
   to recognize and strip both delimiters and embedded whitespace.

   For example, the text

      Yes, Jim, I found it under "http://www.w3.org/Addressing/",
      but you can probably pick it up from <ftp://foo.example.
      com/rfc/>.  Note the warning in <http://www.ics.uci.edu/pub/
      ietf/uri/historical.html#WARNING>.

   contains the URI references

      http://www.w3.org/Addressing/
      ftp://foo.example.com/rfc/
      http://www.ics.uci.edu/pub/ietf/uri/historical.html#WARNING


