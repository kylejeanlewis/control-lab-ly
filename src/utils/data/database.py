# %%
# -*- coding: utf-8 -*-
"""
Created on 

@author: Chang Jie
"""
import pyodbc # pip install pyodbc
import pandas as pd
import sqlite3
from sqlite3 import Error
print(f"Import: OK <{__name__}>")


class SQLiteDB(object):
    def __init__(self, db_file=None):
        self.filename = db_file
        self.conn = None
        self.tables = {}

        if self.filename:
            self.create_connection(self.filename)
        return

    def close_connections(self, cursor=None):
        '''
        Close connections to database and cursor
        - cursor: cursor object to be closed

        Returns: None
        '''
        if cursor:
            cursor.close()
        if self.conn:
            self.conn.close()
        return

    def create_connection(self, db_file):
        '''
        Create a database connection to database
        - db_file: file path of database

        Returns: database connection object
        '''
        try:
            self.conn = sqlite3.connect(db_file)
            print(sqlite3.version)
        except Error as err:
            print(err)
        return self.conn

    def execute_query(self, sql, close=False):
        '''
        Execute the SQL string
        - sql: SQL command to be executed
        - close: whether to close connections

        Returns: cursor object
        '''
        if self.conn == None:
            print('Connection not found!')
            return
        cursor = self.conn.cursor()
        cursor.execute(sql)
        if close:
            self.close_connections(cursor)
            return
        return cursor
    
    def fetch_query(self, sql, close=False):
        '''
        Retreives data from database
        - sql: SQL command
        - close: whether to close connections

        Returns: dataframe of requested data (pd.Dataframe)
        '''
        df = pd.DataFrame()
        try:
            df = pd.read_sql(sql, self.conn)
            date_cols = [c for c in df.columns.to_list() if 'date' in c.lower()]
            for col in date_cols:
                try:
                    df[col] = df[col].dt.strptime('%Y-%m-%d')
                except:
                    pass
        except Error as err:
            print('Unable to fetch query!')
            print(err)
        finally:
            if close:
                self.close_connections()
        return df
    
    def get_all_tables(self, close=False):
        '''
        Retreives all the tables in database and store in self.tables attribute
        - close: whether to close connections

        Returns: None
        '''
        sql = """SELECT name FROM sqlite_master WHERE type='table'"""
        cursor = self.execute_query(sql)
        tables = cursor.fetchall()
        table_names = [t[0] for t in tables]

        for table_name in table_names:
            self.tables[table_name] = self.fetch_query(f"""SELECT * FROM {table_name}""")
        if close:
            self.close_connections(cursor)
        return

    def import_all_tables(self, other_db, map_file, close=False):
        '''
        Import all tables from another database to this database
        - other_db: database object
        - map_file: txt file with the maps of table names
        - close: whether to close connections

        Returns: None
        '''
        tables_map = []
        with open(map_file, 'r') as m:
            lines = m.readlines()
            for line in lines:
                tables_map.append(line.split(':'))
        
        for other_table, table_name in tables_map:
            sql = f"""SELECT * FROM {other_table}"""
            df = other_db.fetch_query(sql)
            date_cols = [c for c in df.columns.to_list() if 'date' in c.lower()]
            for col in date_cols:
                try:
                    df[col] = df[col].dt.strftime('%Y-%m-%d')
                except:
                    pass
            print(table_name)
            self.import_table(df, table_name)
        if close:
            self.close_connections()
        return

    def import_table(self, df, table_name, close=False):
        '''
        Import a table from pandas.Dataframe to database
        - df: Dataframe object
        - table_name: table name of target table to which data is imported to
        - close: whether to close connections

        Returns: None
        '''
        sql = f"""SELECT * FROM {table_name}"""
        cursor = self.execute_query(sql)
        cols = [c[0] for c in cursor.description]
        col_names = ', '.join(cols)
        n_cols = ', '.join(['?' for _ in range(len(cols))])
        
        params = df.to_dict('split')['data']
        sql = f"""
            INSERT INTO {table_name} ({col_names}) 
            VALUES ({n_cols}) """
        self.update_database(sql, params, close=close)
        return

    def reconnect(self):
        '''
        Re-establish connection with database

        Returns: database connection object
        '''
        self.create_connection(self.filename)
        return self.conn

    def setup_database(self, sql_file, close=False):
        '''
        Prepares the tables / views in the database
        - sql_file: SQL file with the set-up instructions
        - close: whether to close connections

        Returns: None
        '''
        with open(sql_file, 'r') as s:
            sql = s.read()
            commands = sql.split(';')
        for cmd in commands:
            cursor = self.execute_query(cmd)
        if close:
            self.close_connections(cursor)
        return

    def update_database(self, sql, params, close=False):
        '''
        Writes data into database
        - sql: SQL command
        - params: list of lists of values to be written into database
        - close: whether to close connections

        Returns: None
        '''
        cursor = self.conn.cursor()
        print("Writing to database...")
        try:
            cursor.executemany(sql, params)
        except Error as err:
            print("Database Error!")
            print(err)
            self.conn.rollback()
        else:
            self.conn.commit()
            print("Success!")
        if close:
            self.close_connections(cursor)
        return


class AccessDB(SQLiteDB):
    def __init__(self, db_file=None):
        super().__init__(db_file=db_file)
        return

    def create_connection(self, db_file):
        '''
        Create a database connection to database
        - db_file: file path of database

        Returns: database connection object
        '''
        try:
            self.conn = pyodbc.connect('Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ='+db_file+';')
        except pyodbc.DatabaseError as err:
            print(err)
        return self.conn

    def update_database(self, sql, params, close=False):
        '''
        Writes data into database
        - sql: SQL command
        - params: list of lists of values to be written into database
        - close: whether to close connections

        Returns: None
        '''
        cursor = self.conn.cursor()
        print("Writing to database...")
        try:
            self.conn.autocommit = False
            cursor.executemany(sql, params)
        except pyodbc.DatabaseError as err:
            print("Database Error!")
            self.conn.rollback()
        else:
            self.conn.commit()
            print("Success!")
        finally:
            self.conn.autocommit = True
        if close:
            self.close_connections(cursor)
        return


# %%
def main():
    global db, accdb
    
    db = SQLiteDB('qd_database.db')
    accdb = AccessDB(r'C:\Users\leongcj\A STAR\QD cocktail party - General\Experiment logs\QD database.accdb')
    try:
        if db.conn and accdb.conn:
            db.setup_database('setup_tables.sql')
            db.import_all_tables(accdb, 'map_tables.txt')
            db.setup_database('setup_views.sql')
        if db.conn:
            db.get_all_tables()
    finally:
        if db.conn:
            db.close_connections()
        if accdb.conn:
            accdb.close_connections()
    return

if __name__ == '__main__':
    main()
    print('Done!')


# %%
