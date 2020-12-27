"""
 gitlocal.py

 These git utilities work with a local repository,
 which provides a revision history for each file.

 They can :
   * set up a git repository in a course's folder
   * add and remove files or folders from the repo
   * get the history (git log) of versions of a file
   * get the content of one previous version of a file

 This implementation is designed for one repo per course.  (I used to have one
 repo per site, which eventually got too big and too slow.)

 Concurrency is an issue here.  For drag'n'drop file uploads, with multiple
 file uploads, each one fires off an ajax request and each save file invokes
 "git add ...; git commit ...". Git uses a lock file to avoid conflicts, so
 these will fail if another concurrent web server process is already running.
 My current approach is to simply wait a bit (with some randomness to try to
 avoid spread things out) and try again, hopefully giving enough time for the
 conflict to resolve. A better approach might be to set up a dedicated single
 git server to catch these and process them one at a time, perhaps just using
 python's socket server.

"""

from utilities import print_debug
from os import getpid
from time import sleep
from shlex import quote
from random import random
import subprocess
import json

def run(*commands, timeout=1.0, verbose=True, attempt=0):
    """ Run commands in a subprocess and return their output.
        >>> print(run('echo hello', 'echo goodbye', verbose=False))
        hello
        goodbye
        <BLANKLINE>
    """
    # Since I'm using && between the commands,
    # the commands in the sequence will only run
    # if the previous ones succeed.
    error_signature = 'fatal'  # start of result.stderr for retry
    retry_delay = 0.5          # seconds
    max_attempts = 10          # perhaps up to drag'n'drop file upload count?
    argstring = ' && '.join(commands)
    success = True
    pid = getpid() # process id
    try:
        # An attempt at preemptive git lock collision avoidance :
        # wait a random amount of time from 0 to 0.01 sec,
        # so that concurrent file uploads start at slightly different times.
        sleep(0.01 * random())
        result = subprocess.run([argstring], timeout = timeout,
                                shell = True, capture_output = True,
                                text = True, check = False)
        if verbose:
            print_debug(f" gitlocal {pid} attempt={attempt}")
            print_debug(f" gitlocal {pid} run result.stdout='{result.stdout}'")
            print_debug(f" gitlocal {pid} run result.stderr='{result.stderr}'")
    except Exception as e:
        success = False
    if result.stderr.startswith(error_signature):
        success = False
    if success:
        return result.stdout
    if attempt > max_attempts:
        return ' gitlocal {pid} fatal error: run() failed after too many attempts'
    # -- try again --
    delay = random()*retry_delay
    if verbose:
        print_debug(" gitlocal {pid} : failed; wait {delay} sec & try again")
    sleep(delay)
    retry = run(*commands, attempt=attempt+1)
    return retry

system_username = '__system__'
    
def _git_(command, course=None, page=None, user=None, abspath=None):
    """ Run a sequence of git command strings 
        e.g. ('git init ...', 'git add ...', 'git commit ...') """
    username = quote(user.username) if user else system_username
    repo = quote(course.abspath)
    if command == 'rm -r':
        # abspath is a list of absolute paths
        git_command = []
        for _abspath in abspath:
            path = quote(page.get_gitpath(_abspath)) if page else ''
            git_command.append(f'git -C {repo} {command} {path}')
    else:
        path = quote(page.get_gitpath(abspath)) if page else ''
        git_command = f'git -C {repo} {command} {path}'
    git_commit = f'git -C {repo} commit -m "umber_editor {username}"'
    print_debug(f" _git_ : git_command='{git_command}' git_commit='{git_commit}'")
    if command == 'init':
        run(git_command, f'/bin/git -C {repo} add .', git_commit)
    elif command == 'rm -r':
        git_command.append(git_commit)
        run(*git_command)
    else:
        run(git_command, git_commit)

def init_add_commit(course, user):
    """ Create a new .git repo in a course, add its files, and commit. """
    _git_('init', course=course, page=None, user=user, abspath=None)

def add_commit(page, abspath=None):
    """ Add one file or folder to the course's git repo, and commit. """
    _git_('add', course=page.course, page=page, user=page.user, abspath=abspath)

def rms_commit(page, abspaths):
    """ Remove a list of files from a course's git repo, and commit. """
    _git_('rm -r', course=page.course, page=page, user=page.user, abspath=abspaths)

def get_history(page):
    """ Get a file's git log, returning [(revision, date, author),... ] """
    path = quote(page.get_gitpath())
    repo = quote(page.course.abspath)
    format = """--pretty=format:'{"commit":"%H", "date":"%aI", "msg": "%s"},'"""
    # Note that git log dates are in UTC, not local time zone.
    log_string = run(f'git -C {repo} log {format} {path}').replace(
        system_username, '')
    print_debug(f" gitlocal get_history log_string='{log_string}' ")
    log_raw = json.loads('[' + log_string[:-1] + ']') # omit last comma
    # len('umber_editor ')==13, so author username is message[13:]
    log = [(entry['commit'], entry['date'], entry['msg'][13:])
           for entry in log_raw]
    print_debug(f' gitlocal get_log : "{log}"')
    return log
    
def get_revision(page):
    """ Return a file's content from a given revision. """
    # The revisions are given by git commit hashes,
    # and passed into this routine within the page object.
    path = quote(page.get_gitpath())
    repo = quote(page.course.abspath)
    revision = page.revision_commit
    content = run(f'git -C {repo} show {revision}:{path}')
    print_debug(f' gitlocal get_revision : "{content[:16]}...{content[-16:]}"')
    return content

if __name__ == '__main__':
    import doctest
    doctest.testmod()

