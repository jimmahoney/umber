# -- coding: utf-8 --
"""
 utilities.py
"""
import os, urlparse, sh
from markdown2 import markdown
from settings import url_basename, os_base
from flask import url_for

class Git:
    """ a wrapper around sh.git """
    # self._git.log('--date=iso', '--format=(%H,%cd,%s)', 'demo/home.md')
    def __init__(self):
        self._git = sh.git.bake(_cwd=os_base)
    def add_and_commit(self, page):
        # This gets called after page is modified.
        self._git.add(page.path)
        self._commit('-m "user:"'.format(page.user.username), page.path)
    def log(self, page):
        # self._git.log('--date=iso', '--format=(%H,%cd,%s)', 'demo/home.md')
        pass

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

#class ActionHTML(object):
#    """ Return
#            tabs        e.g.  ['edit', 'history', ...]
#            styles      e.g.  {'edit':'style', ...}
#            uris        e.g.  {'edit':'base?action=edit', ...}
#            links       e.g.  {'edit':'edit', ...
#    """
#    def __init__(self, page):
#        self.tabs = []
#        self.style = {}
#        self.uri = {}
#        self.link = {}
#        if page.can['write']:
#            self.tabs = ['edit', 'history']
#            self.style = {'edit' : 'behind',
#                          'history' : 'behind' }
#            self.uri = {'edit' : '?action=edit',
#                        'history' : '?action=history' }
#            self.link = {'edit' : 'edit',
#                         'history' : 'history' }

def link_translate(course, html):
    """ return html string with ~/ and ~~/ links translated
        into the appropriate course and site urls """
    html = html.replace('~/', course.url + '/')
    html = html.replace('~~/', '/' + url_basename + '/')
    return html

def unlinkify(page, html):
    """ Return html string with any absolute urls to page unlinkified """
    

def markdown2html(string):
    # See https://github.com/trentm/python-markdown2
    #     https://github.com/trentm/python-markdown2/wiki/Extras
    return markdown(string,
                    extras=['code-friendly', 'fenced-code-blocks',
                            'footnotes', 'pyshell', 'tables',
                            'cuddled-lists', 'markdown-in-html'])
            
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
