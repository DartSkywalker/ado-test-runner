import datetime
import sqlite3
from sqlite3.dbapi2 import Error

from flask import g
from flask_login import current_user

from loguru import logger
from sqlalchemy import create_engine, MetaData, Table, select, desc, and_, join
from sqlalchemy.pool import SingletonThreadPool, QueuePool
import os


my_sql = 'mysql+mysqlconnector://user:user@localhost:3306/ado'
postgres = os.environ['DATABASE_URL']


def sql_connection():
    engine = create_engine(postgres, echo=False, poolclass=QueuePool, pool_size=5, pool_recycle=2)
    connection = engine.connect()
    connection.execution_options(autocommit=True)
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


def get_test_suites_from_database():
    """
    Return suite with its id's
    """
    test_suites_list_db = connection.execute(select([table_suites.c.TEST_SUITE_ID,
                                                     table_suites.c.TEST_SUITE_NAME]).distinct()).fetchall()
    test_suites_ids = [suite[0] for suite in test_suites_list_db]
    test_suite_names = [suite[1] for suite in test_suites_list_db]
    if len(test_suites_ids) == 0 or len(test_suite_names) == 0:
        result = {"0": "empty"}
    else:
        result = dict(zip(test_suites_ids, test_suite_names))
    return result


def get_test_suite_name_by_id(suite_id):
    suite_name = connection.execute(select([table_suites.c.TEST_SUITE_NAME]).
                                    where(table_suites.c.TEST_SUITE_ID == suite_id)).fetchone()[0]
    return suite_name


def get_test_cases_from_db_by_suite_name(test_suite_id):
    test_cases_list_db = connection.execute(select([table_cases.c.TEST_CASE_ADO_ID,
                                                    table_cases.c.TEST_CASE_NAME,
                                                    table_cases.c.STATUS,
                                                    table_cases.c.EXECUTED_BY])
        .order_by(desc(table_cases.c.TEST_CASE_ID)).where(
        table_cases.c.TEST_SUITE_ID == test_suite_id)).fetchall()
    test_cases_id_list = [test_case[0] for test_case in test_cases_list_db]
    test_cases_name_list = [test_case[1] for test_case in test_cases_list_db]
    test_cases_status = [test_case[2] for test_case in test_cases_list_db]
    test_cases_executed = [test_case[3] for test_case in test_cases_list_db]
    test_cases_link_list = ["https://dev.azure.com/HAL-LMKRD/RESDEV/_workitems/edit/" + str(tc_id) for tc_id in
                            test_cases_id_list]

    test_case_dict = dict(zip(test_cases_id_list, zip(test_cases_name_list, test_cases_link_list,
                                                      test_cases_status, test_cases_executed)))
    return test_case_dict
# get_test_cases_from_db_by_suite_name('Velocity Test Cases')


def get_current_user():
    g.user = current_user.get_id()
    query = select([table_user.c.username]).where(table_user.c.id == g.user)
    user = connection.execute(query).fetchall()
    return str(user[0][0])


def get_all_users():
    query = select([table_user.c.username, table_user.c.id])
    users = connection.execute(query).fetchall()
    user_ids_list = [ids[1] for ids in users]
    user_names_list = [ids[0] for ids in users]
    users_dict = dict(zip(user_ids_list, user_names_list))
    return users_dict


def get_test_case_steps_by_id(test_case_id):
    """
    Return steps/expected results based on suite_id and case_id
    """
    steps_expected = connection.execute(select([table_steps.c.STEP_NUMBER,
                                                table_steps.c.DESCRIPTION,
                                                table_steps.c.EXPECTED_RESULT,
                                                table_steps.c.STEP_STATUS,
                                                table_steps.c.COMMENT])
                                        .order_by('STEP_NUMBER').distinct()
                                        .where(table_steps.c.TEST_CASE_ID == test_case_id)).fetchall()
    step_num = [data[0] for data in steps_expected]
    step_description = [data[1] for data in steps_expected]
    step_expected = [data[2] for data in steps_expected]
    step_status = [data[3] for data in steps_expected]
    step_comment = [data[4] for data in steps_expected]
    steps_list = [list(a) for a in zip(step_num, step_description, step_expected, step_status, step_comment)]
    return steps_list


def get_test_suites_info():
    suites_info_db = connection.execute(select([table_suites.c.TEST_SUITE_ID,
                                                table_suites.c.TEST_SUITE_NAME,
                                                table_suites.c.CREATED_BY,
                                                table_suites.c.CREATED_DATE]).distinct()).fetchall()
    suite_ids = [data[0] for data in suites_info_db]
    suite_names = [data[1] for data in suites_info_db]
    suite_created_by = [data[2] for data in suites_info_db]
    suite_created_date = [datetime.datetime.strptime(str(data[3]), '%Y-%m-%d %H:%M:%S.%f').strftime("%b %d %Y %H:%M:%S")
                          for data in suites_info_db]
    suite_cases_num = []
    suite_cases_passed = []
    suite_cases_failed = []
    suite_cases_blocked = []
    suite_cases_not_executed = []

    for suite_id in suite_ids:
        num_of_cases = connection.execute(select([table_cases.c.TEST_CASE_ID]) \
                                          .where(table_cases.c.TEST_SUITE_ID == suite_id)).fetchall()
        num_of_cases = len(num_of_cases)
        suite_cases_num.append(num_of_cases)

        num_of_passed = connection.execute(select([table_cases.c.TEST_CASE_ID]) \
                                           .where(and_(table_cases.c.TEST_SUITE_ID == suite_id,
                                                       table_cases.c.STATUS == 'Passed'))).fetchall()
        num_of_passed = len(num_of_passed)
        suite_cases_passed.append(num_of_passed)

        num_of_failed = connection.execute(select([table_cases.c.TEST_CASE_ID]) \
                                           .where(and_(table_cases.c.TEST_SUITE_ID == suite_id,
                                                       table_cases.c.STATUS == 'Failed'))).fetchall()
        num_of_failed = len(num_of_failed)

        suite_cases_failed.append(num_of_failed)

        num_of_blocked = connection.execute(select([table_cases.columns['TEST_CASE_ID']]) \
                                            .where(and_(table_cases.columns['TEST_SUITE_ID'] == suite_id,
                                                        table_cases.columns['STATUS'] == 'Blocked'))).fetchall()
        num_of_blocked = len(num_of_blocked)
        suite_cases_blocked.append(num_of_blocked)

        suite_cases_not_executed.append(num_of_cases - (num_of_passed + num_of_failed + num_of_blocked))

    suite_info_dict = dict(zip(suite_ids, zip(suite_names, suite_cases_num, suite_cases_passed,
                                              suite_cases_failed, suite_cases_blocked, suite_cases_not_executed,
                                              suite_created_by, suite_created_date)))
    return suite_info_dict


def get_test_case_name_by_id(test_case_id):
    test_case_name = connection.execute(select([table_cases.c.TEST_CASE_NAME]).
                                        where(table_cases.c.TEST_CASE_ID == test_case_id)).fetchone()[0]
    return test_case_name


def get_test_case_id_by_ado_id(suite_id, test_case_ado_id):
    test_case_id = connection.execute(select([table_cases.c.TEST_CASE_ID])
                                      .where(and_(table_cases.c.TEST_SUITE_ID == suite_id,
                                                  table_cases.c.TEST_CASE_ADO_ID == test_case_ado_id))).fetchone()[0]
    return test_case_id


def get_list_of_suites():
    suites = Table('TEST_SUITES', meta)
    test_suites_list_db = connection.execute(select([suites.columns['TEST_SUITE_ID']]).distinct()).fetchall()
    test_suites_ids = [suite[0] for suite in test_suites_list_db]
    return test_suites_ids


def get_test_case_states_for_suites(suites):
    result = {}
    result_detailed = {}
    for test_suite in suites:
        status = connection.execute(select([table_cases.c.STATUS, table_cases.c.TEST_CASE_ID,
                                            table_cases.c.TEST_CASE_ADO_ID, table_cases.c.TEST_CASE_NAME])
                                    .where(and_(table_cases.c.TEST_SUITE_ID == test_suite))).fetchall()

        list = [case[0] for case in status]
        result[test_suite] = {'Failed': list.count("Failed"),
                              'Passed': list.count("Passed"),
                              'Blocked': list.count("Blocked"),
                              'Ready': list.count("Ready"),
                              'Paused': list.count("Paused")}
        result_detailed[test_suite] = {
            'Failed': [[case[1], case[2], case[3]] for case in status if case[0] == 'Failed'],
            'Passed': [[case[1], case[2], case[3]] for case in status if case[0] == 'Passed'],
            'Blocked': [[case[1], case[2], case[3]] for case in status if case[0] == 'Blocked'],
            'Ready': [[case[1], case[2], case[3]] for case in status if case[0] == 'Ready'],
            'Paused': [[case[1], case[2], case[3]] for case in status if case[0] == 'Paused']}
    return result, result_detailed
# get_test_case_states_for_suites([2])


def get_test_run_date_duration(test_suite_id, case_ado_id):
    data_list = connection.execute(select(
        [table_cases.c.CHANGE_STATE_DATE, table_cases.c.DURATION_SEC, table_suites.c.TEST_SUITE_NAME]).select_from(
        join(table_suites, table_cases, table_suites.c.TEST_SUITE_ID == table_cases.c.TEST_SUITE_ID))
                                   .where(table_cases.c.TEST_CASE_ADO_ID == case_ado_id)).fetchall()
    execution_date = [datetime.datetime.strptime(str(data[0]), '%Y-%m-%d %H:%M:%S.%f').strftime("%b %d %Y %H:%M:%S") for
                      data in data_list]
    duration = [str(data[1]) for data in data_list]
    test_suite = [str(data[2]) for data in data_list]
    return execution_date, duration, test_suite


def set_test_case_for_user(suite_id, test_case_id, json_data):
    username = connection.execute(select([table_user.c.username]) \
                                  .where(table_user.c.id == json_data['userid'])).fetchone()[0]
    update_statement = table_cases.update().where(and_
                                                  (table_cases.c.TEST_SUITE_ID == suite_id,
                                                   table_cases.c.TEST_CASE_ADO_ID == test_case_id)) \
        .values(EXECUTED_BY=username)
    connection.execute(update_statement)


def set_test_case_state(test_case_id, json_with_step_states):
    # g.user = current_user.get_id()
    # query = select([table_user.columns['username']]).where(table_user.columns['id'] == g.user)
    user = get_current_user()
    for id, statistic in json_with_step_states.items():
        if id != 'testResult':
            step_number = list(statistic.values())[0]
            step_status = list(statistic.values())[1]
            try:
                comment = list(statistic.values())[2]
            except IndexError:
                comment = ""
            update_statement = table_steps.update().where(and_
                                                          (table_steps.c.TEST_CASE_ID == int(test_case_id),
                                                           table_steps.c.STEP_NUMBER == int(step_number))) \
                .values(STEP_STATUS=str(step_status), COMMENT=str(comment))
            connection.execute(update_statement)
        else:
            test_case_result = list(statistic.values())[0]
            test_run_duration = list(statistic.values())[1]
            update_statement = table_cases.update().where(table_cases.c.TEST_CASE_ID == int(test_case_id)) \
                .values(STATUS=str(test_case_result), EXECUTED_BY=str(user), DURATION_SEC=str(test_run_duration))
            connection.execute(update_statement)
# json = {'0': {'stepNum': 1,'outcome': 'Passed', 'comment':"test"},'1': {'stepNum': 2,'outcome':'Failed'},
#         '2': {'stepNum': 3,'outcome': 'Passed'},'3': {'stepNum': 4,'outcome':'Failed'},
#         '4': {'stepNum': 5,'outcome': 'Passed'},'5': {'stepNum': 6,'outcome':'Passed'},
#         '6': { 'stepNum': 7,'outcome': 'Passed'},'testResult': {'outcome': 'Failed'}}
# set_test_case_state(1,json)


def update_user_token(token):
    username = get_current_user()
    update_statement = table_user.update().where(table_user.c.username == username) \
        .values(token=token)
    try:
        connection.execute(update_statement)
        return 'success'
    except:
        return 'failed'


def update_test_steps_sql(test_case_id, json_with_step_states):
    user = get_current_user()
    for id, statistic in json_with_step_states.items():
        if id != 'testResult':
            step_number = list(statistic.values())[0]
            step_status = list(statistic.values())[1]
            try:
                comment = list(statistic.values())[2]
                new_action = list(statistic.values())[3]
                new_expected = list(statistic.values())[4]
            except IndexError:
                comment = ""
                new_action = ""
                new_expected = ""
            if new_action != "" and new_expected != "":
                update_statement = table_steps.update().where(and_
                                                              (table_steps.c.TEST_CASE_ID == int(test_case_id),
                                                               table_steps.c.STEP_NUMBER == int(step_number))) \
                    .values(STEP_STATUS=str(step_status), COMMENT=str(comment),
                            DESCRIPTION=str(new_action),
                            EXPECTED_RESULT=str(new_expected))
            elif new_action != "" and new_expected == "":
                update_statement = table_steps.update().where(and_
                                                              (table_steps.c.TEST_CASE_ID == int(test_case_id),
                                                               table_steps.c.STEP_NUMBER == int(step_number))) \
                    .values(STEP_STATUS=str(step_status), COMMENT=str(comment),
                            DESCRIPTION=str(new_action))
            elif new_action == "" and new_expected != "":
                update_statement = table_steps.update().where(and_
                                                              (table_steps.c.TEST_CASE_ID == int(test_case_id),
                                                               table_steps.c.STEP_NUMBER == int(step_number))) \
                    .values(STEP_STATUS=str(step_status), COMMENT=str(comment),
                            EXPECTED_RESULT=str(new_expected))
            else:
                update_statement = table_steps.update().where(and_
                                                              (table_steps.c.TEST_CASE_ID == int(test_case_id),
                                                               table_steps.c.STEP_NUMBER == int(step_number))) \
                    .values(STEP_STATUS=str(step_status), COMMENT=str(comment))
            connection.execute(update_statement)
        else:
            test_case_result = list(statistic.values())[0]
            test_run_duration = list(statistic.values())[1]
            update_statement = table_cases.update().where(table_cases.c.TEST_CASE_ID == int(test_case_id)) \
                .values(STATUS=str(test_case_result), EXECUTED_BY=str(user), DURATION_SEC=str(test_run_duration))
            connection.execute(update_statement)



