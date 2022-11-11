# %% -*- coding: utf-8 -*-
"""
Created: Tue 2022/11/11 10:34:30
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import os
import pandas as pd
import sqlite3
import sqlalchemy # pip install SQLAlchemy
print(f"Import: OK <{__name__}>")

class SQLiteDB(object):
    def __init__(self, db_filename='', connect=False):
        self.conn = None
        self.cursor = None
        self.filename = db_filename
        self.tables = {}

        if not os.path.exists(db_filename):
            os.makedirs(db_filename)
        if connect:
            self.connect(db_filename)
        return
    
    def __delete__(self):
        return self.disconnect(full=True)
    
    @property
    def filename(self):
        return self.__filename
    
    @filename.setter
    def filename(self, value):
        if not value.endswith('.db'):
            raise Exception("Input a filename with '.db' filename extension")
        self.__filename = value
        return
    
    def connect(self, db_filename=''):
        '''
        Create a database connection to database
        - db_file: file path of database

        Returns: database connection object
        '''
        if len(db_filename) == 0:
            db_filename = self.filename
        try:
            self.conn = sqlite3.connect(db_filename)
            print(sqlite3.version)
        except sqlite3.Error as err:
            print(err)
        return self.conn
    
    def disconnect(self, full=False):
        '''
        Close connections to database and cursor
        - cursor: cursor object to be closed

        Returns: None
        '''
        if self.cursor:
            self.cursor.close()
        if self.conn and full:
            self.conn.close()
        return

    def executeSQL(self, sql, close=False):
        '''
        Execute the SQL string
        - sql: SQL command to be executed
        - close: whether to close connections

        Returns: cursor object
        '''
        if self.conn == None:
            raise Exception('Connection not found!')
        self.cursor = self.conn.cursor()
        self.cursor.execute(sql)
        if close:
            self.disconnect()
        return
    
    def fetchQuery(self, sql, close=False):
        df = pd.DataFrame()
        df = pd.read_sql(sql, self.conn)
        return