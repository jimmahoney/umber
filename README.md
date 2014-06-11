
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
    >>> # see src/model.py for examples

    $ ./server
    then visit http://localhost:8080 or https://localhost:8433
    at /test or /umber/demo/home

For the details, start at umber.py and docs/history.txt.

----------------------------------------------------------

Jim Mahoney | cs.marlboro.edu | June 2013 | MIT License

[wikiacademia]: http://cs.marlboro.edu/wikiacademia/source_code 
                "wikiacademia source code"
