"""
 gitlocal.py

 These git utilities work with a local repository.
 They can :
   * set up a git repository in a course's folder
   * add and remove files or folders from the repo
   * get the history (git log) of versions of a file
   * get the content of one previous version of a file

"""
# This implementation is based on python subprocess.run
# ... which may be problematic in a web app environment.

from utilities import print_debug
from shlex import quote
import subprocess
import json

def run(*commands, timeout=1.0, verbose=True):
    """ Run commands in a subprocess and return their output.
        >>> print(run('echo hello', 'echo goodbye', verbose=False))
        hello
        goodbye
        <BLANKLINE>
    """
    # Since I'm using && between the commands,
    # each will only run if the previous ones succeed.
    argstring = ' && '.join(commands)
    if verbose:
        print_debug(f" gitlocal run argstring='{argstring}'")
    try:
        result = subprocess.run([argstring], timeout = timeout,
                                shell = True, capture_output = True,
                                text = True, check = False)
        if verbose:
            print_debug(f" gitlocal run result.stdout='{result.stdout}'")
            print_debug(f" gitlocal run result.stderr='{result.stderr}'")
        return result.stdout
    except Exception as e:
        print_debug(f" gitlocal run error '{e}' ")
        # TODO : ... handle this properly in the calling routines
        return 'FAIL'

system_username = '__system__'
    
def _git_(command, course=None, page=None, user=None):
    """ Run a sequence of git command strings 
        e.g. ('git init ...', 'git add ...', 'git commit ...') """
    username = quote(user.username) if user else system_username
    path = quote(page.get_gitpath()) if page else ''
    repo = quote(course.abspath)
    git_command = f'git -C {repo} {command} {path}'
    git_commit = f'git -C {repo} commit -m "umber_editor {username}"'
    if command == 'init':
        run(git_command, f'/bin/git -C {repo} add .', git_commit)
    else:
        run(git_command, git_commit)

def init_add_commit(course, user):
    """ Create a new .git repo in a course, add its files, and commit. """
    _git_('init', course=course, page=None, user=user)

def add_commit(page):
    """ Add one file or folder to the course's git repo, and commit. """
    _git_('add', course=page.course, page=page, user=page.user)

def rm_commit(page):
    """ Remove one file or folder from a course's git repo, and commit. """
    _git_('rm -r', course=page.course, page=page, user=page.user)

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

