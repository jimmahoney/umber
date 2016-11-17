# -- coding: utf-8 --
"""
 markup.py

 See
   * https://github.com/trentm/python-markdown2
   * https://github.com/trentm/python-markdown2/wiki/Extras
  
"""

from markdown2 import markdown
from bs4 import BeautifulSoup
from settings import url_basename, os_root
import re, os

def markup(string):
    return markdown(string,
                    extras=['code-friendly', 'fenced-code-blocks',
                            'footnotes', 'pyshell', 'tables',
                            'cuddled-lists', 'markdown-in-html'])

def nav_content(page):
    """ return authorized parts of page's course's navigation file """
    with open(os.path.join(page.course.nav_os_path())) as file:
        content = file.read()
    parser = BeautifulSoup(content, 'html.parser')
    for role in ['admin', 'student', 'faculty', 'guest']:
        divs = parser.find_all('div', access=role)
        if page.user_rank < Role.by_name(role).rank:
            for div in divs:
                div.extract() # modifies parser object
    return str(parser)

nav_test = """
<div access='all' markdown='1'>
### course ###
* [home](~/home)
* [syllabus](~/syllabus)
* [resources](~/resources)
* [class notes](~/notes/home)
* [assignments](~/special/assignments)
</div>
<div access='student' markdown='1'>
### student ###
* [roster](~/special/roster)
* [grades](~/special/grades)
</div>
<div access='faculty' markdown='1'>
### faculty ###
* [add students](//special/users)
* [edit navigation](//navigation)
* [private](~/private)
</div>
<div access='admin' markdown='1'>
### admin ###
* [site home](//home)
* [all courses](//special/courses)
* [all users](//special/users)
</div>
<div access='all' markdown='1'>
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
