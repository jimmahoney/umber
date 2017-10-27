# -- coding: utf-8 --
"""
 utilities.py
"""
import os, urlparse, sh, arrow, string, re
from markdown2 import markdown
from settings import url_basename, os_base, timezone, timezoneoffset
from flask import url_for

class Time(object):
    """ Time in an ISO GMT form, as typically stored in the sqlite database,
        including a timezone-aware (as specified in settings.py) offset.
        >>> print Time('2013-01-01T12:24:52.3327-05:00')
        2013-01-01T12:24:52-05:00
        >>> print Time('2013-05-09') # daylight savings => -4 from GMT
        2013-05-09T13:00:00-04:00
        >>> print Time('2013-01-09') # not daylight savings => -5 from GMT
        2013-01-09T12:00:00-05:00
    """
    # Uses the python Arrow library; see http://crsmithdev.com/arrow/  .
    # For time differences, subtract two of these (given a datetime.timedelta)
    # and then use .seconds, .total_seconds(), .resolution etc.
    #
    # The string format is like that described
    # at http://momentjs.com/docs/#/displaying/format/
    
    def __init__(self, *args, **kwargs):
        """ With no arguments, returns the 'now' time. """
        # And if the arg is just e.g. '2015-01-02', add utc 'T12:00:00-05:00'
        # (Apparently an ISO string date string like '2015-12-01' ignores
        #  the tzinfo optional arg. However
        #  arrow.get(datetime.date(2015,12,01), tzinfo=timezone) does work.)
        if len(args)>=1 and isinstance(args[0], basestring) \
                        and len(args[0])==10:
            args = (args[0] + 'T12:00:00' + timezoneoffset,) +  args[1:]
        self.arrow = arrow.get(*args, **kwargs).to(timezone)
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

class Git:
    """ a wrapper around sh.git """
    
    def __init__(self):
        self._git = sh.git.bake(_cwd=os_base, _tty_out=False)

    def rm_and_commit(self, page, abspaths):
        """ remove files and folders (absolute paths) & commit changes """
        # -- page is the folder from which the delete form was submitted.
        page.keep()
        self._git.rm('-r', *abspaths)
        self._git.commit('--message=user:{}'.format(page.user.username),
                         *abspaths)
        
    def add_and_commit(self, page, abspath=None):
        """ commit abspath or this page or this folder to git repo """
        if not abspath:
            page.keep()                 # if folder, create ./.keep file
            abspath = page.keepabspath  # page.abspath or folder's .keep
        self._git.add(abspath)
        self._git.commit('--message=user:{}'.format(page.user.username), abspath)
        
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
    html = html.replace('~/', course.url + '/')
    html = html.replace('~~/', '/' + url_basename + '/')
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
    
def markdown2html(string):
    # See https://github.com/trentm/python-markdown2
    #     https://github.com/trentm/python-markdown2/wiki/Extras
    output = markdown(string,
                    extras=['code-friendly', 'fenced-code-blocks',
                            'footnotes', 'pyshell', 'tables',
                            'cuddled-lists', 'markdown-in-html'])
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
