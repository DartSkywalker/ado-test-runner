# from ..crelds import ADO_TOKEN
import os
from ..utils.api import ado_api
from flask_login import current_user
from flask import g
from sqlalchemy.sql import table, column, select, update, insert
from sqlalchemy import Table, MetaData, create_engine, and_,desc

def get_ado_token_for_user(username):
   connection, meta = ado_api.sql_connection()
   g.user = current_user.get_id()
   query = select([ado_api.table_user.columns['token']]).where(ado_api.table_user.c.id == g.user)
   token = connection.execute(query).fetchone()[0]
   return token


QUERY_ID = "abb94139-79de-4924-b2f1-73468d05fc20"
QUERY_LINK = "https://dev.azure.com/HAL-LMKRD/RESDEV/_apis/wit/queries/"
WIQL_LINK = "https://dev.azure.com/HAL-LMKRD/RESDEV/_apis/wit/wiql/"
WORKITEM_LINK = "https://dev.azure.com/HAL-LMKRD/RESDEV/_apis/wit/workitems/"
HEADERS = {'Content-type': 'application/json'}
DB_NAME = "ado.db"
USER_ROLES = ["admin", "manager", "engineer"]
