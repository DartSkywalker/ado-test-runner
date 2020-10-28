import requests
import json
import sqlite3
from flask import g
from flask_login import current_user
from sqlite3 import Error
from loguru import logger
from . import ado_parser
from ..constants import ADO_TOKEN, QUERY_LINK, WIQL_LINK, HEADERS, DB_NAME, WORKITEM_LINK
# from utils.constants import ADO_TOKEN, QUERY_LINK, WIQL_LINK, HEADERS, DB_NAME, WORKITEM_LINK
# from utils.api import ado_parser
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import table, column, select, update, insert
from sqlalchemy import Table, MetaData, create_engine, and_


def sql_connection():
    engine = create_engine('sqlite:///db.sqlite', echo=False)
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


def get_query_name_by_query_id(query_id):
    """
    Returns query name by its id
    :param query_id:
    :return:
    """
    r_query = requests.get(QUERY_LINK + str(query_id), headers=HEADERS, auth=('', ADO_TOKEN))
    if r_query.status_code == 200:
        r_query.close()
        parsed_data = json.loads(str(r_query.text))
        # print(query_id)
        # print(parsed_data)
        return parsed_data['name']


def get_test_cases_urls_by_query_id(query_id):
    """
    Get list of test case urls (Test Suite) by query ID
    :param query_id:
    :return:
    """
    r_query = requests.get(WIQL_LINK + str(query_id), headers=HEADERS, auth=('', ADO_TOKEN))
    if r_query.status_code == 200:
        r_query.close()
        parsed_data = json.loads(str(r_query.text))
        test_case_urls_list = [test_case['url'] for test_case in parsed_data['workItems']]
        test_cases_ids_list = [test_case['id'] for test_case in parsed_data['workItems']]
        return dict(zip(test_cases_ids_list, test_case_urls_list))
    else:
        logger.critical(f"ADO returns status code {str(r_query.status_code)}. Check your ADO_TOKEN.")


def get_test_case_name(tc_id):
    r_query = requests.get(WORKITEM_LINK + str(tc_id), headers=HEADERS, auth=('', ADO_TOKEN))
    if r_query.status_code == 200:
        r_query.close()
        parsed_data = json.loads(str(r_query.text))
        test_case_name = parsed_data['fields']['System.Title']
        return str(test_case_name)
    else:
        logger.critical(f"ADO returns status code {str(r_query.status_code)}. Check your ADO_TOKEN.")


def get_test_case_steps_by_url(test_case_url):
    """
    Get list of cleaned steps of the test case
    :param test_case_url:
    :return:
    """
    r_query = requests.get(test_case_url, headers=HEADERS, auth=('', ADO_TOKEN))
    if r_query.status_code == 200:
        r_query.close()
        parsed_data = json.loads(str(r_query.text))
        try:
            steps = parsed_data['fields']['Microsoft.VSTS.TCM.Steps']
        except KeyError:
            steps = "Test Case does not contain steps"
        # print(steps)
        steps_list = ado_parser.parse_html_steps(steps)
        return steps_list


# print(get_test_case_steps_by_url("https://dev.azure.com/HAL-LMKRD/d54c5f94-240d-4817-b74e-82588f96c6ba/_apis/wit/workItems/128710"))


def get_all_test_case_data(tc_id):
    """
    Get list of cleaned steps of the test case
    :param test_case_url:
    :return:
    """
    r_query = requests.get(WORKITEM_LINK + str(tc_id), headers=HEADERS, auth=('', ADO_TOKEN))
    if r_query.status_code == 200:
        r_query.close()
        parsed_data = json.loads(str(r_query.text))
        test_case_title = parsed_data['fields']['System.Title']
        try:
            steps = parsed_data['fields']['Microsoft.VSTS.TCM.Steps']
        except KeyError:
            steps = "Test Case does not contain steps"
        # print(steps)
        steps_list = ado_parser.parse_html_steps(steps)
        test_case = [test_case_title, steps_list]
        return test_case


# print(get_all_test_case_data(128597))


def create_new_test_suite_in_db(query_id):
    logger.debug(query_id)
    logger.debug(ADO_TOKEN)
    test_cases_dict, test_suite_name = get_test_cases_urls_by_query_id(query_id), get_query_name_by_query_id(query_id)
    #
    connection, meta = sql_connection()
    g.user = current_user.get_id()
    table = Table('User', meta)
    table_suites = Table('TEST_SUITES', meta)
    table_cases = Table('TEST_CASES', meta)
    test_steps = Table('TEST_STEPS', meta)
    query = select([table.columns['username']]).where(table.columns['id'] == g.user)
    user = connection.execute(query).fetchall()

    connection.execute(meta.tables['TEST_SUITES'].insert().values(TEST_SUITE_NAME=test_suite_name,
                                                                  CREATED_BY=str(user[0][0])))

    test_suite_ids = connection.execute(select([table_suites.columns['TEST_SUITE_ID']])
        .where(
        table_suites.columns['TEST_SUITE_NAME'] == str(test_suite_name))).fetchall()
    test_suite_id = test_suite_ids[len(test_suite_ids)-1][0]
    for id, url in test_cases_dict.items():
        logger.debug(str(id), url, test_suite_name)
        test_case = get_all_test_case_data(str(id))
        test_case_name = test_case[0]
        step_number = 1

        connection.execute(meta.tables['TEST_CASES'].insert().values(TEST_SUITE_ID=str(test_suite_id),
                                                                     TEST_CASE_ADO_ID=str(id),
                                                                     TEST_CASE_NAME=str(test_case_name),
                                                                     STATUS='Ready'))
        for test_steps in test_case[1]:
            test_sql_case_ids = connection.execute(select([table_cases.columns['TEST_CASE_ID']])
                                                  .where(table_cases.columns['TEST_CASE_ADO_ID'] == id)).fetchall()
            test_sql_case_id=test_sql_case_ids[len(test_sql_case_ids)-1][0]
            # print(test_sql_case_id)
            connection.execute(meta.tables['TEST_STEPS'].insert().values(TEST_CASE_ID=int(test_sql_case_id),
                                                                         STEP_NUMBER=str(step_number),
                                                                         DESCRIPTION=test_steps[0],
                                                                         EXPECTED_RESULT=test_steps[1]))
            step_number += 1
    logger.info(
        f"{test_suite_name} was successfully added to the database. Contains {len(test_cases_dict)} test cases.")


# create_new_test_suite_in_db("1f70f015-030a-48ca-9674-4bfd123c801c")

# def get_test_suites_from_database():
#     connection, meta = sql_connection()
#     suites = Table('TEST_SUITES', meta)
#     test_suites_list_db = connection.execute(select([suites.columns['TEST_SUITE_NAME']]).distinct()).fetchall()
#     test_suites_list = [suite[0] for suite in test_suites_list_db]
#     return test_suites_list
def get_test_suites_from_database():
    """
    Return suite with its id's
    """
    connection, meta = sql_connection()
    suites = Table('TEST_SUITES', meta)
    test_suites_list_db = connection.execute(select([suites.columns['TEST_SUITE_ID'],
                                                     suites.columns['TEST_SUITE_NAME']]).distinct()).fetchall()
    test_suites_ids = [suite[0] for suite in test_suites_list_db]
    test_suite_names = [suite[1] for suite in test_suites_list_db]
    return dict(zip(test_suites_ids, test_suite_names))


def get_test_suite_name_by_id(suite_id):
    connection, meta = sql_connection()
    table_suites = Table('TEST_SUITES', meta)
    suite_name = connection.execute(select([table_suites.columns['TEST_SUITE_NAME']]).
                                    where(table_suites.columns['TEST_SUITE_ID'] == suite_id)).fetchone()[0]
    return suite_name


def get_test_cases_from_db_by_suite_name(test_suite_id):
    connection, meta = sql_connection()
    test_cases_table = Table('TEST_CASES', meta)
    table_suites = Table('TEST_SUITES', meta)
    # test_suite_id = connection.execute(select([table_suites.columns['TEST_SUITE_ID']]).
    #                                    where(table_suites.columns['TEST_SUITE_NAME'] == test_suite)).fetchone()[0]

    test_cases_list_db = connection.execute(select([test_cases_table.columns['TEST_CASE_ADO_ID'],
                                                    test_cases_table.columns['TEST_CASE_NAME'],
                                                    test_cases_table.columns['STATUS'],
                                                    test_cases_table.columns['EXECUTED_BY']])
        .where(
        test_cases_table.columns['TEST_SUITE_ID'] == test_suite_id)).fetchall()

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
    connection, meta = sql_connection()
    g.user = current_user.get_id()
    table = Table('User', meta)
    query = select([table.columns['username']]).where(table.columns['id'] == g.user)
    user = connection.execute(query).fetchall()
    return str(user[0][0])


def get_all_users():
    connection, meta = sql_connection()
    table = Table('User', meta)
    query = select([table.columns['username'], table.columns['id']])
    users = connection.execute(query).fetchall()
    user_ids_list = [ids[1] for ids in users]
    user_names_list = [ids[0] for ids in users]
    users_dict = dict(zip(user_ids_list, user_names_list))
    return users_dict


def get_test_case_steps_by_id(suite_id, case_id):
    """
    Return steps/expected results based on suite_id and case_id
    """
    connection, meta = sql_connection()
    test_cases_table = Table('TEST_CASES', meta)
    test_steps_table = Table('TEST_STEPS', meta)
    steps_expected = connection.execute(select([test_steps_table.columns['STEP_NUMBER'],
                                                test_steps_table.columns['DESCRIPTION'],
                                                test_steps_table.columns['EXPECTED_RESULT'],
                                                test_steps_table.columns['STEP_STATUS']]).distinct()
                                        .where(and_(test_cases_table.columns['TEST_SUITE_ID'] == suite_id,
                                               test_steps_table.columns['TEST_CASE_ID'] == case_id))).fetchall()
    step_num = [data[0] for data in steps_expected]
    step_description = [data[1] for data in steps_expected]
    step_expected = [data[2] for data in steps_expected]
    step_status = [data[3] for data in steps_expected]
    steps_list = [list(a) for a in zip(step_num, step_description, step_expected, step_status)]
    return steps_list

def get_test_suites_info():
    connection, meta = sql_connection()
    test_suites_table = Table('TEST_SUITES', meta)
    test_cases_table = Table('TEST_CASES', meta)
    suites_info_db = connection.execute(select([test_suites_table.columns['TEST_SUITE_ID'],
                                                test_suites_table.columns['TEST_SUITE_NAME'],
                                                test_suites_table.columns['CREATED_BY'],
                                                test_suites_table.columns['CREATED_DATE']]).distinct()).fetchall()
    suite_ids = [data[0] for data in suites_info_db]
    suite_names = [data[1] for data in suites_info_db]
    suite_created_by = [data[2] for data in suites_info_db]
    suite_created_date = [data[3] for data in suites_info_db]
    suite_cases_num = []
    suite_cases_passed = []
    suite_cases_failed = []
    suite_cases_not_executed = []

    for suite_id in suite_ids:
        num_of_cases = connection.execute(select([test_cases_table.columns['TEST_CASE_ID']])\
            .where(test_cases_table.columns['TEST_SUITE_ID'] == suite_id).count()).fetchone()[0]
        suite_cases_num.append(num_of_cases)

        num_of_passed = connection.execute(select([test_cases_table.columns['TEST_CASE_ID']])\
            .where(and_(test_cases_table.columns['TEST_SUITE_ID'] == suite_id,
                        test_cases_table.columns['STATUS'] == 'Passed')).count()).fetchone()[0]
        suite_cases_passed.append(num_of_passed)

        num_of_failed = connection.execute(select([test_cases_table.columns['TEST_CASE_ID']])\
            .where(and_(test_cases_table.columns['TEST_SUITE_ID'] == suite_id,
                        test_cases_table.columns['STATUS'] == 'Failed')).count()).fetchone()[0]
        suite_cases_failed.append(num_of_failed)

        suite_cases_not_executed.append(num_of_cases - (num_of_passed + num_of_failed))

    suite_info_dict = dict(zip(suite_ids, zip(suite_names, suite_cases_num, suite_cases_passed,
                                              suite_cases_failed, suite_cases_not_executed,
                                              suite_created_by, suite_created_date)))
    return suite_info_dict

def get_test_case_name_by_id(test_case_id):
    connection, meta = sql_connection()
    test_cases_table = Table('TEST_CASES', meta)
    test_case_name = connection.execute(select([test_cases_table.columns['TEST_CASE_NAME']]).
                                    where(test_cases_table.columns['TEST_CASE_ID'] == test_case_id)).fetchone()[0]
    return test_case_name


def set_test_case_state(test_case_id, json_with_step_states):
    connection, meta = sql_connection()
    g.user = current_user.get_id()
    table = Table('User', meta)
    table_cases = Table('TEST_CASES', meta)
    test_steps = Table('TEST_STEPS', meta)
    query = select([table.columns['username']]).where(table.columns['id'] == g.user)
    user = connection.execute(query).fetchone()[0]
    for id, statistic in json_with_step_states.items():
        if id != 'testResult':
            step_number = list(statistic.values())[0]
            step_status = list(statistic.values())[1]
            try:
                comment = list(statistic.values())[2]
            except IndexError:
                comment = ""
            update_statement = test_steps.update().where(and_
                                                     (test_steps.c.TEST_CASE_ID == int(test_case_id),
                                                      test_steps.c.STEP_NUMBER == int(step_number)))\
                                                    .values(STEP_STATUS=str(step_status), COMMENT=str(comment))
            connection.execute(update_statement)
        else:
            test_case_result = list(statistic.values())[0]
            update_statement = table_cases.update().where(table_cases.c.TEST_CASE_ID == int(test_case_id))\
                .values(STATUS=str(test_case_result), EXECUTED_BY=str(user), DURATION_SEC='666')
            connection.execute(update_statement)


# json = {'0': {'stepNum': 1,'outcome': 'Passed', 'comment':"test"},'1': {'stepNum': 2,'outcome':'Failed'},
#         '2': {'stepNum': 3,'outcome': 'Passed'},'3': {'stepNum': 4,'outcome':'Failed'},
#         '4': {'stepNum': 5,'outcome': 'Passed'},'5': {'stepNum': 6,'outcome':'Passed'},
#         '6': { 'stepNum': 7,'outcome': 'Passed'},'testResult': {'outcome': 'Failed'}}
# set_test_case_state(1,json)


def get_test_case_id_by_ado_id(suite_id, test_case_ado_id):
    connection, meta = sql_connection()
    test_cases_table = Table('TEST_CASES', meta)
    test_case_id = connection.execute(select([test_cases_table.columns['TEST_CASE_ID']])
                                      .where(and_(test_cases_table.columns['TEST_SUITE_ID'] == suite_id,
                                                  test_cases_table.columns[
                                                      'TEST_CASE_ADO_ID'] == test_case_ado_id))).fetchone()[0]
    return test_case_id

def set_test_case_for_user(suite_id, test_case_id, json_data):
    connection, meta = sql_connection()
    test_cases_table = Table('TEST_CASES', meta)
    table_users = Table('User', meta)
    username = connection.execute(select([table_users.columns['username']])\
            .where(table_users.columns['id'] == json_data['userid'])).fetchone()[0]
    logger.warning(username)
    update_statement = test_cases_table.update().where(and_
                                                 (test_cases_table.columns['TEST_SUITE_ID'] == suite_id,
                                                  test_cases_table.columns['TEST_CASE_ADO_ID'] == test_case_id)) \
        .values(EXECUTED_BY=username)
    connection.execute(update_statement)