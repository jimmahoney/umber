# -- coding: utf-8 --
"""
 model2.py
 
 database model for umber : sqlite3 database , pewee ORM

    # installing it :
    pip install peewee

    # features :
    playhouse.flask_utils : open/close db correctly during web request
    playhouse.reflection  : database introspection - models from existing database

 See database/sqlite    
 
 
"""

from settings import db_path

from peewee import SqliteDatabase
from playhouse.reflection import Introspector

db = SqliteDatabase(db_path)
introspector = Introspector.from_database(db)
