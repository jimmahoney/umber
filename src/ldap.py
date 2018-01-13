
from ldap3 import Server, Connection, ALL


def testing():
    s = Server('ldap.marlboro.edu', get_info=ALL)
    c = Connection(s, user='mahoney', password='red2shoes;')
    if not c.bind():
        print('error in bind', c.result)

