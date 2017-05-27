# -- coding: utf-8 --
"""
 markup.py

 See
   * https://github.com/trentm/python-markdown2
   * https://github.com/trentm/python-markdown2/wiki/Extras
  
"""

from model import Role
from markdown2 import markdown
from bs4 import BeautifulSoup
from settings import url_basename, os_root
import re, os

def markdown2html(string):
    return markdown(string,
                    extras=['code-friendly', 'fenced-code-blocks',
                            'footnotes', 'pyshell', 'tables',
                            'cuddled-lists', 'markdown-in-html'])

def nav2html(page):
    """ return authorized parts of page as html """
    # The menu navigation page has html tags that look like this :
    #    <div access='student'>
    #    ...
    #    </div>
    # 
    parser = BeautifulSoup(page.content(), 'html.parser')
    for role in ['admin', 'student', 'faculty', 'guest']:
        divs = parser.find_all('div', access=role)
        for div in divs:         # add attribute that will set markdown2
            div['markdown'] = 1  # to process markdown within this div tag.
        if page.user_rank < Role.by_name(role).rank:
            for div in divs:
                div.extract() # remove this div from its parent parser
    return markdown2html(str(parser))

nav_test = """
<div access='all' >
### course ###
* [home](~/home)
* [syllabus](~/syllabus)
* [resources](~/resources)
* [class notes](~/notes/home)
* [assignments](~/special/assignments)
</div>
<div access='student' >
### student ###
* [roster](~/special/roster)
* [grades](~/special/grades)
</div>
<div access='faculty' >
### faculty ###
* [add students](//special/users)
* [edit navigation](//navigation)
* [private](~/private)
</div>
<div access='admin' >
### admin ###
* [site home](//home)
* [all courses](//special/courses)
* [all users](//special/users)
</div>
<div access='all' >
### navigation ###
* [help](//help)
* <a href='..'>..</a>
* <a href='.'>.</a>
</div>
"""

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    print "------ navtest --------"
    nav_html = markup(nav_test)
    print nav_html
