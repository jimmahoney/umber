umber
=====

a course management web app built with python Flask, sqlite3, and git.

installation
-------------

Tested on Ubuntu 16.05 with python 2.7.12.

    # -- Install the system dependencies. --
    $ sudo apt-get install git sqlite3 virtualenv 

    # -- Get the project files. --
    $ git clone https://github.com/jimmahoney/umber.git
    $ cd umber

    # --Install the python environment and its required modules. --
    $ virtualenv --python=python2.7 venv
    $ . env/activate
    $ pip install -r ./env/requirements.txt



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
    # then visit http://127.0.0.1:5000/umber/demo/home with a browser.

production
----------

Like any Flask app, this can be deployed using WSGI, 
using for example libapache2-mod-wsgi or gunicorn.
See src/umber.wsgi and env/production for more information.

----------------------------------------------------------

Jim Mahoney | cs.marlboro.edu | Jan 2018 | MIT License | github.com/jimmahoney/umber
