# -- coding: utf-8 --
"""
 utilities.py
"""
import os
import urlparse
from markdown2 import markdown
from settings import url_basename

class ActionHTML(object):
    """ Return
            tabs        e.g.  ['edit', 'history', ...]
            styles      e.g.  {'edit':'style', ...}
            uris        e.g.  {'edit':'base?action=edit', ...}
            links       e.g.  {'edit':'edit', ...
    """
    def __init__(self, page):
        self.tabs = []
        self.style = {}
        self.uri = {}
        self.link = {}
        if page.can['write']:
            self.tabs = ['edit', 'history']
            self.style = {'edit' : 'behind',
                          'history' : 'behind' }
            self.uri = {'edit' : '?action=edit',
                        'history' : '?action=history' }
            self.link = {'edit' : 'edit',
                         'history' : 'history' }

def link_hacks(course, html):
    """ return html with ~/ and ~~/ links translated
        into the appropriate course and site urls """
    html = html.replace('~/', course.url + '/')
    html = html.replace('~~/', '/' + url_basename + '/')
    return html
            
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

