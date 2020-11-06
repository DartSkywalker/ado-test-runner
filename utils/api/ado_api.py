import requests
import json
import sqlite3
from flask import g
from flask_login import current_user
from sqlite3 import Error
from loguru import logger
from . import ado_parser
from ..constants import get_ado_token_for_user, QUERY_LINK, WIQL_LINK, HEADERS, DB_NAME, WORKITEM_LINK
# from utils.api import ado_parser
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import table, column, select, update, insert
from sqlalchemy import Table, MetaData, create_engine, and_, desc, join
import datetime

import aiohttp
from aiohttp import ClientSession
import asyncio
from timeit import default_timer as timer


my_sql = 'mysql+mysqlconnector://user:user@localhost:3306/ado'
postgres = 'postgresql+psycopg2://user:user@localhost:5432/ado'

def sql_connection():
    engine = create_engine(postgres, echo=False)
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
# g.user = current_user.get_id()
table_user = Table('user', meta)
table_suites = Table('TEST_SUITES', meta)
table_cases = Table('TEST_CASES', meta)
table_steps = Table('TEST_STEPS', meta)


def get_query_name_by_query_id(query_id):
    """
    Returns query name by its id
    :param query_id:
    :return:
    """
    r_query = requests.get(QUERY_LINK + str(query_id), headers=HEADERS, auth=('', get_ado_token_for_user(get_current_user)))
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
    r_query = requests.get(WIQL_LINK + str(query_id), headers=HEADERS, auth=('', get_ado_token_for_user(get_current_user)))
    if r_query.status_code == 200:
        r_query.close()
        parsed_data = json.loads(str(r_query.text))
        test_case_urls_list = [test_case['url'] for test_case in parsed_data['workItems']]
        test_cases_ids_list = [test_case['id'] for test_case in parsed_data['workItems']]
        return dict(zip(test_cases_ids_list, test_case_urls_list))
    else:
        logger.critical(f"ADO returns status code {str(r_query.status_code)}. Check your ADO_TOKEN.")


def get_test_case_name(tc_id):
    r_query = requests.get(WORKITEM_LINK + str(tc_id), headers=HEADERS, auth=('', get_ado_token_for_user(get_current_user)))
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
    r_query = requests.get(test_case_url, headers=HEADERS, auth=('', get_ado_token_for_user(get_current_user)))
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


async def request_test_case_data(session, url):
    response = await session.request(method='GET', url=url, headers=HEADERS, auth=aiohttp.BasicAuth('', get_ado_token_for_user(get_current_user)))
    response_json = await response.json()
    return response_json


async def get_test_cases_by_suite_id(query_id):
    tc_urls = get_test_cases_urls_by_query_id(query_id)
    tc_urls = [value for key, value in tc_urls.items()]
    async with ClientSession() as session:
        result = await asyncio.gather(*[request_test_case_data(session, url) for url in tc_urls])
        return result


def get_all_test_case_data_async(query_id):
    r = asyncio.run(get_test_cases_by_suite_id(query_id))
    test_cases_dict = {}
    for test_case in r:
        id = test_case['id']
        test_case_title = test_case['fields']['System.Title']
        try:
            steps = test_case['fields']['Microsoft.VSTS.TCM.Steps']
        except KeyError:
            steps = "Test Case does not contain steps"
        steps_list = ado_parser.parse_html_steps(steps)
        test_case_data = [test_case_title, steps_list]
        test_cases_dict[id] = test_case_data
    return test_cases_dict
# print(get_all_test_case_data_async('1f70f015-030a-48ca-9674-4bfd123c801c'))


def create_new_test_suite_in_db(query_id):
    logger.debug(query_id)
    test_cases_dict, test_suite_name = get_all_test_case_data_async(query_id), get_query_name_by_query_id(query_id)
    g.user = current_user.get_id()
    query = select([table_user.c.username]).where(table_user.c.id == g.user)
    user = connection.execute(query).fetchall()
    connection.execute(table_suites.insert().values(TEST_SUITE_NAME=test_suite_name,
                                                                  CREATED_BY=str(user[0][0])))

    test_suite_ids = connection.execute(select([table_suites.c.TEST_SUITE_ID])
        .where(
        table_suites.c.TEST_SUITE_NAME == str(test_suite_name))).fetchall()
    test_suite_id = test_suite_ids[len(test_suite_ids)-1][0]
    for id, test_case_details in test_cases_dict.items():
        logger.debug("Test case: " + str(id))

        test_case = test_case_details
        test_case_name = test_case[0]
        step_number = 1

        connection.execute(table_cases.insert().values(TEST_SUITE_ID=str(test_suite_id),
                                                                     TEST_CASE_ADO_ID=str(id),
                                                                     TEST_CASE_NAME=str(test_case_name),
                                                                     STATUS='Ready'))
        for test_steps in test_case[1]:
            test_sql_case_ids = connection.execute(select([table_cases.c.TEST_CASE_ID])
                                                  .where(table_cases.c.TEST_CASE_ADO_ID == id)).fetchall()
            test_sql_case_id=test_sql_case_ids[len(test_sql_case_ids)-1][0]
            # print(test_sql_case_id)
            connection.execute(table_steps.insert().values(TEST_CASE_ID=int(test_sql_case_id),
                                                                         STEP_NUMBER=str(step_number),
                                                                         DESCRIPTION=test_steps[0],
                                                                         EXPECTED_RESULT=test_steps[1]))
            step_number += 1
    logger.info(
        f"{test_suite_name} was successfully added to the database. Contains {len(test_cases_dict)} test cases.")
# def get_all_test_case_data(tc_id):
#     """
#     Get list of cleaned steps of the test case
#     :param test_case_url:
#     :return:
#     """
#     r_query = requests.get(WORKITEM_LINK + str(tc_id), headers=HEADERS, auth=('', ADO_TOKEN))
#     if r_query.status_code == 200:
#         r_query.close()
#         parsed_data = json.loads(str(r_query.text))
#         test_case_title = parsed_data['fields']['System.Title']
#         try:
#             steps = parsed_data['fields']['Microsoft.VSTS.TCM.Steps']
#         except KeyError:
#             steps = "Test Case does not contain steps"
#         # print(steps)
#         steps_list = ado_parser.parse_html_steps(steps)
#         test_case = [test_case_title, steps_list]
#         return test_case
# print(get_all_test_case_data(128597))


# def create_new_test_suite_in_db(query_id):
#     logger.debug(query_id)
#     logger.debug(ADO_TOKEN)
#     test_cases_dict, test_suite_name = get_test_cases_urls_by_query_id(query_id), get_query_name_by_query_id(query_id)
#     g.user = current_user.get_id()
#     query = select([table_user.c.username]).where(table_user.c.id == g.user)
#     user = connection.execute(query).fetchall()
#
#     connection.execute(table_suites.insert().values(TEST_SUITE_NAME=test_suite_name,
#                                                                   CREATED_BY=str(user[0][0])))
#
#     test_suite_ids = connection.execute(select([table_suites.c.TEST_SUITE_ID])
#         .where(
#         table_suites.c.TEST_SUITE_NAME == str(test_suite_name))).fetchall()
#     test_suite_id = test_suite_ids[len(test_suite_ids)-1][0]
#     for id, url in test_cases_dict.items():
#         logger.debug(str(id), url, test_suite_name)
#         test_case = get_all_test_case_data(str(id))
#         test_case_name = test_case[0]
#         step_number = 1
#
#         connection.execute(table_cases.insert().values(TEST_SUITE_ID=str(test_suite_id),
#                                                                      TEST_CASE_ADO_ID=str(id),
#                                                                      TEST_CASE_NAME=str(test_case_name),
#                                                                      STATUS='Ready'))
#         for test_steps in test_case[1]:
#             test_sql_case_ids = connection.execute(select([table_cases.c.TEST_CASE_ID])
#                                                   .where(table_cases.c.TEST_CASE_ADO_ID == id)).fetchall()
#             test_sql_case_id=test_sql_case_ids[len(test_sql_case_ids)-1][0]
#             # print(test_sql_case_id)
#             connection.execute(table_steps.insert().values(TEST_CASE_ID=int(test_sql_case_id),
#                                                                          STEP_NUMBER=str(step_number),
#                                                                          DESCRIPTION=test_steps[0],
#                                                                          EXPECTED_RESULT=test_steps[1]))
#             step_number += 1
#     logger.info(
#         f"{test_suite_name} was successfully added to the database. Contains {len(test_cases_dict)} test cases.")


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
    test_suites_list_db = connection.execute(select([table_suites.c.TEST_SUITE_ID,
                                                     table_suites.c.TEST_SUITE_NAME]).distinct()).fetchall()
    test_suites_ids = [suite[0] for suite in test_suites_list_db]
    test_suite_names = [suite[1] for suite in test_suites_list_db]
    if len(test_suites_ids)==0 or len(test_suite_names)==0:
        result = {"0" : "empty"}
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
    query = select([table_user.columns['username']]).where(table_user.c.id == g.user)
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
        num_of_cases = connection.execute(select([table_cases.c.TEST_CASE_ID])\
            .where(table_cases.c.TEST_SUITE_ID == suite_id)).fetchall()
        num_of_cases=len(num_of_cases)
        suite_cases_num.append(num_of_cases)

        num_of_passed = connection.execute(select([table_cases.c.TEST_CASE_ID])\
            .where(and_(table_cases.c.TEST_SUITE_ID == suite_id,
                        table_cases.c.STATUS == 'Passed'))).fetchall()
        num_of_passed=len(num_of_passed)
        suite_cases_passed.append(num_of_passed)

        num_of_failed = connection.execute(select([table_cases.c.TEST_CASE_ID])\
            .where(and_(table_cases.c.TEST_SUITE_ID == suite_id,
                        table_cases.c.STATUS == 'Failed'))).fetchall()
        num_of_failed=len(num_of_failed)

        suite_cases_failed.append(num_of_failed)

        num_of_blocked = connection.execute(select([table_cases.columns['TEST_CASE_ID']])\
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


def set_test_case_state(test_case_id, json_with_step_states):
    g.user = current_user.get_id()
    query = select([table_user.columns['username']]).where(table_user.columns['id'] == g.user)
    user = connection.execute(query).fetchone()[0]
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
            update_statement = table_cases.update().where(table_cases.c.TEST_CASE_ID == int(test_case_id))\
                .values(STATUS=str(test_case_result), EXECUTED_BY=str(user), DURATION_SEC=str(test_run_duration))
            connection.execute(update_statement)
# json = {'0': {'stepNum': 1,'outcome': 'Passed', 'comment':"test"},'1': {'stepNum': 2,'outcome':'Failed'},
#         '2': {'stepNum': 3,'outcome': 'Passed'},'3': {'stepNum': 4,'outcome':'Failed'},
#         '4': {'stepNum': 5,'outcome': 'Passed'},'5': {'stepNum': 6,'outcome':'Passed'},
#         '6': { 'stepNum': 7,'outcome': 'Passed'},'testResult': {'outcome': 'Failed'}}
# set_test_case_state(1,json)


def update_test_steps_in_ado(test_case_sql_id, data):
    # Getting the list of test case steps before the changes
    test_case_steps = get_test_case_steps_by_id(test_case_sql_id)

    # Getting the ADO id of the test case
    test_case_ADO_id = connection.execute(
        select([table_cases.c.TEST_CASE_ADO_ID]).where(table_cases.c.TEST_CASE_ID == test_case_sql_id)).fetchall()
    test_case_ADO_id = test_case_ADO_id[len(test_case_ADO_id) - 1][0]

    # Converting dict of dicts to list
    test_case_steps_changes = [list(test_case.values()) for test_case in list(data.values())]

    # Create updated list of steps
    updated_test_case = []
    for step, updated_step in zip(test_case_steps, test_case_steps_changes):
        if updated_step[3] == "" and updated_step[4] == "":
            updated_test_case.append(step)
        elif updated_step[3] != "" and updated_step[4] == "":
            step[1] = updated_step[3]
            updated_test_case.append(step)
        elif updated_step[3] == "" and updated_step[4] != "":
            step[2] = updated_step[4]
            updated_test_case.append(step)
        elif updated_step[3] != "" and updated_step[4] != "":
            step[1] = updated_step[3]
            step[2] = updated_step[4]
            updated_test_case.append(step)

    # Converting the Action and Expected result to xml format supported by ADO
    result_steps_xml = ado_parser.convert_to_xml(updated_test_case)

    # Changing HEADERS to json-patch from json in constants and sending change request
    HEADERS = {'Content-type': 'application/json-patch+json'}
    json_patch = [{"op": "replace", "path": "/fields/Microsoft.VSTS.TCM.Steps", "value": result_steps_xml}]
    r_ado = requests.patch(
        "https://dev.azure.com/HAL-LMKRD/RESDEV/_apis/wit/workitems/" + str(test_case_ADO_id) + "?api-version=6.0",
        json=json_patch, headers=HEADERS, auth=('', get_ado_token_for_user(get_current_user)))

    # Check ADO server accepted changes and return error message if not
    try:
        if str(json.loads(r_ado.text)['id']) == str(test_case_ADO_id):
            result = "200"
    except:
        result = json.loads(r_ado.text)['message']
    return result
# print(update_test_steps_in_ado(2, data_example))


def update_test_steps_sql(test_case_id, json_with_step_states):
    g.user = current_user.get_id()
    query = select([table_user.columns['username']]).where(table_user.columns['id'] == g.user)
    user = connection.execute(query).fetchone()[0]
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
                                                          table_steps.c.STEP_NUMBER == int(step_number)))\
                                                        .values(STEP_STATUS=str(step_status), COMMENT=str(comment),
                                                                DESCRIPTION=str(new_action),
                                                                EXPECTED_RESULT=str(new_expected))
            elif new_action != "" and new_expected == "":
                update_statement = table_steps.update().where(and_
                                                         (table_steps.c.TEST_CASE_ID == int(test_case_id),
                                                          table_steps.c.STEP_NUMBER == int(step_number)))\
                                                        .values(STEP_STATUS=str(step_status), COMMENT=str(comment),
                                                                DESCRIPTION=str(new_action))
            elif new_action == "" and new_expected != "":
                update_statement = table_steps.update().where(and_
                                                         (table_steps.c.TEST_CASE_ID == int(test_case_id),
                                                          table_steps.c.STEP_NUMBER == int(step_number)))\
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
            update_statement = table_cases.update().where(table_cases.c.TEST_CASE_ID == int(test_case_id))\
                .values(STATUS=str(test_case_result), EXECUTED_BY=str(user), DURATION_SEC=str(test_run_duration))
            connection.execute(update_statement)

def check_access_to_test_case_ado(test_case_id):
    test_case_ado_id = connection.execute(select([table_cases.c.TEST_CASE_ADO_ID])
                                      .where(table_cases.c.TEST_CASE_ID == test_case_id)).fetchone()[0]
    r = requests.get(WORKITEM_LINK + str(test_case_ado_id), headers=HEADERS,
                           auth=('', get_ado_token_for_user(get_current_user)))
    if r.status_code == 200:
        return True
    else:
        return False


def get_test_case_id_by_ado_id(suite_id, test_case_ado_id):
    test_case_id = connection.execute(select([table_cases.c.TEST_CASE_ID])
                                      .where(and_(table_cases.c.TEST_SUITE_ID == suite_id,
                                                  table_cases.c.TEST_CASE_ADO_ID == test_case_ado_id))).fetchone()[0]
    return test_case_id


def set_test_case_for_user(suite_id, test_case_id, json_data):
    username = connection.execute(select([table_user.c.username])\
            .where(table_user.c.id == json_data['userid'])).fetchone()[0]
    update_statement = table_cases.update().where(and_
                                                 (table_cases.c.TEST_SUITE_ID == suite_id,
                                                  table_cases.c.TEST_CASE_ADO_ID == test_case_id)) \
        .values(EXECUTED_BY=username)
    connection.execute(update_statement)

def get_list_of_suites():
    connection, meta = sql_connection()
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
        result[test_suite] = {'Failed' : list.count("Failed"),
                            'Passed' : list.count("Passed"),
                            'Blocked' : list.count("Blocked"),
                            'Ready' : list.count("Ready"),
                            'Paused' : list.count("Paused")}
        result_detailed[test_suite] = {'Failed' : [[case[1], case[2], case[3]] for case in status if case[0]== 'Failed' ],
                            'Passed' : [[case[1], case[2], case[3]] for case in status if case[0]== 'Passed'],
                            'Blocked' : [[case[1], case[2], case[3]] for case in status if case[0]== 'Blocked'],
                            'Ready' : [[case[1], case[2], case[3]] for case in status if case[0]== 'Ready'],
                            'Paused' : [[case[1], case[2], case[3]] for case in status if case[0]== 'Paused']}
    return result, result_detailed
# get_test_case_states_for_suites([2])

def update_user_token(token):
    username = get_current_user()
    update_statement = table_user.update().where(table_user.c.username == username) \
        .values(token=token)
    try:
        connection.execute(update_statement)
        return 'success'
    except:
        return 'failed'


def get_test_run_date_duration(test_suite_id, case_ado_id):
    data_list = connection.execute(select([table_cases.c.CHANGE_STATE_DATE, table_cases.c.DURATION_SEC, table_suites.c.TEST_SUITE_NAME]).select_from(join(table_suites, table_cases, table_suites.c.TEST_SUITE_ID==table_cases.c.TEST_SUITE_ID))
                                   .where(table_cases.c.TEST_CASE_ADO_ID == case_ado_id)).fetchall()
    execution_date = [datetime.datetime.strptime(str(data[0]), '%Y-%m-%d %H:%M:%S.%f').strftime("%b %d %Y %H:%M:%S") for data in data_list]
    duration = [str(data[1]) for data in data_list]
    test_suite = [str(data[2]) for data in data_list]
    return execution_date, duration, test_suite

# def get_test_run_duration(test_suite_id, case_ado_id):
#     test_case_duration = connection.execute(select([table_cases.c.DURATION_SEC]).
#                                        where(and_(table_cases.c.TEST_CASE_ADO_ID == case_ado_id,
#                                                   table_cases.c.TEST_SUITE_ID == test_suite_id))).fetchone()[0]
#
#     return test_case_duration