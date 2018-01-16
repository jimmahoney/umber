# umber project Makefile
#
# inspired by github.com/JackStouffer/Flask-Foundation/blob/master/Makefile
#
# Ubuntu 16.04 , Jan 2018 , system default python 2.7.12
#

help:
	@echo " prereqs  install other software prerequesites"
	@echo " env	 create devel environment (assumes python2.7 & virtualenv)"
	@echo " deps	 install python dependencies with pip"

prereqs:
	sudo apt-get install git
	sudo apt-get install sqlite3
	sudo apt-get install virtualenv
	sudo apt-get install libapache2-mod-wsgi
env:
	virtualenv venv && . env/activate && make deps

deps:
	pip install -r env/requirements
