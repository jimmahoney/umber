# umber project Makefile
#
# inspired by github.com/JackStouffer/Flask-Foundation/blob/master/Makefile
#
# Ubuntu 16.04 , Jan 2018 , system default python 2.7.12
#

help:
	@echo " prereqs       install system software prerequesites"
	@echo " environment   install python(2.7) environment and modules"

prereqs:
	sudo apt-get install git
	sudo apt-get install sqlite3
	sudo apt-get install virtualenv
	sudo apt-get install libapache2-mod-wsgi

environment:
	virtualenv --python=python2.7 venv && . env/activate && make modules

modules:
	pip install -r ./env/requirements.txt

all:
	make prereqs
	make environment
