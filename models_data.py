from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy import MetaData, Table

engine = create_engine('sqlite:///db.sqlite', echo=True)
connection = engine.connect()
Base = declarative_base()

class User(Base):
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True) # primary keys are required by SQLAlchemy
    username = Column(String(100), unique=True)
    password = Column(String(100))
    token = Column(String(100))
    # test_case=relationship("TEST_CASES")

class Test_Suites(Base):
    __tablename__ = 'TEST_SUITES'
    TEST_SUITE_ID = Column(Integer, primary_key=True)
    TEST_SUITE_NAME = Column(String)
    CREATED_BY = Column(String)
    # test_case = relationship("TEST_CASES")

class Test_Cases(Base):
    __tablename__ = 'TEST_CASES'
    TEST_SUITE_ID = Column(Integer, ForeignKey('TEST_SUITES.TEST_SUITE_ID'))
    TEST_CASE_ID = Column(Integer, primary_key=True)
    TEST_CASE_ADO_ID = Column(Integer)
    TEST_CASE_NAME = Column(String)
    STATUS = Column(String)
    DURATION_SEC = Column(Integer)
    EXECUTED_BY = Column(String, ForeignKey('User.username'))
    # test_step = relationship("TEST_STEPS")

class Test_Steps(Base):
    __tablename__ = 'TEST_STEPS'
    TEST_CASE_ID = Column(Integer, ForeignKey('TEST_CASES.TEST_CASE_ID'), primary_key=True)
    STEP_NUMBER = Column(Integer)
    DESCRIPTION = Column(String)
    EXPECTED_RESULT = Column(String)
    STEP_STATUS = Column(String)
    COMMENT = Column(String)

# Uncomment to create a new DB tables
# metadata = MetaData()
# Base.metadata.create_all(engine)
