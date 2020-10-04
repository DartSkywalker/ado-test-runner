import sqlite3
import hashlib
import os
import sys

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