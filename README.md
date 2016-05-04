umber
=====

a course management web application built from [wikiacademia][]
using python's Flask web framework, sqlite3, and git.

development testing
--------------------

    $ source env/activate # setup shell environment (PATH, UMBER_ROOT)

    $ umber_init_db       # put test data in database

    $ umber_test          # run software tests

    $ umber_console       # interact with database from command line
    >>> demo
    <Course name='Demo Course' ...>
    >>> demo.assignments
    >>> demo.persons
    >>> Person.find_by(username='johnsmith')
    <Person name = 'Johnny Smith' ...>
    >>> # see src/model.py for examples

    $ umber_server  # then visit e.g.
                    #   http://localhost:8080/test
                    #   http://localhost:8080/umber/demo/home
                    #   https://localhost:8433/test
                    #   https://localhost:8433/umber/demo/home

For more details, start at docs/history.txt and src/umber.py.

----------------------------------------------------------
Jim Mahoney | cs.marlboro.edu | June 2013 | MIT License

[wikiacademia]: http://cs.marlboro.edu/wikiacademia/source_code 
                "wikiacademia source code"
