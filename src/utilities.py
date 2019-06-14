# -*- coding: utf-8 -*-
"""
 utilities.py
"""
import parsedatetime, pytz, random
import os, urllib.parse, arrow, string, re, io
from dulwich import porcelain
from dulwich.repo import Repo
from dulwich.object_store import tree_lookup_path
from flask import url_for, app
from markdown2 import markdown
from settings import url_base, debug_logfilename, \
    localtimezone, os_git, umber_debug, umber_cleanup
from flask import url_for, app
from dateutil.parser import parse as dateutil_parse

debug_log = {'file': None}
def print_debug(message):
    if umber_debug:
        print(message)
    if debug_logfilename:
        if not debug_log['file']:
            debug_log['file'] = open(debug_logfilename, 'a')
        debug_log['file'].write(message + "\n")

def myparsethedatetime(date_time_string):
    """ Return a date time string without timezone information
        that arrow() can understand, given a human-friendly 
        description.
    """
    return str(dateutil_parse(date_time_string, ignoretz=True))

def name_to_htmltitle(name):
    """ Return an html version of a course name 
        >>> name_to_htmltitle('123 567 9')
        '123 567 9'
        >>> name_to_htmltitle('123 567 9012 45')
        '123<br>567<br>9012<br>45'
    """
    if len(name) <= 10:
        return name
    else:
        return name.replace(' ', '<br>')

def is_iso_utc(date_time_string):
    """ Return true if this is e.g. '2018-03-03T19:00:00-05:00' 
        which is the ISO time-zone-aware 
        way that I'm storing date-times in the database """
    return bool(re.match(
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}',
        #  2018 - 03  - 03  T 19  : 00  : 00   -   05  : 00
        date_time_string))

def path_to_startdate(path):
    """ Given a path of the form fall2018/coursename, 
        returns corresponding start date.
        >>> path_to_startdate('fall2018/coursename')
        '2018-09-01'
        >>> path_to_startdate(u'fall2018')
        '2018-09-01'
        >>> path_to_startdate('spring2018/foo/bar/baz')
        '2018-01-01'
        >>> path_to_startdate('summer2018/any')
        '2018-06-01'
        >>> path_to_startdate('anything/else')
        ''
    """
    # The string before the first / should be fall|summer|spring + YYYY,
    # else this returns the empty string.
    s = str(path.split('/')[0])
    if s.startswith('fall'):
        return s[-4:] + '-09-01'
    elif s.startswith('spring'):
        return s[-4:] + '-01-01'
    elif s.startswith('summer'):
        return s[-4:] + '-06-01'
    else:
        return ''

class Time(object):
    """ Time in an ISO GMT form, as typically stored in the sqlite database,
        including a timezone-aware (as specified in settings.py) offset.

        >>> print Time('2013-01-01T12:24:52.3327-05:00')
        2013-01-01T12:24:52-05:00

        >>> a = str(Time('Tue Jul 10 2018 18:01:33 +0000')) # UTC
        >>> b = str(Time('Tue Jul 10 2018 14:01:33 -0400')) # EST
        >>> a == b
        True

    """
    # Uses the python Arrow library; see http://crsmithdev.com/arrow/  .
    #
    # For time differences, subtract two of these (given a datetime.timedelta)
    # and then use .seconds, .total_seconds(), .resolution etc.
    #
    # The string format is at http://momentjs.com/docs/#/displaying/format/
    #
    # Since I'm using these mostly for assignment due dates, if a date is given
    # without a time, then the time will by default be set to 11:59pm local.

    defaulttime = '11:59 pm'
    default24time = '23:59:00'
    utc_offset = int(str(arrow.now())[-6:-3])  # from e.g. '2018-07-11T18:05:09-04:00'
    
    @staticmethod
    def parse(date_time_string):
        """ Return Time object from human-ish description 
            i.e. Time.parse('Tuesday') """
        return Time(Time._parse(date_time_string))

    @staticmethod
    def _parse(date_time_string):
        """ Return a date time string from a human-ish description.
            >>> Time._parse('April 1 2018')
            '2018-04-01 23:59:00'
            >>> Time._parse('April 1 2018 5:01pm')
            '2018-04-01 17:01:00'
            >>> Time._parse('2018-01-01')
            '2018-01-01 23:59:00'
            >>> Time._parse('03/19/18 9:00')
            '2018-03-19 09:00:00'

            >>> Time._parse('Tue Jul 10 2018 18:01:33')
            '2018-07-10 18:01:33'
            >>> Time._parse('Tue Jul 10 2018 18:01:33 +0000')
            '2018-07-10 18:01:33'
            >>> Time._parse('Tue Jul 10 2018 14:01:33 -4000')
            '2018-07-10 14:01:33'

        """
        # date_time_string does not do what seems reasonable with time zones,
        # so I'm ignoring it if present and trying to do the right thing later.
        try:
            result = str(dateutil_parse(date_time_string, ignoretz=True))
        except:
            result = str(Time())  # If it can't be parsed, use "now" time.
        if re.search(r'00:00:00', result):
            # rather than use the start of the day (midnight), use the end.
            #print "found zeros"
            try:
                date_time_string += ' ' + Time.default24time
                result = str(dateutil_parse(date_time_string, ignoretz=True))
            except:
                pass
        return result
            
    def __init__(self, datetimestring=None):
        try:
            if datetimestring == None or datetimestring == '':
                # use the "now" time.
                self.arrow = arrow.get()
            elif is_iso_utc(datetimestring):
                # matches the database ISO8601 format with timezone,
                # so don't send it through the parser - just use it.
                self.arrow = arrow.get(datetimestring)
            else:
                parsed = Time._parse(datetimestring)
                parsed = re.sub(r'\.\d+', '', parsed) # remove decimal seconds
                self.arrow = arrow.get(parsed)
                # dulwich git python stores dates in utc timezone
                # as e.g. 'Tue Jul 10 2018 18:01:33 +0000'
                # So if the string looked like that, convert to local timezone.
                # (Note that command line git does e.g. 'Tue Jul 10 2018 14:01:33 -4000')
                if datetimestring[-5:] == '+0000':
                    self.arrow = self.arrow.to('local')
        except:
            # if all else fails, use current time
            self.arrow = arrow.get() 
        # Set timezone.
        self.arrow = self.arrow.replace(tzinfo=localtimezone)
        
    def __lt__(self, other):
        try:
            return self.arrow < other.arrow
        except:
            return False
    def __le__(self, other):
        try:
            return self.arrow <= other.arrow
        except:
            return False
    def __gt__(self, other):
        try:
            return self.arrow > other.arrow
        except:
            return False
    def __ge__(self, other):
        try:
            return self.arrow >= other.arrow
        except:
            return False
    def __eq__(self, other):
        try:
            return self.arrow == other.arrow
        except:
            return False
    def __ne__(self, other):
        try:
            return self.arrow != other.arrow
        except:
            return False
    def __str__(self):
        """ ISO representation rounded down to the nearest second """
        return self.arrow.floor('second').isoformat()
    def human(self):
        """ Return in human friendly form, e.g. 'seconds ago'"""
        return self.arrow.humanize()
    def date(self):
        """ Return as e.g. 'May 09 2013' """
        return self.arrow.format('MMMM DD YYYY')
    def isodate(self):
        return self.arrow.format('YYYY-MM-DD')
    def daydatetime(self):
        """ Return as e.g. 'Sun May 9 2013 4:10 pm' """
        return self.arrow.format('ddd MMMM D YYYY h:mm a')
    def datetime(self):
        """ Return as fixed length e.g. 'Oct 09 2013 04:10 pm' """
        return self.arrow.format('ddd MMM DD YYYY hh:mm a')
    def daydatetimesec(self):
        """ Return as fixed length e.g. 'ddd Oct 09 2013 04:10:32 pm' """
        return self.arrow.format('ddd MMM DD YYYY hh:mm:ss a')
    def slashes(self):
        """ Return as e.g. '06/09/13' """
        return self.arrow.format('MM/DD/YY')
    def assigndate(self):
        """ Return as e.g. 'Thu Jan 26' or 'Tue Jan 23 2pm' """
        datetime = self.arrow.format('ddd MMM D h:mm a')
        if Time.defaulttime in datetime:
            return self.arrow.format('ddd MMM D')
        else:
            return datetime
    def assignISOdate(self):
        """ Return as e.g. '2017-09-03' or '2017-09-4 2pm' """
        datetime = self.arrow.format('YYYY-MM-DD h:mm a')
        if Time.defaulttime in datetime:
            return self.arrow.format('YYYY-MM-DD')
        else:
            return datetime
    def semester(self):
        """ Return as e.g. 'Summer 2013' """
        # YYYY-01-01           => Spring
        # YYYY-06-01 or 07-01  => Summer
        # YYYY-09-01           => Fall
        month = self.arrow.month
        if month < 6:
            season = 'Spring '
        elif month < 9:
            season = 'Summer '
        else:
            season = 'Fall '
        return season + str(self.arrow.year)
    def str(self):
        return str(self)
    def shift_minutes(self, mins):
        self.arrow = self.arrow.shift(minutes=mins)
        return self

def clean_access_dict(dict):
    """ Return access dict with unicode replaced by str 
        >>> dirty = {u'one': u'alpha', 'two':[u'beta', 'gamma']}
        >>> clean = clean_access_dict(dirty)
        >>> sorted(clean.iteritems())
        [('one', 'alpha'), ('two', ['beta', 'gamma'])]
    """
    new_dict = {}
    for (key,value) in dict.items():
        if type(value) == type([]):
            new_value = list(map(str, value))
        else:
            new_value = str(value)
        new_dict[str(key)] = new_value
    return new_dict

def parse_assignment_data(request_form):
    """ Return a dict assignments_data[nth][name, due, blurb] 
        from request form data 
        >>> data = {'assignment_name_2':'readings', 
        ...         'assignment_due_2':'2017-02-03',
        ...         'assignment_blurb_2':'do some stuff' }
        >>> p = parse_assignment_data(data)
        >>> (p[2]['name'], p[2]['due'])
        ('readings', '2017-02-03')
    """
    # The data are in request.form with keys like
    # ('assignment_name_n', 'assignment_due_n', 'assignment_blurb_n')
    # where n is an integer.
    # Empty assignments (e.g. 'assignment_name_7':'') are ignored.
    assignment_data = {}
    regex_expression = re.compile(r'assignment_(\w+)_(\d+)')
    for key in request_form:
        m = regex_expression.match(key)
        if m:
            (which, nth) = (m.group(1), int(m.group(2)))
            if request_form[key] != "":              # Ignore blank assignments.
                if nth not in assignment_data:
                    assignment_data[nth] = {}
                assignment_data[nth][which] = request_form[key]
    # Only keep well-formed assignments which have (name, due, blurb)
    bad = []
    for nth in assignment_data:
        if 'name' not in assignment_data[nth] or \
           'due' not in assignment_data[nth] or \
           'blurb' not in assignment_data[nth]:
             bad.append(nth)
    for nth in bad:
        del assignment_data[nth]
    return assignment_data

def parse_porcelain_log(logstring):
    """ parse the string (stream) generated by from porcelain.log(file)
        into a modification history of the file
        and return a list of tuples [(githash, date, author)] """
    #
    # The logstring input is e.g.
    #
    #   u'--------------------------------------------------\n
    #   commit: d2ecde1b475eafa1293f4827de656d40ee13aaac\n
    #   Author: Jim Mahoney <jim@mahoney.cc>\n
    #   Date:   Tue Jul 10 2018 18:01:33 +0000\n\n
    #   porcelain commit file3\n\n
    #   --------------------------------------------------\n
    #   commit: a4995962bac1bded32e8a75d989378766b0f1bfd\n
    #   Author: Jim Mahoney <jim@mahoney.cc>\n
    #   Date:   Tue Jul 10 2018 13:58:14 -0400\n\n
    #   file 3 initial\n\n
    #   --------------------------------------------------\n
    #   commit: 3b9826ccaffe0f833ca65864c28118efd6bf65fb\n
    #   Author: Jim Mahoney <jim@mahoney.cc>\n
    #   Date:   Mon Jul 09 2018 23:05:29 +0000\n
    #   --message=user:tedteacher\n\n\n'
    #
    # The data timezone is slightly different for git vs dulwich commits.
    # Umber commits store the web user as --message=user: , and that is the
    # the only user that this will pay attention to; else author is left blank.
    #
    # The dash string between entries is 50 characters long.
    # '--------------------------------------------------')
    #           1         2         3         4         5
    #  12345678901234567890123456789012345678901234567890
    #
    result = []
    for revstring in logstring.split('-'*50):
        lines = revstring.split('\n')
        #print_debug("lines : {}".format(lines))
        (githash, date, author) = ('', '', '')
        for line in lines:
            #print_debug("line = '{}'".format(line))
            if line:
                if line[:7] == 'commit:':
                    githash = line[7:].strip()
                if line[:5] == 'Date:':
                    date = Time(line[5:].strip()).daydatetimesec()
                if line[:15] == '--message=user:':
                    author = line[15:].strip()
        if githash:
            result.append((githash, date, author))
        #print_debug('parce_porcelain_log: {}'.format(result))
    return result

def dulwich_get_file_revision(repo, commit, path):
    """ Return a previous version of a file """
    # adapted from http://www.aaronheld.com/post/using-python-dulwich-to-load-any-version-of-a-file-from-a-local-git-repo
    #  repo : absolute path to git repository e.g. '/Users/mahoney/Desktop/testrepo'
    #  commit : sha1 hash of a commit e.g. 'd2ecde1b475eafa1293f4827de656d40ee13aaac'
    #  path : relative path of file beneath repo e.g. 'folder/file1.txt'
    r = Repo(repo)             # r is hash_table : sha keys => objects (commit,tree,blob,tag)
    tree = r[commit].tree      # same as r.get_object(commit)
    (mode, file_sha) = tree_lookup_path(r.get_object, tree, path)
    return r[file_sha].data

class Git:
    """ a wrapper around www.dulwich.io - python git interface """
    
    def __init__(self):
        pass

    def add_and_commit_all(self):
        """ add and commit all changed files as user admin """
        # Used after creating a new course.
        # See https://www.dulwich.io/apidocs/dulwich.porcelain.html#add
        try:
            # This apparently has unicode path conversion issues
            # on the production server.
            porcelain.add(os_git, paths=None)
            porcelain.commit(os_git, '--message=user:admin')
        except:
            # Instead just run umber_cleanup (which also commits changed files)
            # in a fork.
            # OOPS - this doesn't work either.
            pid = os.spawnlp(os.P_NOWAIT, umber_cleanup, 'umber_cleanup', '')
    
    def add_and_commit(self, page, abspath=None):
        """ commit abspath or this page or this folder to git repo """
        # path vs relative seems strangely picky - this one wants abspath.
        if not abspath:
            page.keep()                 # if folder, create ./.keep file
            abspath = page.keepabspath  # page.abspath or folder's .keep
        porcelain.add(os_git, paths=[abspath])
        porcelain.commit(os_git, '--message=user:{}'.format(page.user.username))
        
    def rm_and_commit(self, page, abspaths):
        """ remove files and folders (absolute paths) & commit changes """
        # -- page is the folder from which the delete form was submitted.
        relpaths = [os.path.relpath(x, os_git) for x in abspaths]
        page.keep()
        porcelain.rm(os_git, paths=relpaths)
        porcelain.commit(os_git, '--message=user:{}'.format(page.user.username))
        # This porcelain.rm seems to sometimes not delete the file itself.
        for abspath in abspaths:
            try:
                os.remove(abspath)
            except:
                pass

    def log(self, page):
        """ return revisions and dates of a given file as [(githash, date, author)]"""
        # The path seems to be picky here - wants not abspath but relative to os_git.
        relpath = os.path.relpath(page.abspath, os_git)
        buffer = io.StringIO()
        porcelain.log(os_git, paths=[relpath], outstream=buffer)
        logstring = buffer.getvalue()
        print_debug('  dulwich git log for {} is {}'.format(page.abspath, logstring))
        return parse_porcelain_log(buffer.getvalue())
    
    def get_revision(self, page):
        """ Return content from a git version of a page """
        # page.revision:     (new) current 4 3 2 1 (old) page.revision
        # page.githashes     (new) 0       1 2 3 4 (old) if 5 revisions
        index = len(page.githashes) - page.revision
        commit_sha = str(page.githashes[index])
        relpath = os.path.relpath(page.abspath, os_git)        
        return dulwich_get_file_revision(os_git, commit_sha, relpath)

git = Git()

# -- icons for file types and their file extensions --
_icon_map = {'text' : ('text.gif', ('txt', 'css', 'rtf', 'html',
                                   'wiki', 'md', 'markdown')),
             'video' : ('movie.gif', ('mpeg', 'mov', 'movie', 'avi', 'qt',
                                     'mpg', 'mp4', 'mkv') ),
             'audio' : ('sound2.gif', ('wav', 'ram', 'aif', 'au', 'midi',
                                      'mp3', 'mp2', 'snd') ),
             'image' : ('image2.gif', ('gif', 'xbm', 'png', 'ico', 'tiff',
                                       'svg', 'pict', 'jpeg', 'jpg', 'jp2')),
             'code' : ('script.gif', ('sh', 'pl', 'java', 'js', 'c', 'cc',
                                      'rb', 'go', 'lisp', 'cc', 'c++',
                                      'hs', 'py')),
             'doc' : ('a.gif',('pdf', 'doc', 'ps', 'tex', 'dvi')),
             'unknown' : ('unknown.gif', [] ),
             'generic' : ('generic.gif', [] ),
             'binary' : ('binary.gif',   ('bin', 'exe')),
             'back' : ('back.gif',       [] ),
             'compressed' : ('compressed.gif', ('gz', 'tar',
                                                'zip', 'dmg', 'hqx') ),
             'directory'  : ('folder.gif', [] )
           }
ext_to_filetype = {}
filetype_to_icon = {}
for (filetype, (icon, extensions)) in list(_icon_map.items()):
    filetype_to_icon[filetype] = os.path.join('icons', icon)
    for ext in extensions:
        ext_to_filetype['.' + ext] = filetype

allowed_chars = set(string.ascii_lowercase + string.digits + '_')
def is_clean_folder_name(name):
    """ Return true if string has only chars (1-9, a-z, _) """
    # TODO: speed this up ?
    # from stackoverflow.com/questions/1323364/
    # in-python-how-to-check-if-a-string-only-contains-certain-characters
    return set(name) <= allowed_chars

def static_url(filename):
    return url_for('static', filename=filename)

def size_in_bytes(n):
    """ Convert to human readable bytes size K,M,G, etc
        >>> size_in_bytes(123)
        '123B'
        >>> size_in_bytes(1234)
        '1.2K'
        >>> size_in_bytes(1280)
        '1.3K'
        >>> size_in_bytes(12345)
        ' 12K'
        >>> size_in_bytes(123888)
        '124K'
        >>> size_in_bytes(1234567)
        '1.2M'
        >>> size_in_bytes(12945678)
        ' 13M'
        >>> size_in_bytes(123456789)
        '123M'
        >>> size_in_bytes(1234567890)
        '1.2G'
        >>> size_in_bytes(12645678900)
        ' 13G'
    """
    if not n:
        return ''
    if n < 1000:
        return '{:3}B'.format(n)
    elif n < 10000:
        return '{:3}K'.format( (((n+50) // 100) * 100) / 1000.0)
    elif n < 1000000:
        return '{:3}K'.format( (n+500) // 1000 )
    elif n < 10000000:
        return '{:3}M'.format( (((n+50000) // 100000) * 100000) / 1000000.0)
    elif n < 1000000000:
        return '{:3}M'.format( (n+500000) // 1000000)
    elif n < 10000000000:
        return '{:3}G'.format( (((n+50000000) // 100000000) * 100000000) / 1000000000.0)
    else:
        return '{:3}G'.format((n+500000000) // 1000000000)

def link_translate(course, html):
    """ return html string with ~/ and ~~/ links translated
        into the appropriate course and site urls """
    html = html.replace('~~/', '/' + url_base + '/')
    # for site course, url ends with / ; for others, it doesn't.
    if course.url[-1] == '/':
        course_url_with_slash = course.url
    else:
        course_url_with_slash = course.url + '/'
    html = html.replace('~/', course_url_with_slash)
    return html

def whitestrip(x):
    """ strip whitespace """
    # translate() fails when x is unicode.
    # return string.translate(x, None, deletions=string.whitespace)
    return re.sub(r'\s+', '', x)

def stringify_access(rights):
    """ convert list or string to list with commas """
    # [u'frank', u'bob'] => 'frank, bob'
    # u'joe'  => 'joe'
    if type(rights) == type('') or type(rights) == type(''):
        return str(rights)
    else:
        return str(', '.join(rights))

def parse_access_string(access):
    """ Convert a string of roles and/or usernames to a string or list """
    # 'frank' => 'frank'
    # 'frank, faculty' => ['frank', 'faculty']
    names = re.split(r'\s*,\s*|\s+', access) # split on commas and/or whitespace
    names = list(map(whitestrip, names))
    names = [x for x in names if len(x)>0]
    if len(names) == 1:
        names = names[0]
    return names

def make_marker(bits=64):
    """ Return a unique string that , for marking boundaries in text """
    #  i.e. '|-b1dda1c7f14cd89e-|'
    # In python2, hex() on big numbers gives i.e. '0x3333333333L'.
    # I'll drop the 1st two and last chars with [2:-1].
    return '|-'+hex(random.getrandbits(64))[2:-1]+'-|'

def mathjax_replace(text):
    """ Replace substrings of text between several boundaries
        $$...$$ ,  \(...\) , \[...\] with unique-ish boundary markers.
        Return new text and dictionary of markers and replaced substrings.
    """
    replacements = {}
    for expr in (r'\$\$.*?\$\$',       #   $$ ... $$
                 r'\\\(.*?\\\)',       #   \( ... \)
                 r'\\\[.*?\\\]'):      #   \[ ... \]
        pattern = re.compile(expr)
        while True:
            match = re.search(pattern, text)
            if not match:
                break
            substring = match.group(0)
            m = make_marker()
            replacements[m] = substring
            text = text.replace(substring, m)
    return (text, replacements)

def undo_mathjax_replace(text, replacements):
    for mark in replacements:
        text = text.replace(mark, replacements[mark])
    return text

def markdown2html(string, extras=True):
    """ Convert markdown-formatted text to html 
        >> markdown2html(r'Formula \\( \\frac{1}{x} \\)')
        u'<p>Formula \\( \\frac{1}{x} \\)</p>\n'
    """
    #print_debug(u" markdown2html: string before replace '{}'".format(string))    
    (string, replacements) = mathjax_replace(string)
    #print_debug(u" markdown2html: string after replace '{}'".format(string))
    if extras:
        output = markdown(string,
                    extras=['code-friendly', 'fenced-code-blocks',
                            'footnotes', 'pyshell', 'tables',
                            'cuddled-lists', 'markdown-in-html'])
    else:
        output = markdown(string)
    #print_debug(u" markdown2html: string after markdown '{}'".format(string))
    #print_debug(u" markdown2html: replacemements '{}'".format(unicode(replacements)))
    output = undo_mathjax_replace(output, replacements)
    #print_debug(u" markdown2html: string after undo ''".format(string))  
    #
    # markdown2 bug fix :
    #   query string & should not be escaped to &amp;
    #   semi colons should not be inserted into link
    href_amp = re.compile(r'href=([^\s>]*)&amp;')
    href_semi = re.compile(r'href=([^\s>]*);')
    while re.search(href_amp, output):
        output = re.sub(href_amp, r'href=\1&', output)
    while re.search(href_semi, output):
        output = re.sub(href_semi, r'href=\1', output)
    # ---
    return output

def split_url(urlpath):
    """ Given e.g. 'foo/bar/baz.html?this=that&color=red', 
        return ('foo/bar/baz', '.html', '?this=that&color=red') """
    (scheme, netloc, path, query, fragment) = urllib.parse.urlsplit(urlpath)
    (base, ext) = os.path.splitext(path)
    return (base, ext, query)

def pygment_webpage(filename, body):
    """ Return html webpage for pygmentized code """
    pygments_css = static_url('styles/pygment.css')
    try:
        body = body.encode('utf8')
    except:
        pass
    return """
<html>
<head>
<title>{}</title>
<link rel="stylesheet" type="text/css" href="{}">
</head>
<body>
{}
</body>
</html>
""".format(filename, pygments_css, body)

def pygmentize(code, filename=None, language=None):
    """ return html syntax higlighted code """
    # See  - http://pygments.org/docs/quickstart/ .
    #      - http://pygments.org/docs/quickstart/#guessing-lexers
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name, guess_lexer, \
                                guess_lexer_for_filename
    if filename:
        lexer = guess_lexer_for_filename(filename, code) # add stripall=True ?
    elif language:
        lexer = get_lexer_by_name(language)
    else:
        lexer = guess_lexer(code)
    formatter = HtmlFormatter(linenos=False, cssclass='codehilite')
    code_as_html = highlight(code, lexer, formatter)
    return pygment_webpage(filename, code_as_html)


def in_console():
    """ Return True if current environment is the flask console """
    # See $UMBER_ROOT/bin/umber_console
    return 'UMBER_CONSOLE' in os.environ

if __name__ == '__main__':
    import doctest
    doctest.testmod()
