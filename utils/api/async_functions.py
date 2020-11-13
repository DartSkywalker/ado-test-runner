import asyncio

import aiohttp
from aiohttp import ClientSession
from flask import g
from flask_login import current_user
from loguru import logger
from sqlalchemy import select

from . import ado_parser
from .ado_api import get_test_cases_urls_by_query_id, get_query_name_by_query_id, connection
from .sql_api import table_user, table_suites, table_cases, table_steps, get_current_user
from utils.constants import HEADERS, get_ado_token_for_user


async def request_test_case_data(session, url):
    response = await session.request(method='GET', url=url, headers=HEADERS,
                                     auth=aiohttp.BasicAuth('', get_ado_token_for_user(get_current_user)))
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
    test_suite_id = test_suite_ids[len(test_suite_ids) - 1][0]
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
            test_sql_case_id = test_sql_case_ids[len(test_sql_case_ids) - 1][0]
            # print(test_sql_case_id)
            connection.execute(table_steps.insert().values(TEST_CASE_ID=int(test_sql_case_id),
                                                           STEP_NUMBER=str(step_number),
                                                           DESCRIPTION=test_steps[0],
                                                           EXPECTED_RESULT=test_steps[1]))
            step_number += 1
    logger.info(
        f"{test_suite_name} was successfully added to the database. Contains {len(test_cases_dict)} test cases.")