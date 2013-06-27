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

Working on my MacPro, OS X 10.8.4 .

* Update the basic tools: python (2.7.5), pip (1.31), virtualenv (1.9.1),
  and git (to 1.8.3.1, manually from git-scm.com, including running 
  a script to make its environment available to non-terminal applications.)

        $ sudo port upgrade python27
        $ sudo pip install --upgrade pip
        $ sudo pip install --upgrade virtualenv

* Use markdown for docs, with html conversion (when needed)
  by a [python markdown package](https://pypi.python.org/pypi/Markdown) :
 
        $ sudo pip install markdown
        # e.g. "markdown_py file.md > file.html"

* Set up initial directories, environment, git repo.
  (Just like last year's ~/academics/web_development/flask/planet_express )

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

* 

- - - 



## TODO #3

* requirements.txt, __init__.py , rest of planet_express-like stuff.

 Git within the project : 
 http://stackoverflow.com/questions/1456269/python-git-module-experiences

 Stare at sqlite3 tables ; think about mapping to SQLAlchemy stuff.


