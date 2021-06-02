# import mysql.connector
from .config import config
import logging
import traceback
import pymysql
import functools
import aiomysql
import asyncio
from ..helper_funcs import print_req_info as print_req_info
import time

# try:
# connection = pymysql.connect(
#     host=config.db_conf['host'],
#     user=config.db_conf['user'],
#     password=config.db_conf['password'],
#     database=config.db_conf['db_name']
# )

# def connect():
#     connect = pymysql.connect(
#         host=config.db_conf['host'],
#         user=config.db_conf['user'],
#         password=config.db_conf['password'],
#         database=config.db_conf['db_name']
#     )
#     return connect

num_of_retries = 10

# @print_req_info
def connector(func):
    async def db_conn(*args, **kwargs):
        try:
            connection = pymysql.connect(
            host=config.db_conf['host'],
            user=config.db_conf['user'],
            password=config.db_conf['password'],
            db=config.db_conf['db_name'],
            port=config.db_conf['port']
            # autocommit=True
        )
        except:
            i = 0
            while i < num_of_retries:
                i += 1
                print('Lost connection to DB. Reconnect attempt: ' + str(i), end="\r")
                time.sleep(1)
                try:
                    connection = pymysql.connect(
                    host=config.db_conf['host'],
                    user=config.db_conf['user'],
                    password=config.db_conf['password'],
                    db=config.db_conf['db_name'],
                    port=config.db_conf['port']
                    # autocommit=True
                    )
                    print('\nSuccessfully re-connected')
                    break
                except:
                    connection = None
                    pass
        
        if connection:
            with connection:
                
                cur = connection.cursor()
                res = func(cur, *args, **kwargs)
            connection.close()
        else:
            print('\nError connecting to database at: ' + str(config.db_conf['host']))
            res = {'status': 'Error connecting to database'}
        
        return res
    return db_conn

def connector_for_class_method(func):
    async def db_conn(self, *args, **kwargs):
        try:
            
            connection = pymysql.connect(
            host=config.db_conf['host'],
            user=config.db_conf['user'],
            password=config.db_conf['password'],
            db=config.db_conf['db_name'],
            port=config.db_conf['port']
            # autocommit=True
            )
            
        except:
            i = 0
            while i < num_of_retries:
                i += 1
                print('Lost connection to DB. Reconnect attempt: ' + str(i), end="\r")
                time.sleep(1)
                try:
                    connection = pymysql.connect(
                    host=config.db_conf['host'],
                    user=config.db_conf['user'],
                    password=config.db_conf['password'],
                    db=config.db_conf['db_name'],
                    port=config.db_conf['port']
                    # autocommit=True
                    )
                    print('\nSuccessfully re-connected')
                    break
                except:
                    connection = None
                    pass
        
        if connection:
            with connection:
                
                cur = connection.cursor()
                res = func(self, cur, *args, **kwargs)
            connection.close()
        else:
            print('\nError connecting to database at: ' + str(config.db_conf['host']))
            res = {'status': 'Error connecting to database'}
        
        return res
    return db_conn

# Seperate connector for insert function. (the func has to be awaited, this throws an error with non update funcs)
def connector_for_class_post_method(func):
    def db_conn(self, *args, **kwargs):
        try:
            connection = pymysql.connect(
            host=config.db_conf['host'],
            user=config.db_conf['user'],
            password=config.db_conf['password'],
            db=config.db_conf['db_name'],
            port=config.db_conf['port']
            # autocommit=True
        )
        except:
            i = 0
            while i < num_of_retries:
                i += 1
                print('Lost connection to DB. Reconnect attempt: ' + str(i), end="\r")
                time.sleep(1)
                try:
                    connection = pymysql.connect(
                    host=config.db_conf['host'],
                    user=config.db_conf['user'],
                    password=config.db_conf['password'],
                    db=config.db_conf['db_name'],
                    port=config.db_conf['port']
                    # autocommit=True
                    )
                    print('\nSuccessfully re-connected')
                    break
                except:
                    connection = None
                    pass
        
        if connection:
            with connection:
                
                cur = connection.cursor()
                res = func(self, cur, *args, **kwargs)
            connection.close()
        else:
            print('\nError connecting to database at: ' + str(config.db_conf['host']))
            res = {'status': 'Error connecting to database'}
        
        return res
    return db_conn
    
# except Exception:
#     print("timed out connectionm------------------------")

# class mydb2:
#     try:
#         mydb = mysql.connector.connect(
#             host=config.db_conf['host'],
#             user=config.db_conf['user'],
#             password=config.db_conf['password'],
#             database=config.db_conf['db_name']
#         )
#     except:
#         print('Connection TOd')
#         mydb = mysql.connector.connect(
#             host=config.db_conf['host'],
#             user=config.db_conf['user'],
#             password=config.db_conf['password'],
#             database=config.db_conf['db_name']
#         )

# class curser:
#     try:
#         mycursor = connection.cursor()
#     except Exception:
#         print("timed out connectionm------------------------")
    

# class mydb:
# def db_connector(func):
#     print('in db conn')
#     # @functools.wraps(f)
#     def with_connection(*args, **kwargs):
#         connection = pymysql.connect(
#             host=config.db_conf['host'],
#             user=config.db_conf['user'],
#             password=config.db_conf['password'],
#             database=config.db_conf['db_name']
#         )
#         rv = None
#         try:
#             rv = func(connection=connection, *args, **kwargs)
#         except Exception:
#             traceback.format_exc()
#             # logging.error("Database connection error: "+)
#         else:
#             rv = func(connection, *args,**kwargs)
#         finally:
#             connection.close()
#         return rv
#     return with_connection


# class curser:
#     mycursor = mydb.mydb.cursor()
# loop = asyncio.get_event_loop()


# @asyncio.coroutine
# def db_connector(func):
#     print('in db conn')
#     pool = yield from aiomysql.create_pool(
#         host=config.db_conf['host'],
#         port=3306,
#         user=config.db_conf['user'],
#         password=config.db_conf['password'],
#         db=config.db_conf['db_name'],
#         loop=loop,
#         autocommit=True
#     )
#     # @functools.wraps(f)
#     def wrapper(*args, **kwargs):
#         with (yield from pool) as conn:
#             with (yield from conn.cursor()) as cur:
#                 # try:
#                 #     rv = func(cursor=cur, *args, **kwargs)
#                 # except Exception:
#                 #     traceback.format_exc()
#                 #     # logging.error("Database connection error: "+)
#                 # else:
#                 #     print('finished')
#                 # finally:
#                 #     pool.close()
#                 #     await pool.wait_closed()
#                 rv = func(cursor=cur, *args, **kwargs)
#                 return rv
#     return wrapper
