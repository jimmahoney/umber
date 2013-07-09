"""
 ... in progress ...

"""

from model import Course

class Page(object):

    def __init__(self, coursepath=None, request=None, user=None, insecure_login=False):
        self.insecure_login = insecure_login  # set to False if https available
        self.request = request
        self.secure_url = 'https://' + request.host + request.path
        self.coursepath = coursepath
        self.course = Course()
        self.uri_links = '- uri_links -'
        self.path = request.path if request != None else ''
        self.full_path = request.full_path if request != None else ''
        self.title = '- title -'
        self.has_error = False
        self.has_lastmodified = True
        self.lastmodified = ' - MODIFIED DATE -'
        

