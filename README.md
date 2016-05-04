
umber
=====

a course management web application built from [wikiacademia][]
using python's Flask web framework, sqlite3, and git.

development testing
--------------------

    $ source ./env/activate    # setup shell environment (PATH, UMBER_ROOT)

    $ ./database/init_db       # initialize database (WARNING: deletes old data)

    $ ./run/test               # run software tests (assumes database init)

    $ ./run/console            # interact with database from command line
    >>> demo
    <Course name='Demo Course' ...>
    >>> demo.assignments
    >>> demo.persons
    >>> Person.find_by(username='johnsmith')
    <Person name = 'Johnny Smith' ...>
    >>> # see src/model.py for examples

    $ ./run/server
    then visit http://localhost:8080 or https://localhost:8433
    at /test or /umber/demo/home

For more details start docs/history.txt and src/umber.py.

----------------------------------------------------------

Jim Mahoney | cs.marlboro.edu | June 2013 | MIT License

[wikiacademia]: http://cs.marlboro.edu/wikiacademia/source_code 
                "wikiacademia source code"
