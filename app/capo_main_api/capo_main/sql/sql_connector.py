from .config import Config
import logging
import traceback
import pymysql
import functools
import aiomysql
import asyncio
import time

MAX_RETRIES = 10

# DB Connectors
# Class methods, functions, and awaits have different signatures
# so we need a connector for each type

def _pymysql_connect():
    print('Connecting to db: ', Config.get('db')['host'], Config.get('db')['port'] )
    return pymysql.connect(
            host=Config.get('db')['host'],
            user=Config.get('db')['user'],
            password=Config.get('db')['password'],
            db=Config.get('db')['db_name'],
            port=Config.get('db')['port'],
            connect_timeout=10,
            autocommit=True
        )

def _connection():
    try:
        connection = _pymysql_connect()
        return connection

    except:
        i = 0
        while i < MAX_RETRIES:
            i += 1
            print('Lost connection to DB. Reconnect attempt: ' + str(i), end="\r")
            time.sleep(1)
            try:
                connection = _pymysql_connect()
                print('\nSuccessfully re-connected')
            except:
                connection = None
                pass

    return connection

def connector(func):
    def db_conn(*args, **kwargs):

        connection = _connection()
        
        if connection:
            with connection:
                cur = connection.cursor()
                res = func(cur, *args, **kwargs)
        else:
            print('\nError connecting to database at: ' + str(Config.get('db')['host']))
            res = {'status': 'Error connecting to database'}
        
        return res
    return db_conn

def connector_for_class_method(func):
    async def db_conn(self, *args, **kwargs):

        connection = _connection()
        
        if connection:
            with connection:
                cur = connection.cursor()
                res = func(self, cur, *args, **kwargs)
        else:
            print('\nError connecting to database at: ' + str(Config.get('db')['host']))
            res = {'status': 'Error connecting to database'}
        
        return res
    return db_conn

# Seperate connector for insert function. (the func has to be awaited, this throws an error with non update funcs)
def connector_for_class_post_method(func):
    def db_conn(self, *args, **kwargs):

        connection = _connection()
        
        if connection:
            with connection:
                cur = connection.cursor()
                res = func(self, cur, *args, **kwargs)
        else:
            print('\nError connecting to database at: ' + str(Config.get('db')['host']))
            res = {'status': 'Error connecting to database'}
        
        return res
    return db_conn