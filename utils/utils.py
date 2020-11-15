import sqlite3
import hashlib
import os
import sys
from sqlalchemy.sql import table, column, select, update, insert
from sqlalchemy import Table, MetaData, create_engine, and_, desc, join
from .api.sql_api import sql_connection
from werkzeug.security import generate_password_hash
from loguru import logger
import random
import string
from flask_login import current_user



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
                completion = check_password(dbPass, password)
    return completion


def check_password(hashed_password, user_password):
    print(hashlib.md5(user_password.encode()).hexdigest())
    return hashed_password == hashlib.md5(user_password.encode()).hexdigest()


# print(validate('admin', 'admin'))

def validate_invite(invite_code):
    connection, meta = sql_connection()
    table_invites = Table('INVITE_INFO', meta)
    db_invite_code = connection.execute(select([table_invites.c.CODE]) \
                                        .where(and_(table_invites.c.CODE == invite_code,
                                                    table_invites.c.ACTIVATED == None))).fetchall()
    if len(db_invite_code) != 1:
        return False
    else:
        update_statement = table_invites.update().where(table_invites.c.CODE == invite_code) \
            .values(ACTIVATED='true')
        connection.execute(update_statement)
        return True


def get_invites_table():
    connection, meta = sql_connection()
    table_invites = Table('INVITE_INFO', meta)
    invites_table = connection.execute(
        select([table_invites.c.ID, table_invites.c.CODE, table_invites.c.ACTIVATED])).fetchall()
    ids = [data[0] for data in invites_table]
    code = [data[1] for data in invites_table]
    activated = [data[2] for data in invites_table]
    return ids, code, activated


def generate_invite_codes(num_of_codes):
    connection, meta = sql_connection()
    table_invites = Table('INVITE_INFO', meta)
    try:
        for i in range(0, int(num_of_codes)):
            random_code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12))
            connection.execute(table_invites.insert().values(CODE=random_code))
        return True
    except TypeError as e:
        logger.critical(e, "Error while creating invites.")
        return False


def get_user_role():
    connection, meta = sql_connection()
    table_users = Table('user', meta)
    user_id = current_user.get_id()
    try:
        user_role = connection.execute(select([table_users.c.role]) \
                                       .where(table_users.c.id == user_id)).fetchone()[0]
        return user_role
    except Exception as e:
        logger.critical(e)
        return ""


def get_users_dict():
    connection, meta = sql_connection()
    table_users = Table('user', meta)
    user_role = connection.execute(select([table_users.c.id, table_users.c.username, table_users.c.role])).fetchall()
    user_id = [data[0] for data in user_role]
    username = [data[1] for data in user_role]
    user_role = [data[2] for data in user_role]
    logger.warning(dict(zip(user_id, zip(username, user_role))))
    return dict(zip(user_id, zip(username, user_role)))


def set_new_user_role(user_id, new_role):
    connection, meta = sql_connection()
    table_users = Table('user', meta)
    try:
        update_statement = table_users.update().where(table_users.c.id == int(user_id)) \
            .values(role=str(new_role))
        connection.execute(update_statement)
        return True
    except Exception as e:
        logger.critical(e)
        return False


def change_password_for_user(new_pass):
    connection, meta = sql_connection()
    table_users = Table('user', meta)
    user_id = current_user.get_id()
    new_pass_encrypted = generate_password_hash(new_pass, method='sha256')
    try:
        update_statement = table_users.update().where(table_users.c.id == int(user_id)) \
            .values(password=str(new_pass_encrypted))
        connection.execute(update_statement)
        return True
    except Exception as e:
        logger.critical(e)
        return False

