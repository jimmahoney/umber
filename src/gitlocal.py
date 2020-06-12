"""
 gitlocal.py

 These git utilities work with a local repository.
 They can :
   * set up a git repository in a course's folder
   * add and remove files or folders from the repo
   * get the history (git log) of versions of a file
   * get the content of one previous version of a file

   >> from model import Course
   >> gittest = Course.create_course(name='GitTest', path='gittest')

"""

# This implementation is based on python subprocess.run,
# which may be problematic in a web WSGI environment.
# Check out the notes at the bottom of this file for more.

from utilities import print_debug
from shlex import quote
import subprocess
import json

def run(*commands, timeout=1.0):
    """ Run commands in a subprocess and return their output.
        >>> print(run('echo hello', 'echo goodbye'))
        hello
        goodbye
        <BLANKLINE>
    """
    # Since I'm using && between the commands,
    # each will only run if the previous ones succeed.
    try:
        argstring = ' && '.join(commands)
        print_debug(f" gitlocal run arstring='{argstring}'")
        result = subprocess.run([argstring], timeout = timeout,
                                shell = True, capture_output = True,
                                text = True, check = True)
        print_debug(f" gitlocal run result.stdout='result.stdout'")
        return result.stdout
    except Exception as e:
        print_debug(f" gitlocal run error : args={args}, error={e} ")
        # TODO : ... handle this properly in the calling routines
        return 'FAIL'

def _git_(command, course=None, page=None, user=None):
    """ Run a sequence of git command strings 
        e.g. ('git init ...', 'git add ...', 'git commit ...') """
    username = quote(user.username) if user else '__system__'
    path = quote(page.relpath) if page else ''
    repo = quote(course.abspath)
    git_command = f'git -C {repo} {command} {path}'
    git_commit = f'git -C {repo} commit -m "umber editor {username}"'
    if command == 'init':
        git_add = f'git -C {repo} add .'
        command_list = [git_command, git_add, git_commit]
    else:
        command_list = [git_command, git_commit]
    run(' && '.join(command_list))

def init_add_commit(course, user):
    """ Create a new .git repo in a course, add its files, and commit. """
    _git_('init', course=course, page=None, user=user)

def add_commit(page):
    """ Add one file or folder to the course's git repo, and commit. """
    _git_('add', course=page.course, page=page, user=page.user)

def rm_commit(page):
    """ Remove one file or folder from a course's git repo, and commit. """
    _git_('rm', course=page.course, page=page, user=page.user)

def get_history(page):
    """ Get a file's git log, returning [(revision, date, author),... ] """
    path = quote(page.relpath)
    repo = quote(page.course.abspath)
    format = """--pretty=format:'{"commit":"%H", "date":"%ad", "message": "%f"},%n'"""
    log_string = run(f'git -C {repo} log --date=iso-strict {format} {path}')
    log_raw = json.loads('[' + log_string + ']')
    # len('umber editor ')==13, so author username is message[13:]
    log = [(entry['commit'], entry['date'], entry['message'][13:])
           for entry in log_raw]
    print_debug(f' gitlocal get_log : "{log}"')
    return log
    
def get_revision(page):
    """ Return a file's content from a given revision. """
    # The revisions are given by git commit hashes,
    # and passed into this routine within the page object.
    path = quote(page.relpath)
    repo = quote(page.course.abspath)
    revision = page.revision
    content = run(f'git -C {repo} show {revision}:{path}')
    print_debug(f' gitlocal get_revision : "{content[:16]}...{content[-16:]}"')
    return content

if __name__ == '__main__':
    import doctest
    doctest.testmod()

# . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 
#
# -- Notes --
#
# The git commit message "author" field is just the process name
# of the web deamon running the umber system, which isn't useful information.
# To keep track of which user (faculty member or student typically) modified
# a given file, the git commit messages store the username.
#
# python subprocess ; see https://docs.python.org/3/library/subprocess.html
#  ... though I'm not sure how well this will work in a wsgi environment.
# I guess I'll see.
#
#  * use && to execute several commands, continuing only if preceding is OK
#      i.e. "git add . && git commit -m 'commit'"
#  *  use shlex.quote(arg) to make sure one arg is actually one arg,
#      if using shell=True ... which is what I need to use &&
#      and to do one subprocess.run() for multiple git operations
#
# I'm quoting a bunch of stuff that I probably don't need to
# ... but it shouldn't hurt and may b safer.
#
# command line git options ; see https://git-scm.com/docs/git
#   git
#      -C <path>           # as if run in this directory
#      -git-dir=<path>     # folder that has the .git data
#      <command>           # init | add | rm | log | show | ...
#      <args>
#
# git log formatting examples :
#   https://stackoverflow.com/questions/4600445/
#     git-log-output-to-xml-json-or-yaml
#   https://github.com/context-driven-testing-toolkit/git-log2json
#      git log --pretty=format:'{%n  "commit": "%H",%n
#                                    "author": "%aN <%aE>",%n
#                                    "date": "%ad",%n
#                                    "message": "%f"%n},' <path>
#
# getting a git revision of a file :
#   https://stackoverflow.com/questions/610208/
#     how-to-retrieve-a-single-file-from-a-specific-revision-in-git
#   git show <revision>:<path>
#
# ----- file and url paths for pages and courses --------------------
# (venv) mahoney@greymaple:umber$ umber_console
# == Umber console | flask shell | development ==
# Database file is /Users/mahoney/sugar/academics/umber/database/umber.db
# To see all defined names : pp(vars()) .
# Variables include (democourse, homepage, jane, app, request).
# Python 3.7.3 (v3.7.3:ef4ec6ed12, Mar 25 2019, 16:52:21) 
# [Clang 6.0 (clang-600.0.57)] on darwin
# App: umber [production]
# Instance: /Users/mahoney/sugar/academics/umber/src/instance
# >>> democourse.path
# 'demo'
# >>> democourse.abspath
# '/Users/mahoney/sugar/academics/umber/courses/demo'
# >>> homepage.path
# 'demo/home'
# >>> homepage.abspath
# '/Users/mahoney/sugar/academics/umber/courses/demo/home.md'
# >>> os_root
# '/Users/mahoney/sugar/academics/umber'
# >>> homepage.relpath
# 'home'
#
#from model import Course, Person, Page
# ... I'm having issues with circular imports (model imports gitlocal).
#     But to just use fields or methods of a passed argument
#     (e.g. course.abspath), I guess  I don't need to reference
#     the names of the objects themselves and so don't need the import.
#     Some online discussion suggest that just "import model" would work,
#     even if "from model import ..." has issues.
