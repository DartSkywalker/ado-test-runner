import sqlite3
import hashlib
import os
import sys
from sqlalchemy.sql import table, column, select, update, insert
from sqlalchemy import Table, MetaData, create_engine, and_, desc, join
from .api.ado_api import sql_connection, get_current_user
from loguru import logger


def validate(username, password):
    con = sqlite3.connect('ado.db')
    completion = False
    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM USERS")
        rows = cur.fetchall()
        for row in rows:
            dbUser = row[0]
            print(dbUser)
            dbPass = row[1]
            if str(dbUser) == str(username):
                print('SOEM')
                completion=check_password(dbPass, password)
    return completion

def check_password(hashed_password, user_password):
    print(hashlib.md5(user_password.encode()).hexdigest())
    return hashed_password == hashlib.md5(user_password.encode()).hexdigest()

# print(validate('admin', 'admin'))

def validate_invite(invite_code):
    connection, meta = sql_connection()
    table_invites = Table('INVITE_INFO', meta)
    db_invite_code = connection.execute(select([table_invites.c.CODE])\
            .where(and_(table_invites.c.CODE == invite_code,
                        table_invites.c.ACTIVATED == None))).fetchall()
    if len(db_invite_code) != 1:
        return False
    else:
        update_statement = table_invites.update().where(table_invites.c.CODE == invite_code) \
            .values(ACTIVATED='true')
        connection.execute(update_statement)
        return True
