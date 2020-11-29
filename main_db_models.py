from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import MetaData, Table
from sqlalchemy.sql import func

postgres = 'postgresql+psycopg2://user:user@localhost:5432/maindb'

engine = create_engine(postgres, echo=False)
connection = engine.connect()
Base = declarative_base()

class user(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True) # primary keys are required by SQLAlchemy
    username = Column(String(100), unique=True)
    password = Column(String(100))
    token = Column(String(100))
    role = Column(String(100))
    team = Column(Integer)
    # test_case=relationship("TEST_CASES")

class Test_Suites(Base):
    __tablename__ = 'TEST_SUITES'
    TEST_SUITE_ID = Column(Integer, primary_key=True)
    TEST_SUITE_NAME = Column(String)
    CREATED_BY = Column(String)
    CREATED_DATE = Column(DateTime(timezone=False), server_default=func.now())
    # test_case = relationship("TEST_CASES")

class Test_Cases(Base):
    __tablename__ = 'TEST_CASES'
    TEST_SUITE_ID = Column(Integer, ForeignKey('TEST_SUITES.TEST_SUITE_ID'))
    TEST_CASE_ID = Column(Integer, primary_key=True)
    TEST_CASE_ADO_ID = Column(Integer)
    TEST_CASE_NAME = Column(String)
    STATUS = Column(String)
    DURATION_SEC = Column(Integer)
    EXECUTED_BY = Column(String, ForeignKey('user.username'))
    CHANGE_STATE_DATE = Column(DateTime(timezone=False), server_default=func.now())
    # test_step = relationship("TEST_STEPS")

class Test_Steps(Base):
    __tablename__ = 'TEST_STEPS'
    ID = Column(Integer, primary_key=True)
    TEST_CASE_ID = Column(Integer, ForeignKey('TEST_CASES.TEST_CASE_ID'))
    STEP_NUMBER = Column(Integer)
    DESCRIPTION = Column(String)
    EXPECTED_RESULT = Column(String)
    STEP_STATUS = Column(String)
    COMMENT = Column(String)

class Invite_Info(Base):
    __tablename__ = 'INVITE_INFO'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    CODE = Column(String)
    ACTIVATED = Column(String)
    ACTIVATED_BY = Column(Integer)

class Teams_Info(Base):
    __tablename__ = 'TEAMS_INFO'
    ID = Column(Integer, primary_key=True, autoincrement=True)
    TEAM = Column(String)
    DATABASE = Column(String)

def create_table():
    metadata = MetaData()
    Base.metadata.create_all(engine)
    connection.close()
    engine.dispose()

# Uncomment to create a new DB tables
# create_table()