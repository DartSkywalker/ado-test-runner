import sqlite3
from sqlite3.dbapi2 import Error

from loguru import logger
from sqlalchemy import create_engine, MetaData, Table

my_sql = 'mysql+mysqlconnector://user:user@localhost:3306/ado'
postgres = 'postgresql+psycopg2://user:user@localhost:5432/ado'


def sql_connection():
    engine = create_engine(postgres, echo=False, pool_recycle=2)
    connection = engine.connect()
    meta = MetaData()
    meta.reflect(bind=engine)
    return connection, meta


def create_db_connection(db_file):
    """
    Create a database connection to a SQLite database
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        logger.critical(f"Cannot connect to {db_file} database")

connection, meta = sql_connection()

table_user = Table('user', meta)
table_suites = Table('TEST_SUITES', meta)
table_cases = Table('TEST_CASES', meta)
table_steps = Table('TEST_STEPS', meta)