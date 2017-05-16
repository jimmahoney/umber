# -- coding: utf-8 --
"""
 utilities.py
"""
import os

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


def in_console():
    """ Return True if current environement is the flask console """
    # See $UMBER_ROOT/bin/umber_console
    return os.environ.has_key('UMBER_CONSOLE')

