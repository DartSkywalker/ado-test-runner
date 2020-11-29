from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import MetaData, Table

from sqlalchemy.sql import func

Base = declarative_base()

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
    EXECUTED_BY = Column(String)
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

def create_teams_table(connection, engine):
    metadata = MetaData()
    Base.metadata.create_all(engine)
    connection.close()
    engine.dispose()
