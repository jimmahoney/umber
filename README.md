
umber
=====

a course management web application built from [wikiacademia][]
with python's Flask web framework, sqlite3, and git.

development testing
--------------------

    $ ./database/reset_db
    $ ./console
    >>> demo
    <Course name='Demo Course' ...>
    >>> demo.assignments
    >>> demo.persons
    >>> Person.find_by(username='johnsmith')
    <Person name = 'Johnny Smith' ...>

    $ python umber.py
    visit http://localhost:8080/test
    visit http://localhost:8080/umber/demo/home
 
    $ SSL=true python umber.py
    visit https://localhost:8433/test
    visit https://localhost:8433/umber/demo/home

See umber.py and docs/history.txt for more.

----------------------------------------------------------

Jim Mahoney | cs.marlboro.edu | June 2013 | MIT License

[wikiacademia]: http://cs.marlboro.edu/wikiacademia/source_code 
                "wikiacademia source code"
