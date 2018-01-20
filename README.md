umber
=====

a course management web app built with python Flask, sqlite3, and git.

development & testing
---------------------

    # -- setup --
    $ . env/activate       # set shell variables & enable python environment
    $ umber_init_db        # create database with default test data
    $ umber_test           # run a few doc tests (TODO: write lots more ...)

    # -- interactive --
    $ umber_console        # interact with database from command line
    >>> democourse
    <Course name='Demo Course' ...>
    >>> democourse.assignments
    >>> democourse.persons
    >>> john = Person.get(username='johnsmith')
    <Person name = 'Johnny Smith' ...>
    # See src/model.py for more examples

    # -- development server --
    $ umber_server
    # then visit http://127.0.0.1:5000/umber/demo/home

production
----------

Like any Flask app, it can be deployed with wsgi. 
See src/umber.wsgi and env/shell_production for more.

----------------------------------------------------------

Jim Mahoney | cs.marlboro.edu | Jan 2018 | MIT License | github.com/jimmahoney/umber
