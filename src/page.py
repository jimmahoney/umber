# -- coding: utf-8 --
"""
 page.py

 a Page corresponds to both
    (a) a URL, and
    (b) a file or folder in the filesystem.

 Pages are not in the sql database (and not part of the 'model' per se),
 though there are some file and folder meta-data that may be in the
 database such as course assignments and student submitted work.
  
  TODO  find some way to cache (path,course,user,privilege) connections,
        either in the filesystem or the database.)

  TODO  the conversion of markdown or wiki files to html could be
        cached in sql database Page objects. If so, a hash would be
        needed to keep track of whether the file had changed since the
        sql data had been cached. That could speed things up assuming
        the hash computation is faster than the markdown conversion)
        at the cost of database size and code complexity.
 
 --- paths, folders, urls, and all that ---

 The vocabulary terms that I'm using to describe file and url addresses
 for courses, directories, and files are 'path', 'basename', and 'name.
 I'll use an example to illustrate.

 If the settings on my laptop development machine are

    os_root    /Users/mahoney/academics/umber
    url_base   umber
    os_base    courses

 then for the 'notes/week1' file within a course at 'fall/math'
 we would have

    url     http://localhost:8090/  umber    /  fall/math   /  notes/week1
                   host             url_base    course_path    file_path
                       
    file    /Users/mahoney/academics/umber / courses / fall/math  / notes/week1
            os_root                          os_base   course_path  file_path
                 
 My definitions are then
 
    path         address after base
                 e.g. fall/math               for this course
                      fall/math/notes/week1   for this file

    basename     last word in address (same as os.path.basename)
                 e.g. math                    for this course
                      week1                   for this file
                      
    file name    address after course's path, without leading slash
                 e.g. notes/week1             for this file
    
    course name  anything (actual name of course, not part of address)
                 e.g. "Math 101" (or whatever)

 This url would have in its flask reuest

    request.url_root        'http://localhost:8090/'
    request.path            '/umber/fall/math/notes/week1'
                  
 Leading slashes are left off my paths.
                  
 This implies that
    * course and file paths do not start with or end with slashes.
    * course and file paths are unique
    * course_path + file_name = file_path
    * file paths always have a course path as a prefix
    * files with the same name may be in many courses (i.e. notes/week1)

 Folders have nearly the same notion of path, basename, and name as files, i.e.
    * their path has the course path as a prefix, and
    * their name is the address within the course
      (which may be the empty string if it the top folder in a course).
 The difference is that folder paths always end in a trailing slash,
 as do their URLs. If the trailing slash for a folder is missing,
 the URL redirects.
    * url     http://localhost:8090/umber/fall/math/notes/
              http://localhost:8090/umber/fall/math/notes  redirects to notes/
    * path    fall/math/notes/
            
 A Page corresponds to a URL for a file or a folder, not a course.
 (And in fact the path for a course e.g. fall/math is not that 
 same as the path for that course's top folder e.g. fall/math/ .)

 Some file suffixes which are understood by the umber framework
 and displayed within the course layout (.wiki = media-wiki-ish markup,
 .md = markdown-ish markup, .umber = special page) are optional
 (and generally discouraged) in URLs . 
 
"""

from settings import os_root, os_base
import os

class Page(object):
    """ a url-accessable file or folder in a Course """
        # example:
        #    request.url       'http://localhost:8080/umber/demo/home'
        #    request.url_root  'http://localhost:8080/'
        #    request.path      '/umber/demo/home' 
        #    path              'demo/home'
        #    
    
    def __init__(self, 
                 path = None,    # URL=host/url_base+path eg /demo/home
                 request = None, # flask Request object
                 user = None     # Person
                 ):
        
        self.user = user or anonymous_person()
        self.path = path
        self.abspath = os.path.join(os_root, os_base, path) # os.path.abspath
        if len(path)>0 and path[-1]=='/':
            # when path ends in a slash, e.g. 'foo/bar/'
            # the basename (i.e. name of this folder) here will be 'bar',
            # which isn't os.path.basename's behavior.
            self.basename = os.path.basename(path[:-1])
        else:
            self.basename = os.path.basename(path)
        if request:
            self.request = request
            if request.is_secure:
                secure_host = request.host
                host = secure_host.replace(str(https_port), str(http_port))
            else:
                host = request.host
                secure_host = host.replace(str(http_port), str(https_port))
            self.secure_url = 'https://' + secure_host + request.path
            self.url = 'http://' + host + request.path            
        else: # debugging
            self.request = None
            self.secure_url = ''
            self.url = ''

        raise Exception('debug')
            
        # need:
        # course ?
        # file or directory ?
        # access privileges 
                
        #self.course = self.directory.course
        #self.title = self.course.name + " - " + self.name
        #try:
        #    self.role = Registration.find_by(course=self.course, 
        #                                     person=self.user).role
        #except:
        #    self.role = Role.named('all')
        #self.can_write = self.directory.can_write(self.user, self.role)
        #self.can_read = self.directory.can_read(self.user, self.role)
        
        self.has_error = False
        self.has_lastmodified = True
        self.uri_links = '- uri_links -'
        self.lastmodified = ' - MODIFIED DATE -'  # TODO : what should this be?
    def __str__(self):
        return "<Page path='{}' id={}>".format(self.path, id(self))
    def os_fullpath(self):
        if self.pagepath == '':
            # skip self.path; else end up with trailing /
            return os.path.join(os_root, os_base)
        else:
            return os.path.join(os_root, os_base, self.pagepath)

