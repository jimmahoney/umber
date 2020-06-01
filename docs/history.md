# umber development history #

## May 2020

 I'm thinking that one repo per course rather than one big site global
 would keep them smaller and give better performance.  Also, finding a
 way to have the site course next to rather than enclosing the other
 courses would make things simpler and keep the git repo complications
 to a minimum.

## April 2020

* github flavored markdown spec : https://github.github.com/gfm/#example-155

## Jan 2020

 Still thinking now and again about how to get the git
 stuff to work effectively. I need to think about what
 application model is needed - the one I have is too slow
 and too buggy (using dulwich.io).

 Software projects to look at :
   https://gitlab.com/gitlab-org/gitlab-foss
   https://tljh.jupyter.org/en/latest/
   https://tljh.jupyter.org/en/latest/contributing/plugins.html
   edX : https://github.com/edx/edx-platform ; big python based open source LMS

   flexible and lightweight static content management system
   for building websites out of flat files
   https://www.getlektor.com/

   GitPython
   https://gitpython.readthedocs.io/en/stable/tutorial.html#using-git-directly

   I'm remembering finding one commercial project that incorporated
   jupyter and had a course module, but can't remember what it was
   and am not finding my notes about it.

## Sep 7 2019

 on umber (production), moved database outside of cours/*
 tree so that it is *not* within the github repo ... it
 changes often and is a binary file, so I think leaving
 within github is a performance hit for git.

## Sep 5 2019

 performance of python wsgi & git stuff on cs.marlboro.college?

 stackoverflow.com/questions/30794363/
 how-to-improve-the-performance-of-apache-with-mod-wsgi

 there may be some stragegies to improve speed.
 I need to read up more on how to (a) analyze and (b) optimize it.
   - mpm_worker_module
       ... already using mpm_event ... which seems recommended
   - wsgidaemonprocess 
       ... already configured

 also look into speeding up git :
   https://www.atlassian.com/blog/git/handle-big-repositories-git
   - "shallow clone" to remove old history stuff
      ... but I don't slowdown is from too many file versions
   - remove some old binary file "cruft"
      ... maybe ?

 * or move to nginx or gnunicorn
   or "reverse proxy" from apache to one of them
   https://httpd.apache.org/docs/2.4/howto/reverse_proxy.html

 * or write git "to-do" to a file,
   and have a daemon monitor file & do it
   ... removing the (slow) "add; commit" from apache/wsgi procs
   The "get history" - which is really slow - may still need to be
   in apache, but that is used much less often.

## Sep 2 2019

 * Doing "new user" on cs.marlboro.college
   sends one of the apache2 processes to 100% cpu
   in "top" ... and it stays busy even after the
   web page reloads and it looks like it's done.
   
   Something isn't right there - I think that process is hanging,
   even though the page load completes successfully eventually
   and the database seems to up updated correctly.

   Also, "w" and "uptime" show the load shooting up to 1.0.

   Needs more investigation.

   Attempted fix: in Person.create_person, took Course.enroll_site out
   of "with db.atomic()" since there is already one of those within
   enroll_site. (Though
   http://docs.peewee-orm.com/en/3.1.0/peewee/transactions.html says
   that's OK ... at lease within one function.)  Though it does say
   "if an exception occurs in a nested block, this can lead to
   unpredictable behavior, so it is strongly recommended that you
   use atomic"

   Another possibility: picture for user janedoe ... when
   there isn't such a person, in templates/src/newuser.html.
   Just use a stock image, eh?


## Sep 1 2019

 * looking at gitlab ... it can be self-hosted and act as a web-git thingy.
 * perhaps that would help me run some git scripts from the umber side
   to do my git stuff? Hmmm.
 * maybe I just need to run some sort of async script from apache
   to invoke git ...
 * ... or maybe I need another service, i.e.
   e.g. a tornado / python thing on another port; see
   blog.dscpl.com.au/2015/08/running-async-web-applications-under.html
   ... and lots of staring at "async" and "await" in python.

## Aug 28

 more fixes
    - alphabatized list of users
    - "try" around access_rights eval()
      (crashed for non-existant file)
    - url for newuser redirect
    - b'' in ?html pygmentize (another bytes vs string python3 glitch)

## Aug 2019

 fixing various bugs
    - a bunch of related python3 string vs bytes, regex, dulwich paths
    - jpeg/png file content can't be treated as strings ...
    - os.remove does files, not folders; added shutil.rmtree

## June 2019

 working on a python3 branch
 ... though python versions & package management is (still) a royal mess.

 On my softmaple laptop, installed both python.org's 3.73 and homebrew's 3
 (which is also 3.73). Anaconda's lags behind, is still at 3.6x.
 These install to
   /Library/Frameworks/Python.framework/Versions/3.7/bin/python3
 and put a symbolic link at
   /usr/local/bin/python3

 Likewise, pip3 is the python3

 Homebrew lays out the mess :
 Python 3.x or Python 2.x

    Homebrew provides one formula for Python 3.x (python) and another
    for Python 2.7.x (python@2).  The executables are organized as
    follows so that Python 2 and Python 3 can both be installed
    without conflict:

    - python3 points to Homebrew’s Python 3.x (if installed)
    - python2 points to Homebrew’s Python 2.7.x (if installed)
    - python points to Homebrew’s Python 2.7.x (if installed)
       otherwise the macOS system Python. Check out brew info python
       if you wish to add Homebrew’s 3.x python to your PATH.
    - pip3 points to Homebrew’s Python 3.x’s pip (if installed)
    - pip and pip2 point to Homebrew’s Python 2.7.x’s pip (if installed)

 I will keep to this convention for now.

 However, it looks like virtualenv is a more powerful tool
 than the (now recommended at python.org) "python3 -m venv" virtual
 thingy ... which seems too recent for me, particularly since
 I have an existing virtualenv workflow.

  My PATH has the python.org's python3 at it's default place;
  that's the one I guess that I'll use.

  Installed virtualenv :

    $ python3 -m pip install virtualenv

  and with it created a new umber/venv :

    $ cd umber
    $ virtualenv --python=python3.7 venv
    $ . env/activate   # sets environment vars & local python path
    (venv) $ pip3 install -r env/requirements_without_versions.txt
    (venv) $ pip3 freeze > requirements.txt

  Next : try the automated src conversion using
  /Library/Frameworks/Python.framework/Versions/3.7/bin/2to3

    $ 2to3 --output-dir=src -W -n src2

  setting up & pushing a new branch with this python3 stuff.
    $ git branch python3
    $ git checkout python3
    $ git add ...
    $ git commit ...
    $ git push --set-upstream origin python3   # after some googling

## May-ish 2019

 fixed edit_grades bug

## Sep 5 2018

 fixed links for markup help on edit_work and edit_file templates.

 changed umber.css to allow inline code blocks.
 (`stuff` already turns into <code>stuff</code>;
 now that is an inline spec and not a block.)
 Also updated the markup syntax help accordingly.

  -- coming --
  run umber_cleanup from a deamon process
  when the database or files change
  to insure that the git repo in a reasonable state.
  Sending a unix signal from the apache wsgi
  but not taking up time or resources in that process.
  I'm hoping that something like this can help with the high apache
  loads  and glitches I've been seeing.

## Sep 2

 added an adminscripts.py to misc/ folder;
 can do bulk creation of users from nook html listings.
 (upload images manually with for example chrome's
  "image downloader" extension which does background images)

 While the software is feeling fairly stable, I'm seeing
 high loads on the server - often over 2.0. And it seems
 slow to do some of the editing tasks.

## July 13

 TODO: crontabl (daily?) for umber_cleanup DONE
 TODO: new_course

 TODO: review authorization stuff.

## July 12

 have debugged git dulwich stuff.
 seems to be working on development.

 ... but file delete crashed on deployed
 ... and now I see is crashing on development.
 ... several rounds of debugging & testing on deployed version

 upgraded mod_wsgi manually on csmarlboro (see ~/history.txt &
 ~/mod_wsgi) 

 All the git & related stuff seems to now be working:
 edit files, see revision, delete files, upload files.
 Checked both in folders & attachments.

 TODO: work on grades page:
   - smaller horizontally   DONE
   - editable               DONE

## July 9 2018

 Trying to move git stuff to dulwich :

  https://github.com/dulwich/dulwich
  https://www.dulwich.io/docs/

    $ cd umber
    $ . env/activate
    (venv)$ pip install dulwich
    (venv)$ cd env; pip freeze > requirements.txt

  ... all that worked on both hardmaple & cs.marlboro.college,
  so it seems to install OK.

  docs: https://www.dulwich.io/apidocs/dulwich.html

  https://stackoverflow.com/questions/6640546/programmatically-git-checkout-with-dulwich
  https://github.com/mikofski/dulwichPorcelain/blob/master/checkout.py

  dulwich.index.build_file_from_blob

  http://www.aaronheld.com/post/using-python-dulwich-to-load-any-version-of-a-file-from-a-local-git-repo
   

## July 8 2018

 TODO :
   + test upload on folder & attachments ... works in development.
   + test delete on folder & attachments ... works in development.
   
   + commit & upload dropzone changes.
   
   - test on server

     result: file upload works, but there are a bunch of wsgi errors in the log.
             deleting those files fails with an error page.
             ... which upon examination seems to be caused
                 by the failed "git commit" when the files were uploaded.

     So I think that the problems I've been seeing on the deployed server
     all have to do with the interaction of wsgi and the the way I'm
     trying to invoke git, which is failing.

  https://github.com/dulwich/dulwich ... pure-python git implementation (!)


- test larg file uploads

   learn more about https://www.docker.com/community-edition

## July 7 2018

 looking at dropzonejs.com ... which seems to be working OK.
 I'm using their default drop box with some minor changes to their css.
 The ajax handler I had before is doing OK, with a returned json response.

 dropzone does allow folders to be dropped, which as I'm handling things now
 just puts all the files within into the same folder. If multiple files
 have the same name in subfolders, the last uploaded is kept and the
 rest are overwritten.

 The configuration is set in umber.js, and the (minimal) html is in
 edit_folder.html and attachments.html. The back-end is ajax_upload
 in umber.py, called for a POST (dropzone's default) with a
 'dropzone' key set in form.args (i.e. ?dropzone=1 in url).

## May 16

 javascript (i.e. node and web) implementation of git ...
 https://github.com/isomorphic-git/isomorphic-git
 discussion : https://news.ycombinator.com/item?id=17083807 

## May 2018

 "top 17 best free jquery file upload scripts" 2018
 https://colorlib.com/wp/jquery-file-upload-scripts/

 another file upload example
 https://github.com/Bouni/HTML5-jQuery-Flask-file-upload

## Apr 2018

 crypto :

 http://latacora.singles/2018/04/03/cryptographic-right-answers.html
 https://news.ycombinator.com/item?id=16748400
 https://pypi.python.org/pypi/PyNaCl/
 https://pynacl.readthedocs.io/en/stable/

 "just use openssl"
 https://news.ycombinator.com/item?id=16746153

## Apr 5

 peewee version changes :
   http://docs.peewee-orm.com/en/latest/peewee/changes.html?highlight=rel_model
   changes in 3.0 (which Leslie is trying to use)
     BaseModel => ModelBase
     _data     => __data__
     db_table  => table_name
     rel_model => model
     db_column => column_name
     to_field  => field

## Apr 1

Fixed a bug in faculty authorization.

Pentest checklist that might be worth trying :
 jdow.io/blog/2018/03/18/web-application-penetration-testing-methodology/
 https://news.ycombinator.com/item?id=16728207
 https://www.owasp.org/index.php/OWASP_Zed_Attack_Proxy_Project

## Mar 17 2018

Added authorization checks to form handlers in umber.py.

TODO:

 * redo file uploads.

 * maybe put in a crypto "hidden" form key for 
   additional "this isn't a 3rd party submission" assurance ...
   though I'm not sure that really does much that the session doesn't already.
   
 * implement some sort of text framework with "fuzzed" illegal inputs
   and with "manually" constructed form submissions
   See for example http://flask.pocoo.org/docs/0.12/testing/

 * keep a log of form post interactions with user & ip & maybe browser fingerprint
 * put more of code in "try..." blocks & make more robust
 * move git interactions to something asynchronous

## Feb 25

Looking at form submission framework after a comment from Ben -
I've made some small changes there, but should test more carefully
that users have the right permissions to change things, without
assuming that the HTTP came from a valid page.

I also may want to limit setting folder permissions to faculty - there
probably isn't a reason to open that up to students, and there is
certainly ways that could mess things up.

## Feb 22

Weird library bug in what I was using to parse
the datetime strings, namely parsedatetime -
perhaps becuase of an issue with daylight savings, EST vs EDT or some such.
When given a string like 'March 29' it was giving
me a Febuary date ...

I've completely rewritten my Time() class,
now using the dateutil library instead and
(correctly I think) using arrow.replace(tzinfo=...)
rather than (inappropriately) using arrow.to(timezone).

## Feb 8

File upload needs to be done right - it's a core functionality,
and I'm going too many guessing games about what works or doesn't.

Maybe https://github.com/blueimp/jQuery-File-Upload ?

## Feb 2,3

 getting sys/user student to work ... I'm now setting
 registration status to 'drop' for students who were
 registered but are removed from the course. The idea
 is to leave them in as objects in the database so
 that their database work objects don't need to be
 deleted, and so that the ids are still valid.

 Also did some patching of mathjax processing in markdown2html

 jinja2 isn't handling utf8 in the way I would expect.
 My first kludgey fix was to force text to ascii with
 str(), but that fails badly when someone submits (say)
 curly quotes when editing.

 I found https://groups.google.com/forum/#!topic/pocoo-libs/6-zlF-YS8Ag
 from 2012, but jinja2 has changed since this "monkeypatch".

## Feb 1

 TODO: consider using pygit2.org for python => git ,
       since I think it doesn't need another process (command line git)
       and may be faster and more reliable.
 ... but the documentation is not clear. This talks to libgit2,
     and it's "commit" section looks complicated & confusing.

 TODO: consider alternatives to apache2 + mod_wsgi ...
       I'm not sure if that's fast enough or is causing
       some of the errors I'm seeing.

       nginx + uWSGI looks like it might be the most robust deployment.

## Jan 31

Looking at pygments source code highlights - see utilities.py.

## Jan 23

Created css file for code syntax coloring; 
see https://github.com/trentm/python-markdown2/wiki/fenced-code-blocks

  $ pygmentize -S default -f html -a .codehilite static/styles/pygment.css

and loaded that from the main template.

## Jan 21

OK, it's up and running at cs.marlboro.college.
Been doing a few bug fixes but nothing too extreme.

## Jan 17

  - spent way too much time trying to get this deployed,
    first with apache mod_wsgi, then as a gunicorn proxy.
    Both were giving "Page not found" apparently no matter what.
    Eventually managed to track down the issue with
    a gunicorn server (i.e. 127.0.0.1:4000 on my home mac,
    with the bin/umber_gunicorn script) with lots of print
    statements in it, comparing with hello_gunicorn which
    had the same configuration. before_request() was running,
    after_request() was running, but the route was not
    being found. Very weird. Apparently the issue was that
    I was using app.config_from_file() with a file that
    had a lot of stuff defined in it it in addition to
    the stuff that Flask wanted. At least one of those
    definitions, SERVER_NAME I think, conflicted with
    other config stuff (i.e. the gunicorn options).
    With that cleared up, I went back to apache mod_wsgi
    just because I have more experience with apache
    and the ssl certificates were already in place.

    The apache configs I'm using are

       # --- in /etc/apache2/envvar
       export UMBER_ROOT=/var/www/umber
       export UMBER_CONFIG=PRODUCTION
       export PYTHONPATH=$PYTHONPATH:$UMBER_ROOT/src
       # session key generated with python
       # >>> import os, binasci; binascii.hexlify(os.urandom(24))
       export UMBER_SECRET_KEY=..............

       # --- in /etc/apache2/sites-available/cs.marlboro.college.conf
       WSGIDaemonProcess umber
       WSGIScriptAlias /cours /var/www/umber/src/umber.wsgi
       <Directory /var/www/umber/src>
         WSGIProcessGroup umber
         WSGIApplicationGroup %{GLOBAL}
         Require all granted
       </Directory>

    I'm going to commit this as "wsgi deployed"
    and save a "version 0.1" branch 

## Jan 15

 ##### trying to deploy ... failed.

   - most of the time : nothing I can see in any logs "file not found"
   
   - tried moving to /var/www thinking that a global apache pref kept
     it from running elsewhre

   - tried writing to a log file for diagnostics ... nothing

   - did get a "hello world" flask app to run

   - tried installing packages in system python,
     but even minimal one gives no indication of what's wrong

   - try something else besides apache ?

   gunicorn has had some good reviews - 
   it suggests using it with nginx ... though it looks like apache also works.

   https://djangodeployment.com/2016/11/30/how-to-setup-apache-with-gunicorn/

   gunicorn installs with pip , is a stand-alone, serving up pages on
   say 127.0.0.1:4000 , which nginx or apache then proxies.

  

------------------

 I'll be using Apache, WSGI, and virtualenv.
 The relevant recipes are
   http://modwsgi.readthedocs.io/en/develop/user-guides/virtual-environments.html
   http://flask.pocoo.org/docs/0.12/deploying/mod_wsgi/#installing-mod-wsgi

 On the linode deploy server (umber.cc ; cs.marlboro.edu):
 
   $ cd /opt/umber
   # this sets some environment variables and then does virtualenv's 
   # "source venv/bin/activate"
   $ ./env/activate
   (venv)$ python -c 'import sys; print(sys.prefix)'  # location of virtual env
   /opt/umber/venv

 No app.run() : check.

 Same python for mod_wsgi install & virtualenv (2.7.12) : check.
   $ python --version
   Python 2.7.12
   $ sudo apt-get install libapache2-mod-wsgi
   $ cd /opt/umber
   $ virtualenv env
   $ source venv/bin/activate
   (venv)$ pip install env/requirements.txt
   (venv)$ python --version
   Python 2.7.12

 Seems to be various schemes for defining the environment variables
 that the app will need. I notice that one option is to head for
 /etc/apache2/envvars which give the defaults for apache2 :
 I'd think that editing that - or loading another file from it - would work.

 ----------

 Time to try to deploy this.
 commit 06dad3177f6e5266cebc4444546e6a70d32b6bbb

 TODO

  - admin user=? if not found ... check   CHECK
  - enroll users :                        CHECK

  ------- postponed
  - all courses : edit & copy
  - edit a single course
  - add a new course  *   &  default course skeleton
  - script to add users from csv file
  - script do add courses from csv file (?)

### access rights

 I decided that the mechanism for assigning which pages
 could be read/write by whom was too awkward for sys/*
 pages - the code was spreading itself here and there.
 
 I will now require that all sys files (except navigation)
 have a first line that can serve as the .access.yaml like this :

   {# {'write':..., 'read':...} #}

 where the {# #} is the jinja2 template comment.
 Part of the issue was that I want the access rights
 before the action.html piece runs which draws
 the edit|history tabs, but the sys/ content pieces
 don't run until later. The current approach looks
 at the first line early in Page.get_from_path(...)
 and sets up accessdict from either the .access.yaml
 (for regular files and folders) or from the first
 accessyaml comment (for sys/* special pages).

## Jan 14

### environment

All of the examples online I see of flask deployments,
including googling "best practice", all use virtualenv
rather than the anaconda virtual python that I have been using.

And on a production system, anaconda's model of putting everything
in a user's folder rather than the project seems less than ideal.

I also think from reading that virtualenv has improved since
I stopped using it some time ago.

So I have just added in env/ some instructions and files
for virtualenv, which I was able to setup without much
trouble (at least, after finding "conda install virtualenv",
ironically enough - my existing virtualenv was broken or
at least incomapatible with the anaconda python I've been using.)

I've saved a commit 573cc76404dfe5f11ed318ade6379fc1311ba52c
which has both anaconda and virtualenv stuff ... but am going
to now get rid of the anaconda environment rather than
try to keep two virtual environments up to date.

### settings

I've also revamped the src/settings.py file to allow for
a cleaner DEVELOPMENT vs PRODUCTION mode of working.

The production setup I am envisioning on cs.marlboro.edu is

 /opt/umber                      umber software repo

 /var/www/cs/                    apache root for static pages including
 /var/www/cs/courses/fall2017    older courses (url cs.marlboro.edu/courses/ )

 /var/www/cours                  umber repo (url cs.marlboro.edu/cours/
 /var/www/cours/spring2018       this semester's courses       
 /var/www/cours/_umber_.db       sqlite3 database (within git repo)

## Jan 13

 I've been working on this locally but now have uploaded the project to github :

 * created an empty "umber" project on github
 * followed their recipe for adding this stuff to that :
   $ git remote add origin https://github.com/jimmahoney/umber.git
   $ git push -u origin master

 Now the workflow after making changes is
   $ git add .                  # what goes into this set of changes
   $ git commit -m "message"    # notation about this set of changes
   $ git push                   # upload to github

## Jan 10

 markdown2 apparently has a bug in how it handles query strings in links :

 markdown2html('[foo](bar?a=b&c=d)')
 u'<p><a href="bar?a=b&amp;c=d">foo</a></p>\n'

 The issue is the conversion of & to "&amp;" in the query string ... oops.
 Workaround regex fix I have is an ugly regex loop ...

 ----------

 After a bit of futzing around, here's the API for user & course stuff.

 I've decided to put all registered users in the site/ course.
 And I'm using the "member" to mean a registered person who can log in
 i.e. admin + faculty + students + guests.

   -- members --
   
   course/sys/user                              see own data
   course/sys/user?username=janedoe             see user in same course
   course/sys/user?action=edit                  edit password
   course/sys/roster                            picture book

   -- faculty --

   course/sys/users                             edit who is in course

   -- admin --
   
   site/sys/user?username=janedoe&action=edit   edit all fields except username
   site/sys/user?newuser                        create new user

   site/sys/users                               see all users & courses they're in

   --- tentative
   site/sys/courses                             see all courses
   site/sys/course?id=xx                        see one course
   site/sys/course?id=xx&action=edit            edit one course
   site/sys/newcourse                           create a course

 Without an ldap thingy, 
 I will need some way to batch input the users.
 It will probably be easier to write some sort of
 script for that that works on some sort of csv file,
 without putting that functionality directly into a web page.

## Jan 7

 Having trouble with urls which aren't in the demo course.
 Am implementing a quick fix :
   * Even though I am leaving the "Umber" course
     for the folder which holds the other courses,
     trying to display any page within in gives a 404 "not found" error.
   * update: I now have an "error" course which signals the 404
     for this case. Trying to have page.course=None was not
     playing nicely with the peewee ORM.

 Am creating a new "site" course which will hold site-wide resources
 and handle access to them, including help files and user photos.
   site/help/.access.yaml    read: all
       /photos/              read: guests
 (where guest is someone who is logged in i.e. not visitor or anonymous)

## Jan 5

 Finished a first pass on the grades page.

## Jan 2 2018

 Notes about related stuff :

 - I have a 0th attempt from Oct to mirror the cs.marlboro.edu web pages;
   see /var/www/umber on csmarlboro.org and ~/cs_marlboro_edu_static .

 - The html generating part of wikiacademia is in
   /Users/mahoney/sugar/academics/wikiacademia/v0.1alpha/htdocs/courses/source/ .

 Future features to consider :

 - github or generic git integration for student work folders ... some sort of git subfolder.

## Dec 28 2017

At this point:

* showing & editing attachments seems to be OK.
* work pages with grades and editing them is OK.
* editing navigation works, including history and a default example

What's left is the admin stuff :

* sys grades page  (with colors for what changes to pay attention to)
* sys roster page  (with photos)
* edit roster      (update some static database of people from ldap dump maybe?)
* all courses
* all users
* create course

And of course deploying it and testing it.

## Nov 28

 Displaying and editing assignments works.

## Oct 27

 first pass on file upload via drag'n'drop is done - needs more tests.

 ---

 drag'n'drop for folders doesn't seem to have robust support
 so I guess I'll just skip it - too bad.
 Folder upload does lead to recursive folder-within-folder
 complications which I guess for now it's just better to skip.

 https://stackoverflow.com/questions/3590058/does-html5-allow-drag-drop-upload-of-folders-or-a-folder-tree
 https://developer.mozilla.org/en-US/docs/Web/API/DataTransferItem/webkitGetAsEntry#Browser_compatibility
 DataTransferItem.webkitGetAsEntry()

## Oct 19

 folder edit :
   - delete works , including git commit
   - new folder works , including git commit

 next: privileges

 then: file upload

 aside:
  https://bitbucket.org/cse-assemblyline/assemblyline
  a canadian made security tool for scanning files
  for malicious content ... could perhaps be part
  of the upload workflow to check for bad things ...
  though for my situation it is almost certainly overkill.

## Sep 25

 starting to look at file upload.
 Check out :
  https://github.com/kirsle/flask-multi-upload
  https://plainjs.com/javascript/ajax/

 https://www.w3.org/wiki/JavaScript_best_practices#Avoid_globals

## Aug 7

history for .md files works.

folder view works

Set up a development environment on the laptop ...
still not very painless; see the notes in the env/ folder.

TODO:
 - folder edit
 - assignments
 - mirror of existing site
 - deployment strategy
 - authorization mechanism
 - special pages

## July 6

Decided to give up on wiki support for now -
too much bother. Maybe later.

And decided to stick with .md rather than .markdown etc,
for simplicity.

to consider :
 an in-browser quasi wysiwyg markdown editor : 
  https://github.com/sparksuite/simplemde-markdown-editor
 uses https://github.com/chjj/marked , a github flavored markdown
 but ... I guess would still need to add a course/machine link syntax

## June 30 ##

Setting up the git repo for the course pages
will need to done elsewhere. And if I want the
source tree to be separate from the courses pages,
I need to worry about what that git repo structure
looks like later. I think that the right thing here
will be the git submodules thingy, but I haven't
looked into that yet. Or maybe I just put 
the installed courses folder somewhere that isn't
under the source code for the umber project -
that would be simpler.

Edited files are now added and committed to the git repo,
along with a message 'user:username' that I can use
for the web history page.

basic editing of files works.

Starting to think about git.

  == some git command examples ==

  $ git log courses/demo/home.md
  454b6283179be56d4dfe2143163cbf9c93985142 basic editing of files works
  0caeb3005836936d3805484bb72f690d452a6475 minor
  8232a255620ff7d5b6c6aab1354e0c367b3b0da1 markdown works

  $ git show 0caeb3005836936d3805484bb72f690d452a6475:courses/demo/home.md
  home
  ====
  etc

installed python module 'sh' ; updated env/environment.yml
 $ conda install sh
 $ conda env export

The only downside of using git through sh is that I will
likely have to parse some of the output myself ... though
their built in formatting should make that simple :
  $ git log --format="(%H,%cn,%cd,%s)" --date=iso courses/demo/home.md 

Got a conda warning about changing of env format changes -
I will worry about that another time.

## June 27 2017 ##

Still continuing to make slow progress.

The navigation page seems to working including hiding student &
faculty parts from those not authorized.

Login works and assigns roles correctly.

(Though there is no ssl as of yet - I'm now thinking that this time
all of it will be ssl through some other part of the deployment
process.)

Folder listings are also now working.

The navigation page also now has the current page with an anchor link,
as it should. (I've changed it's color to a greyish to distinguish
better from the blue links.)

However, note that the markdown urls must match the canonical form of
those urls if the pattern matching is to do the right thing.

For example links to the file demo/home.md and folder demo/notes
should be in the nav file as

 * [home](~/home)                 RIGHT
 * [notes](~/notes/)

since the cononical form of home.md is home (without the .markdown)
and for a directory is notes/ (with the trailing slash). If
instead the nav file is

 * [home](~/home.md)              WRONG
 * [notes](~/notes)

then the links will work but redirect to "home" and "notes/"

TODO : recognize these other forms.

## May 26 ##

First pass on navigation page done.

TODO:

 - translate course links i.e. ~/home  - done.

 - look at uploads
     http://pythonhosted.org/Flask-Uploads/
     https://github.com/kirsle/flask-multi-upload

## May 24 ##

 adapted wiki2html from wikiacademia

## May 23

 I think that when hosted I will have everything be ssl.
 So the "login" doesn't need to point at secure_url :
 everything will be secure.

 ... and login works! 

## May 19

 ssl : typically in hosting setup;
       see for example https://jslvtr.com/using-https-with-your-flask-app/

 "flash" is the flask message passing system;

## May 15 2017

 Back to a working state , at least on hardmaple :

   $ cd /Users/mahoney/sugar/academics/umber
   $ source env/activate 
   (umber)$ umber_init_db
   (umber)$ umber_test
   (umber)$ umber_console
   (umber)$ umber_server
       http://127.0.0.1:5000/test
       http://127.0.0.1:5000/umber/demo/home

   $ git commit -m "back in a working state"

 Now running with flask 0.12.1 & python 2.7.13 ;
 see env/environment for all the specifics.

 I am not sure that bin/umber_console and bin/umber_server
 are following the flask typical recommendations - I'm setting
 several environment variables and testing for them - but
 at least it seems to work. In particular, the console and
 server have different database connection schemes, and
 my default approach was throwing errors until I explicitly
 tested for the console.

## April 2017

 flask-peewee deprecated ?

 Hmmm.

 I have in model.py :

 from peewee import SqliteDatabase, Model, BaseModel, \
 TextField, IntegerField, PrimaryKeyField, ForeignKeyField

 ... and peewee itself seems healthy :
 http://docs.peewee-orm.com/en/latest/

 added peewee dependency to env/environment.yml ;
 see if anything other glue is needed.

## Feb 2017

Maybe I should look at

 fossil-scm.org
 https://news.ycombinator.com/item?id=13668952 - discussion

which describes itself as a
 "simple, high-reliability, distributed software configuration
  management system with these advanced features ...
  wiki, technotes, web interface, self contained, https/ssh,
  version control with git, free and open source"

Perhaps rather than write umber from scratch I should leverage
this and use its git/wiki/webserver instead?

But: all in a sqlite database, not a file system. Hmmm.
And it's written in C ...

So I guess not.

I supposed it could be a useful API for git version control of the files.
Hmmm. Needs more thinking.

gitlab would be another way to do a similar thing.  Besides hosting
repositories, there's a downloadable you-host-it open source code
base. (Logan is doing this, I think.) Looks like its source code is
in ruby, and that it too keeps everything in a database.

## Dec 2016

Got this working again on my laptop ... but took some doing. (Still sigh.)
The flask commands "python -m flask shell" and "-m flask run" 
don't seem to find umber.py unless it's in the roote directory,
in spite of several attempts to set up environment variables
to do the right thing.

## April 2016

Been away from this for a long time - trying to get things working again.

virtualenv isn't working painlessly. Neither is sqlalchemy. (Sigh.)
 
I'm moving to anaconda and their "conda" environment & package management
system, and moving around some scripts and startup stuff as part of that.

## Sep 2014

  * https://news.ycombinator.com/item?id=8264733
  * http://standardmarkdown.com/

## July 22 2014

I think the postgres stuff is a distraction for now - on to markdown.

## July 3

 Looking at 
  http://www.fullstackpython.com/databases.html
 while gearing up for web programming class.

 Claim is that SQLite is too wimpy for production web servers :
 https://docs.djangoproject.com/en/dev/ref/databases/#database-is-locked-errors

 Postges?
 http://killtheyak.com/use-postgresql-with-django-flask/
 -- installing it --
   http://www.postgresql.org/download/macosx/ :
   "the standard mac OS includes only the postges commandline client ..."

   $ port installed | grep postgres
   postgresql91
   postgresql91-server
   commandline :
      createdb

   $ which psql
   /usr/bin/psql        # perhaps the above default Mac OS client?
                        # ... but createdb (one of its tools) is also in /usr/bin
                        # ... and its version 9.1.9
      
   I see that /opt/local/bin/psql91 -> /opt/local/lib/postgresql91/bin/psql
   $ ls /opt/local/lib/postgresql91/bin
   clusterdb		ecpg			pg_ctl			postgres
   createdb		initdb			pg_dump			postmaster
   createlang		oid2name		pg_dumpall		psql
   createuser		pg_archivecleanup	pg_resetxlog		reindexdb
   dropdb		pg_basebackup		pg_restore		vacuumdb
   droplang		pg_config		pg_standby		vacuumlo
   dropuser		pg_controldata		pg_upgrade

   Hmmm. The "postgres" one is presumbably the server. It isn't on my path.
   Maybe I'll just try resintalling to make sure I have the pieces

   $ sudo port install postgresql91-server
   ... slow : readline, openssl, gettext, python (?) ...

   docs :
   http://www.postgresql.org/docs/9.1/interactive/creating-cluster.html

   $ edited ~/.profile to put /opt/local/bin/psql91 on my PATH
   Looks like it needs to be *before* the postgres stuff in /usr/bin,
   they don't seem to be compatible.

 some commands to get postgresql running in a development mode, 
 without trying to implement any security, using the default localhost 
 trusted stuff and user "mahoney" look like this:
 $ initdb -D <db_directory>                       # create folder db data
 $ postgres -D <db_directory > <logfile> 2>&1 &   # run server in background
 $ createdb <dbname>                              # or "CREATE DATABASE name;"
 $ psql <dbname>                                  # command line SQL client
 # TYPE SQL;

 Googling on "sqlite3 postgresql syntax differences found 
 many examples, including 
   http://blog.flatironschool.com/post/68064669290/
   porting-sqlite3-data-to-postgresql-database-in-rails-4
 which says
   sqlite3                               postgresql
   -----------                           ---------------
   INTEGER PRIMARY KEY AUTOINCREMENT     SERIAL PRIMARY KEY
   datetime                              timestamp
   varchar(255)                          text

## June 19

some perhaps related resources :

 https://news.ycombinator.com/item?id=7913176 discussion of mdwiki
 http://dynalon.github.io/mdwiki/#!index.md   markdown conversion in js
 http://pythonhosted.org/MarkWiki/            python markdown engine

 https://github.com/markdown-it/markdown-it   js (node) markdown engine

## June 11

The jinja2 template debugging is worth keeping
in spite of its non-python limitations. I'm abandoning
the mako templates, and have marked a last_with_mako_templates
branch which had support (and some tests and examples)
for both sorts of templates.

I've enabled https/ssl access so that I don't have 
to finesse that in the code with "allow-login-without-https" stuff.
However, that means I will have to have two sessions running :
    $ python umber.py              # http  8080
    $ SSL=true python umber.py     # https 8443
which is wrapped into just
    $ ./server
with a bash script that invokes both the background
after killing any previously running umber.py processes.

This url is doing fine as a test 
    /test
And the next thing to do is to get
    /demo/home
into better shape.

## June 10

I think I should not try to finesse https for testing,
but instead set up my laptop to allow it. Google 
"https localhost mac" for recipes, including 
http://webdevstudios.com/2013/05/24/
how-to-set-up-ssl-with-osx-mountain-lions-built-in-apache/

I have marked a "minimal_directory_and_permissions" branch
at git commit fe20a41aa6aed29d70680e6f7bd7af036d8382fd
which is the last with Directory and Permission sqlite
objects, sqlalchemy classes, and support. It felt like
all that was getting too messy. After getting the 
old .access.yaml working, I'll do some performance
tests and worry then about caching, either putting
course names into the .access.yaml files and creating
them in subfolders as needed, or putting some sort
of cached thing into the sqlite database, perhaps
with (path,user,course,permissions).

## June 6

Been mucking about with Directory and Permission objects.
I'm not happy with them - they feel complicated and fragile.
The disk folders and database Directory objects will get
out of sync, and so code to create Directory objects
on the fly will be needed. Since Permission(s) are set
in the database, there isn't a clean way to specifiy 
them in the file system alone, without giving default
values here in the code. Blech.

I'm almost tempted to go back to the .access.yaml files
that I had before. Maybe the Directory and Permission 
objects should be act as caches, with the real information
being set (and saved) in the disk files.

I think I need to just leave this alone for now,
and see how they will be used once some of
the other pieces are in place.

## May 16 2014

Second take - summer of 2014. Started looking at this 
again after a 9 month break.

The ./env/ virtualenv cache wasn't working; looks like
there were some absolute paths from back when I had
two hard disks and some of the mount points & folders
where symlinks. I reinstalled all the depenedencies.
First I updated the min versions (after looking online
for what seemed current) in requirements.txt, and 
then followed the recipe there, e.g.

### Reinstalling dependencies 

 $ pwd
 /Users/mahoney/academics/umber
 $ mv env old_env               # set aside old devel environment
 $ virtualenv env -p python2.7  # create ./env (new devel environment)
 $ . env/bin/activate           # local python, pip, ... (alias 'activate')
 (env)$ pip install -r requirements.txt

### Testing

 $ ./reset_db
 $ python src/model.py   # run its tests - passed but for new paths
 $ ./console

### Cleaning up and committing

 $ rm -rf env_old/
 $ git add *
 $ git commit -m "starting work again, summer 2014"

I think that I should look at the question of mako vs jinja2
for the templating engine - I'm not happy with the "debugging sucks"
place I ended up last summer. Maybe mako is now better integrated
with flask ... or maybe I just shouldn't bother with it.

Looking into generating an ERD (entity relationship diagram)
from the sqlite3 database - I'm finding this one (which I've used before)
 http://search.cpan.org/dist/SQL-Translator/lib/SQL/Translator/Manual.pod
 http://mancoosi.org/~abate/tags/sqlfairy
and a bunch of commercial tools.

This worked :
 * already had graphviz (i.e. "dot" etc)
 * from perl's cpan, installed SQL::Translator & GraphViz modules
 * downloaded cpan's SQL-Translator***.tar.gz to get scripts/ 
   including sqlt-graph, which I copied to ./src/sqlt-graph

The scripts and generated diagram are now in database/erd/

## Aug 20 2013

Working on getting main.html functional after all the recent changes.
Debugging the mako templates *really* sucks.

## July 30 ##

Have page with os_path, can_read, can_write working in model.py tests.
Doubt I'll have something working well enough by the start of the term, though.

## July 24 ##

Added unique coursepath to Directory, allowing a fallback Umber
course, as I did with Wikiacademia. (I thought about other 
mechanisms that would avoid embedding a typical course within
another "course", but decided that I still like this model.)

I tried to get the permissions to cascade delete from within sqlite3,
but that didn't seem to work as I expected ... so I'm just doing
that explicitly with Directory.delete() before creating new Directory
objects. This whole permission/directory thing is likely going to 
be slow, but since it doesn't happen often I don't think that
will matter much.

Next: 
 * setting up a Page object for a given request
 * 'generic' file view (with correct permission handling)
 * .md markdown view
 * .wiki mediawiki view (?)
 * directory view
 * error pages & code for (missing page, missing directory, missing course)

## July 22 ##

Permisions and directories mostly working,
and can setup themselves to defaults for folders in Demo Course.

## July 20 ##

Work continued this week (sporadically) on folders and permissions
in the database - taking too long.

## July 12 ##

Continuing to work on folders and permissions.

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

## July 3 ##

Generated a new random background image, pale tan (i.e. umber) color;
see images/random_umber.* . (Actually run at cs.marlboro.edu/images/* 
in old wikiacademia environment.)


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

## June 28 & 29 ##

* Have basic database working, including Demo Course 
  and tests in model.py 

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

## June 26 2013 ##

Started umber project, summer 2013

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

-------------------------------------

# Thinking / TODO #git

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

-------------------------------------------

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

----------------------------------------
markdown 
 
 markdown *does* allow raw HTML by default.
 Thus one way to put in extensions is to make new html-ish tags, eh?

 https://pypi.python.org/pypi/Markdown
 includes support for user defined extensions,
 as well as some of its own extensions 
 (hilited codeblocks with ~~~~ , footnotes)

 another extension module, trac-like (?) syntax
 which I think is double brackets, [[special stuff]]
 https://pypi.python.org/pypi/markdown-macros via codehilite & pygments

 github extensions :
 https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet
 * they treat newlines as real line breaks (ugh ... though they claim evidence)
 * ignore interior underscore (yes)
 * autolink URLs
 * fenced code blocks with 
   ```optional_language
   code
   ```
   in additional to traditional 4-space indent
   (tab or 4 spaces required)
   preceding black line required before all code blocks
 * task lists (eh)
 * @person notification
 * :emoji
 * #issue
 * a bunch of project/user/hashtag auto-links
 * DOES allow inline HTML

 see http://en.wikipedia.org/wiki/Markdown_extensions

pandoc is a full feature document conversion library in Haskell.
includes markdown, pdf, html, etc
extensions :
 * backslash newline is a hard line break
 * requires blank line before header
 * header attributes      # header {attribute}
 * email-like > leading for block quotes
 * fenced code blocks with ~~~ or backticks ``` , optional language
 * three or more * or - or _ (optionally with spaces) gives <HR>
 * LaTeX-ish title/author blocks at start of files; leading %
 * backslash escapes
 * strikeout ~~this~~
 * subscript H~2~O and supersciprt 2^10^ (odd but consistent)
 * math in $text stuff$ blocks ($x....x$ where x is a non-space character)

Several of these are aimed at 
some consitency with PHP Markdown Extras :
http://michelf.ca/projects/php-markdown/extra/

 * footnotes in addition to reference style links, with [^1]
 * abbreviation definition lists

call for standardization :
 http://www.codinghorror.com/blog/2012/10/the-future-of-markdown.html
negative response :
 http://www.rumproarious.com/2012/10/29/markdown-the-spec/

codemirror.net is a javascript library for in browser code editing.
Includes emacs compatability. Used many places - very cool.

ipython connectivity might also be something to consider.

---------
2016 markdown converters :

 I'm trying this one :

 https://github.com/trentm/python-markdown2/wiki/Extras
 extras that look good :
   code-friendly, fenced-code-blocks, footnotes, metadata, pyshell, tables, cuddled-lists

 For syntax highlighting,
 stackoverflow.com/questions/25828453/markdown2-how-to-get-extras-working :
 (a) language hint after ``` 
 (b) pygments installed
 (c) a CSS style : https://github.com/richleland/pygments-css

---------------
2017 invoking git from python thinking :

 gitpython :
   https://gitpython.readthedocs.io/en/stable/intro.html
   "GitPython is not suited for long-running processes (like daemons)
    as it tends to leak system resources."
   Hmmm.

 pygit2 :
   https:www.pygit2.org
   http://www.pygit2.org/recipes.html
   requires compatible versions of libgit2 and pygit2
     ... there are instructions for a virtualenv install,
     but the custom aspects of this make me worry about maintability
     and compatability with the conda requirements stuff i've been doing
   google "conda pygit2" brings me to
     https://anaconda.org/m-labs/pygit2 which says
     $ conda install -c m-labs pygit2=0.24.0 ... which failed.

 sh
   https://stackoverflow.com/questions/1456269/python-git-module-experiences :
   "I've switched to using the sh module for not just git but most
    commandline utilities I need in python. To replicate the above I
    would do this instead:"
    >>> import sh
    >>> git = sh.git.bake(_cwd='/home/me/repodir')
    >>> print git.status()
    # checkout and track a remote branch
    >>> print git.checkout('-b', 'somebranch')
    >>> # add a file
    >>> print git.add('somefile')
    >>> # commit
    >>> print git.commit(m='my commit message')
    # now we are one commit ahead
    >>> print git.status()

   Hmmm. That looks pretty straightforward ... and sh is in conda.
   And they have a "from sh import git" already.

------------
 deploying it

 Apache & mod_wsgi looks like a real option:
   - I already have experience with apache
   - should be able to have part of website static,
     part umber as I do now on cs.

 But also see 
    https://www.fullstackpython.com/docker.html

-------------
 testing

 check out https://realpython.com/blog/python/the-minimum-viable-test-suite/
 which discusses Flask-Testing 

-----------------

 I can clone this repo if I can ssh into a server where it's store.
 For my desktop (hardmaple) and with my ssh keys installed to
 automate login :

   $ cd Desktop    # clone will be put here
   $ git clone harmaple:sugar/academics/umber
   Cloning into 'umber'...
   etc

-------------------
 git does have a version of repositories within repositories -
 it's called "submodules".

-------------------

 LaTeX 
 https://www.mathjax.org/#gettingstarted
 They say to use 
<script src='https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.2/MathJax.js?config=TeX-MML-AM_CHTML'></script>

 4.7G  home
 51M   var/www
 13M   etc
 45M   root

# ls -ld /media/sda/sbin/init
ls: cannot access /media/sda/sbin/init: No such file or directory
# file $(readlink -f /media/sda/sbin/init)
/media/sda/sbin/init: cannot open `/media/sda/sbin/init' (No such file or directory)
# ls -ld /media/sda/bin /media/sda/sbin /media/sda/lib /media/sda/usr /media/sda/etc
sda/usr /media/sda/etc -ld /media/sda/bin /media/sda/sbin /media/sda/lib /media/ 
drwxr-xr-x   2 root root  4096 Jan 12 00:43 /media/sda/bin
drwxr-xr-x 142 root root 12288 Jan 12 05:46 /media/sda/etc
drwxr-xr-x  19 root root  4096 Jan 12 00:44 /media/sda/lib
drwxr-xr-x   2 root root 12288 Jan 12 00:44 /media/sda/sbin
drwxr-xr-x  12 root root  4096 Feb 11  2016 /media/sda/usr

root@ttyS0:~# mkdir /media/sda
root@ttyS0:~# mount /dev/sda /media/sda
root@ttyS0:~# ls -ld /media/sda/sbin/init
ls: cannot access /media/sda/sbin/init: No such file or directory
root@ttyS0:~# file $(readlink -f /media/sda/sbin/init)
/media/sda/sbin/init: cannot open `/media/sda/sbin/init' (No such file or directory)
root@ttyS0:~# ls -ld /media/sda/bin /media/sda/sbin /media/sda/lib /media/sda/usr /media/sda/etc
drwxr-xr-x   2 root root  4096 Jan 12 00:43 /media/sda/bin
drwxr-xr-x 142 root root 12288 Jan 12 05:46 /media/sda/etc
drwxr-xr-x  19 root root  4096 Jan 12 00:44 /media/sda/lib
drwxr-xr-x   2 root root 12288 Jan 12 00:44 /media/sda/sbin
drwxr-xr-x  12 root root  4096 Feb 11  2016 /media/sda/usr

===============
deploy :


      software/
      cours/
      datat/
my choices

     umber.cc
     csmarlboro.cc
     csmarlboro.org


     courses
     cursai | cúrsaí       irish          
     cours                 french         <===
     cursussen             dutch
     cursos                catalan
     kursoj                esperanto
     kurssit               finnish
     kursy                 polish
     kurs                  norwegian  

   -------

     umber.cc/                               the software ?
     
     cs.marlboro.edu/courses/fall2010        ... what it was
     
     umber.cc/marlboro/courses/fall2016      old stuff
     umber.cc/marlboro/kurs/spring2018       new stuff ?
     umber.cc/cs.marlboro                    cs homepage ?

     marlboro.college/umber/fall2016

     cs.marlboro.college/courses/fall2016
     cs.marlboro.college/kurs/spring2018/
                         cours
  or

     csmarlboro.cc/courses/fall2018
     csmarlboro.cc/kurs/2017
     csmarlboro.cc/umber

  --- recursively change text ---
  find ./ -type f -readable -writable -exec sed -i "s/cybernetnews/cybernet/g" {} \;
  --- then --------------
    /courses/       => new folder
    cs.marlboro.edu => new host

