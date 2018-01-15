# -- coding: utf-8 --
"""
 utilities.py
"""
import os, urlparse, sh, arrow, string, re
from markdown2 import markdown
from settings import URL_BASE,DEBUG, LOCALTIMEZONE, LOCALTIMEZONEOFFSET, OS_GIT
from flask import url_for
import parsedatetime, pytz

def print_debug(message):
    if DEBUG:
        print message

class Time(object):
    """ Time in an ISO GMT form, as typically stored in the sqlite database,
        including a timezone-aware (as specified in settings.py) offset.
        >>> print Time('2013-01-01T12:24:52.3327-05:00')
        2013-01-01T12:24:52-05:00
    """
    # Uses the python Arrow library; see http://crsmithdev.com/arrow/  .
    # For time differences, subtract two of these (given a datetime.timedelta)
    # and then use .seconds, .total_seconds(), .resolution etc.
    #
    # The string format is at http://momentjs.com/docs/#/displaying/format/
    #
    # Since I'm using these mostly for assignment due dates, if a date is given
    # without a time, then the time will by default be set to 11:59pm local.

    defaulttime = '11:59 pm'
    default24time = '23:59:00'
    
    @staticmethod
    def parse(date_time_string):
        """ Return Time object from human friendly description 
            i.e. Time.parse('tomorrow') """
        # If a time isn't given (i.e. found via regex search)
        # then it's set to the default.
        # The timezone is local - see settings.py.
        date_time_string = str(date_time_string)  # convert from utf8 if needed
        if 'midnight' in date_time_string:
            date_time_string = date_time_string.replace('midnight',
                                                        Time.defaulttime)
        if not re.search('am|pm|noon|morning|afternoon|evening', date_time_string):
            date_time_string += ' ' + Time.defaulttime
        datetime = parsedatetime.Calendar().parseDT(
           datetimeString=date_time_string,
           tzinfo=pytz.timezone(LOCALTIMEZONE))[0]
        return Time(datetime)
        
    def __init__(self, *args, **kwargs):
        """ With no arguments, returns the 'now' time. """
        # If an iso date string is given without a time i.e. '2017-11-01'
        # then the time will be set to the default 23:59:00 local.
        # I'm checking for that explicit case here and adjusting accordingly.
        # >>> str(Time('2017-12-02'))
        # '2017-12-02T23:59:00-05:00'   where -5 is US/Eastern localtimezone
        # >>> Time('2017-12-02').isodate()
        # '2017-12-02'
        if len(args)==1 and isinstance(args[0], basestring):
            #if re.match('\d+-\d+-\d+T\d+:\d+:\d+(-|+)\d+:\d+', args[0]):
            #    # i.e. '2017-12-02T23:59:00-05:00'
            #    pass  # just leave it alone
            if args[0] == '':
                args[0] = None
            if re.match('^\d+-\d+-\d+$', args[0]):
                    # i.e. '2018-02-04'
                args = (args[0] + 'T' + Time.default24time + \
                        LOCALTIMEZONEOFFSET ,)
        try:
            self.arrow = arrow.get(*args, **kwargs).to(LOCALTIMEZONE)
        except:
            self.arrow = arrow.get() # use current time if all else fails.
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
        month = self.arrow.month
        if month < 6:
            season = 'Spring '
        elif month < 9:
            season = 'Summer '
        else:
            season = 'Fall'
        return season + str(self.arrow.year)
    def str(self):
        return str(self)

def parse_assignment_data(request_form):
    """ Return a dict assignments_data[nth][name, due, blurb] from request form data 
        >>> data = {'assignment_name_2':'readings', 'assignment_due_2':'2017-02-03'}
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
            if not assignment_data.has_key(nth) and request_form[key]:
                assignment_data[nth] = {}
            assignment_data[nth][which] = request_form[key]
    return assignment_data
    
class Git:
    """ a wrapper around sh.git """
    
    def __init__(self):
        self._git = sh.git.bake(_cwd=OS_GIT, _tty_out=False)

    def rm_and_commit(self, page, abspaths):
        """ remove files and folders (absolute paths) & commit changes """
        # -- page is the folder from which the delete form was submitted.
        page.keep()
        self._git.rm('-r', *abspaths)
        try:
            self._git.commit('--message=user:{}'.format(page.user.username),
                                 *abspaths)
        except Exception as err:
            print_debug("git rm_and_commit error '{}'".format(err))
        
    def add_and_commit(self, page, abspath=None):
        """ commit abspath or this page or this folder to git repo """
        if not abspath:
            page.keep()                 # if folder, create ./.keep file
            abspath = page.keepabspath  # page.abspath or folder's .keep
        self._git.add(abspath)
        try:
            self._git.commit('--message=user:{}'.format(page.user.username), abspath)
        except Exception as err:
            print_debug("git add_and_commit error '{}'".format(err))

    def log(self, page):
        # _git.log gives '(revision,date,user:who)\n(revision,date,user:who)'
        lines = self._git.log('--date=iso-strict',
                              '--format=(%H,%cd,%s)',
                              page.abspath).split('\n')
        valid_lines = filter(lambda x: len(x) > 2, lines)
        data = map(lambda line:line[1:-1].split(','), valid_lines)
        for rev in data:
            rev[1] = Time(rev[1]).daydatetimesec()
            if (len(rev[2]) < 6) or rev[2][:5] != 'user:':
                rev[2] = ''
            else:
                rev[2] = rev[2][5:]
        return(data)
    
    def get_revision(self, page):
        """ Return content from a git version of a page """
        # page.revision:     (new) current 4 3 2 1 (old) page.revision
        # page.githashes     (new) 0       1 2 3 4 (old) if 5 revisions
        index = len(page.githashes) - page.revision
        descriptor =  str(page.githashes[index]) + ':' + page.gitpath
        return str(self._git.show(descriptor))

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
for (filetype, (icon, extensions)) in _icon_map.items():
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
    html = html.replace('~~/', '/' + URL_BASE + '/')
    html = html.replace('~/', course.url + '/')
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
    if type(rights) == type('') or type(rights) == type(u''):
        return str(rights)
    else:
        return str(', '.join(rights))

def parse_access_string(access):
    """ Convert a string of roles and/or usernames to a string or list """
    # 'frank' => 'frank'
    # 'frank, faculty' => ['frank', 'faculty']
    names = re.split(r'[ ,\t]', access) # split on commas or spaces
    names = map(whitestrip, names)
    names = filter(lambda x: len(x)>0, names)
    if len(names) == 1:
        names = names[0]
    return names
    
def markdown2html(string, extras=True):
    # See https://github.com/trentm/python-markdown2
    #     https://github.com/trentm/python-markdown2/wiki/Extras
    if extras:
        output = markdown(string,
                    extras=['code-friendly', 'fenced-code-blocks',
                            'footnotes', 'pyshell', 'tables',
                            'cuddled-lists', 'markdown-in-html'])
    else:
        output = markdown(string)
    # ---
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
    (scheme, netloc, path, query, fragment) = urlparse.urlsplit(urlpath)
    (base, ext) = os.path.splitext(path)
    return (base, ext, query)

def in_console():
    """ Return True if current environement is the flask console """
    # See $UMBER_ROOT/bin/umber_console
    return os.environ.has_key('UMBER_CONSOLE')


if __name__ == '__main__':
    import doctest
    doctest.testmod()
