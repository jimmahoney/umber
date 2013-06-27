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

* Updating the basic tools: python (2.7.5), pip (1.31), virtualenv (1.9.1),
  and git (to 1.8.3.1, manually from git-scm.com, including running 
  a script to make its environment available to non-terminal applications.)

        $ sudo port upgrade python27
        $ sudo pip install --upgrade pip
        $ sudo pip install --upgrade virtualenv

* Using markdown for docs, with html conversion (when needed)
  by a [python markdown package](https://pypi.python.org/pypi/Markdown) :
 
        $ sudo pip install markdown
        # e.g. "markdown_py file.md > file.html"

* Setting up directories, environment, git repo.
  (Most of this is very similar to what I did last year in 
  ~/academics/web_development/flask/planet_express )

        $ cd /Users/mahoney/academics/
        $ mkdir umber; cd umber ; mkdir docs
        # Create README.md, docs/history.md (this file)

