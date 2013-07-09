# umber development history #

## June 26 2013 ##

The wikiacademia software I've been using for course management at the
college is feeling pretty crufty. Most of the systems it relies on are
dated, and updating all of 'em is going to be a pain. So I think that
instead I'll just move the whole thing to a new platform. While this
may be a classic case of the "rewrite blunder", it'll give me a chance
to explore some other technologies, and since I know pretty much what
I want, should be fairly straightfoward.

For now at least I'm calling this new version "umber", inspired by
"brown" for "Brown Science Building".  It's at least short,
pronouncable, and the umber.cc domain is currently available.

I've pulled a current copy of the HTML::Mason software from
cs.marlboro.edu/var/www/cs stripped out all but the essential code for
wikiacademia and put it and the 2006 version in
~/academics/wikiacademia/ .

All this is currently on my MacPro, OS X 10.8.4 .

* Updated the basic tools: python (2.7.5), pip (1.31), virtualenv (1.9.1),
  and git (to 1.8.3.1, manually from git-scm.com, including running 
  a script to make its environment available to non-terminal applications.)

        $ sudo port upgrade python27
        $ sudo pip install --upgrade pip
        $ sudo pip install --upgrade virtualenv

* Using markdown for docs, with html conversion (when needed)
  by a [python markdown package](https://pypi.python.org/pypi/Markdown) ;
  see http://pythonhosted.org/Markdown/reference.html#markdown
 
        $ sudo pip install markdown
        # e.g. "markdown_py file.md > file.html"

* Setup initial directories, environment, git repo.
  (See ~/academics/web_development/flask/planet_express from 
   my Fall '12 Web Programming.)

        $ cd /Users/mahoney/academics/
        $ mkdir umber; cd umber ; mkdir docs
        $ mkdir src/ static/ templates/ database/   
        # Manually edited README.md and docs/history.md (this file).

        # Create umber/env folder with python & package environment :
        $ virtualenv -p python2.7 env  # /opt/local/bin/python2.7 is 2.7.5
        # To move into the local development environment, do
        #   $ . env/bin/activate"
        # (I typically have 'activate' aliased to that.)

        # Setup project's source git repo :
        $ git init ; git add * ; git commit -m "initial commit"
        # See hints at http://rogerdudler.github.io/git-guide/
        $ git config color.ui true ; git config format.pretty oneline
        # (Workflow after changes will be "git add ...; git commit -m ...".)

## June 27 ##

* Copyied and adapted basic Flask resources from planet_express,
  including requirements.txt, __init__.py, templates/index.html,
  src/utilities.py, src/console.py, console, 
  and planet_express.py renamed umber.py

* Installing Flask, SQLAlchemy (and anything else listed in requirements.txt).

        $ . env/bin/activate
        $ (env)$ pip install -r requirements.txt
        ...
        Successfully installed Flask SQLAlchemy Werkzeug Jinja2 
        itsdangerous markupsafe

* Fetched various wikiacademia resource files :

        $ mkdir static/images; mkdir static/styles
        $ scp cs.marlboro.edu:/var/www/cs/htdocs/courses/source/images/* \
           static/images/
        $ scp cs.marlboro.edu:/var/www/cs/htdocs/courses/source/styles/* \
           static/styles/

* Started work on sqlite database based on wikiacademia's 
  but using planet_express conventions. 

        # Create database
        $ cd database; sqlite3 umber.db < create_umber_db.sql

## June 28 & 29 ##

* Have basic database working, including Demo Course 
  and tests in model.py 

## June 30 ##

Looking at multiple-word search across text.
The Aho-Corasick implementation at
https://pypi.python.oerg/pypi/ahocorasick/0.9 looks interesting,
but it crashed when I tried it.
    $ (env) umber$ pip install ahocorasick
    $ python
    >>> import ahocorasick
    >>> tree = ahocorasick.KeywordTree()
    >>> tree.add("alpha")
    Bus error: 10
    $
    $ pip uninstall ahocorisck

This pure python implementation from http://0x80.pl/proj/pyahocorasick/ 
looks fine for my purposes.
    $ cd src; wget pyahocorasick.py
    $ python
    >>> from pyahocorasick import Trie
    >>> t = Trie()
    >>> for w in ('fall2012/algorithms', 'fall2012/python'):
    ...   t.add_word(w, w)    # (word, value) ; same for my purposes
    >>> t.make_automaton()    # finalize word collection as search engine
    >>> 
    >>> list(t.iter('This is a string that has no match'))  
    []
    >>> s = '/courses/fall2012/python/has/match'
    >>> list(t.iter(s))
    [(23, ['fall2012/python'])]    # (index of last char, [list_of_matches])
    >>> s[23 - len('fall2012/python') + 1 : (23 + 1)]
Can provide start or end for search string, e.g. iter('....', start) 
or iter('',start,end). For my purposes, there is a prefix (e.g. '/courses'),
a course directory stored in the database (e.g. '/

## July 1 ##

Looking at wiki parsers.

mwlib is a python MediaWiki available via pip install, 
but it took a bit of googling and futzing to get it working.
stackoverflow.com/questions/7630388/how-can-i-install-the-python-library-gevent-on-mac-os-x-lion
    $ sudo port install libevent
    $ CFLAGS="-I /opt/local/include -L /opt/local/lib" pip install gevent

See http://djangosnippets.org/snippets/1277/ for an example of using this

Looks like overkill - huge, awkward, database-of-articles, ... eh.

There are several simpler ones based on wiki creole, which is close
to what I use. Main difference is they use {{{  }}} for code & preformatted.
Not sure what they do with existing HTML, but could be worked around.
Also HR is exactly four dashes : ---- . Links are [[url|name]] ...
though I think I sometimes reverse that on my site.

It would take some adapting and/or pre-processing, but I think 
one of these may work.

    $ pip info creole
    python-creole  https://pypi.python.org/pypi/python-creole/ 
                   pure python ; macros as <<...>> 
    Flask-Creole   based on python-creole
    Creoleparser   bigger; has some support for dialect customization ; requires Genshi
    creole         somewhat smaller https://bitbucket.org/thesheep/wikicreole/wiki/Home

Here's a "pass thru macro" for marking pieces of text to go through unchanged.
Note that the input and output must be unicode; 
see https://code.google.com/p/python-creole/wiki/CreoleMacros
    >>> creole2html(u'one two <<html>><p>paragraph</p><</html>> three', 
    ...             macros={'html':lambda text='':text})

## July 3 ##

Generated a new random background image, pale tan (i.e. umber) color;
see images/random_umber.* . (Actually run at cs.marlboro.edu/images/* 
in old wikiacademia environment.)

## July 5 ##

Look at the available Flask extensions at http://flask.pocoo.org/extensions/ :
    Flask-Testing, 
    Flask-Uploads (file uploading), 
    Flask-WeasyPrint (pdf generation), 
    Flask-SeaSurf (prevent cross-site request forgery), 
    Flask-Restless (generate REST APIs), 
    Flask-Principal (identify management),
    Flask-Login (via session), 
    Flask-OpenID, 
    Flask-Gravatar,
    Flask-Mako (an alternative to the Jinja2 templates with *real* python),
    Flask-Mail (sending email),
    flask-lesscss (css scripting),
    Flask-FlatPages (flat static pages based on text files),     (??)
    Flask-DebugToolbar (Django style),
    Flask-Dashed (admin dashboard inteface),
    Flask-Cache,
    Flask-Bcrypt (for hashing passwords),
    Flask-Assets (webassets library for minifying and compiling CSS and JS),
    Flask-Admin (admin interface)

Also http://flask.pocoo.org/snippets/ , including security, sessions, 
authentication, and a lot more.

I think that I'd rather use Mako than Jinja2 for templating,
and I haven't gone so far that changing should be too much work;
see http://www.makotemplates.org/. Besides using a language 
much closer to real python, it also is reminiscent of Mason,
including the leading % signs for code.

## July 6 ##

The Mako templates work, but the error handling sucks.

The generated flask error page - which worked great 
for the jinja2 templates - is fairly useless for Mako.
This is a significant hit against an otherwise nice 
template engine.

Also, the mako filter syntax is ugly : ${a | filter1, filter2} rather
than what anyone familiar with filters (i.e. unix pipes) would expect,
${a | filter1 | filter2} .  One explanation in the comments is that |
is already part of python (bitwise or). I don't really buy that
argument, since that would suggest that the whole filter syntax 
itself is bogus.

Working on login via Flask-Login, passwords (see model.py comments),
ldap (started) - slow piecemeal progress; heading towards the 
main template with user login.

    $ sudo port install openldap
    $ pip install Python-LDAP

Installed other python libraries as listed in requirement.txt .

See stackoverflow.com/questions/82831/how-do-i-check-if-a-file-exists-using-python
for thinking about checking .access.yaml files. Also PyYAML.

Have working mainroute at commit 'main.html with mako works' at [master 6e79ed0].

## July 9 ##

Mucking about with login, which is (after a lot of trial and error)
now working. New role-based icons are in place.

The Mako templating system is, I'm afraid, more of a disappointment
than I'd expected. While it's close to python, it isn't really 
python: endif and endfor required to stop blocks; context of 
variables not obvious (i.e. "x=5" just crashes, since one
can just introduce a new variable into the context) and caching
trickiness means that capture() etc may be needed to do things
which seem straightforward.

The biggest problem is debugging - template errors are not reported in
a way that is at all helpful - the whole template either succeeds or
(mysteriously) fails. Flask's built-in templating system handles
this much, much beter, as I remember.

The notion of arguments sent to templates is an idea that I like - and
used in Mason - but so far I'm just passing the entire context anyway.
With Mason, that let me test subcomponents independently. But here,
I'd need to set up separate routes for that (since I'm using 'include'
and not inheritance, since my dispatch is 'course' and not just URL
based), and so the subcomponents can't be tested/run as smaller 
pieces ... and thus lose much of their value.

The project is moving towards the model of Flask-Login and the more
typical "code-in-the-model" or "code-in-the-controller", so the
smaller components are not as independent as in the Mason case,
where I had the submission handling was bundled with the forms.

For now I'll stick with Mako anyway. But.

Next: courses, files, pages, folder permissions and all that.

I think that this time around I will have a Folder object in the
database, with all permissions there rather than in the (slow)
.access.yaml files I used before.

That means, though, that'll I think I'll need a database-side
infrastructure to automatically add/remove folders and 
permissions if the file structure has changed.

- - - 

# Thinking / TODO #

* Git within the project : 
 http://stackoverflow.com/questions/1456269/python-git-module-experiences
 Do I need to think about directory structure for git repo
 of web app source vs site course files ??
 * I think I'll just use one git repo, and put site-specific files in a branch;
   see http://www.atlassian.com/git/tutorial/git-branches

* directory structure
  * templates/   : the render engeine looks here; I'll leave 'em.
  * static/      : may be redundant given I want a *.wiki etc hierarchy
  * htdocs/      : my non-flasky file structure of .wiki, .md, .html, .txt, ...
    or courses/    (i.e. the url prefix for these umber course wiki thingies)

http://flask.pocoo.org/mailinglist/archive/2011/5/6/efficiency-and-large-numbers-of-routes/#84e814641458d772989f33af3e4b9548
 * route efficiency?
   * Yes, route search is O(n) worst.
   * database access is typically much slower than in memory stuff,
     so that may not matter anyway.
 * If I just put in one route per course, that's only 
   currently about 200 routes on cs; then match /<course>/<path>
 * Not sure yet how I should handled the generic top-level 
   'wikipedia course' that (in the old model) contained the other paths.

This http://stackoverflow.com/questions/14023864/flask-url-route-route-all-other-urls-to-some-function
suggests that there can be a "default" route after the others :

    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def index():
        return 'This is the front page'

    @app.route('/hello/')
    def hello():
        return 'This catches /hello'

    @app.route('/<path:dummy>')
        def fallback(dummy):
        return 'This one catches everything else'

flask : Catch-All URL
 http://flask.pocoo.org/snippets/57/
 ... then do my own /<course>/<path>/ match against 
 a list (or dict or whatever) of the few hundred strings ?
 See the "Algorithms using finite set of patterns" 
 in http://en.wikipedia.org/wiki/String_searching_algorithm
 And in my case, there is the further constraint that I want
 the match to be from the beginning.
 
syntax highlighting - pygments @ pygments.org

LDAP - http://www.python-ldap.org/docs.shtml


- - - -

icons

iconarchive.com

http://www.iconarchive.com/show/farm-fresh-icons-by-fatcow/user-student-icon.html
user-student-icon.png : CC Attribution license

http://www.iconarchive.com/show/oxygen-icons-by-oxygen-icons.org/Categories-applications-education-university-icon.html

iconarchive.com/show/pretty-office-10-icons-by-custom-icon-design/Professor-icon.html
license : free non-commercial ; "Custom Icon Design"
Professor Teacher-male, Teacher-female, Graduate-female, Graduate-male, Graduate-academic-cap

http://www.shutterstock.com/pic.mhtml?id=113398258
school people icons

User-icon.png - "mini icons" from "Custom Icon Design" ; free for noncommercial
http://www.iconarchive.com/show/mini-icons-by-custom-icon-design/User-icon.html
