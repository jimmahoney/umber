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
  by a [python markdown package](https://pypi.python.org/pypi/Markdown) :
 
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

        # Setup project's source git repo :
        $ git init ; git add * ; git commit -m "initial commit"
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

- - - 

# Thinking / TODO #

* Git within the project : 
 http://stackoverflow.com/questions/1456269/python-git-module-experiences
 Do I need to think about directory structure for git repo
 of web app source vs site course files ??

* Review SQLAlchemy & sqlite3

* Stare at wikacademia sqlite3 tables,
  and think about functions, mapping, and all that.




