# umber project Makefile
# adapted from https://github.com/JackStouffer/Flask-Foundation/blob/master/Makefile

help:
	@echo " env	create devel environment (assumes python2.7 & virtualenv)"
	@echo " deps	install python dependencies with pip"

env:
	virtualenv --python=python2.7 venv && \
        . env/activate && \
        make deps

deps:
	pip install -r env/requirements
