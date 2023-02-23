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
# import sqlalchemy # pip install SQLAlchemy
print(f"Import: OK <{__name__}>")

class SQLiteDB(object):
    """
    SQLite object.

    Args:
        db_filename (str, optional): filename of database. Defaults to ''.
        connect (bool, optional): whether to connect to database. Defaults to False.
    """
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
        """
        Make connection to database.

        Args:
            db_filename (str, optional): filepath of database. Defaults to ''.

        Returns:
            Connection: connection object
        """
        if len(db_filename) == 0:
            db_filename = self.filename
        try:
            self.conn = sqlite3.connect(db_filename)
            print(sqlite3.version)
        except sqlite3.Error as err:
            print(err)
        return self.conn
    
    def disconnect(self, full=False):
        """
        Disconnect from cursor.

        Args:
            full (bool, optional): whether to disconnect from database as well. Defaults to False.
        """
        if self.cursor:
            self.cursor.close()
        if self.conn and full:
            self.conn.close()
        return

    def executeSQL(self, sql:str, close=False):
        """
        Execute SQL command.

        Args:
            sql (str): SQL command to be executed
            close (bool, optional): whether to close cursor after execution. Defaults to False.

        Raises:
            Exception: Connection not found
        """
        if self.conn == None:
            raise Exception('Connection not found!')
        self.cursor = self.conn.cursor()
        self.cursor.execute(sql)
        if close:
            self.disconnect()
        return
    
    def fetchQuery(self, sql:str):
        """
        Fetch results from SQL query

        Args:
            sql (str): SQL query to be fetched

        Returns:
            pd.DataFrame: dataframe of retrieved SQL query
        """
        df = pd.DataFrame()
        df = pd.read_sql(sql, self.conn)
        return df