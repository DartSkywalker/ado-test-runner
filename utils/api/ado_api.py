import requests
import json
from loguru import logger
from . import ado_parser
from .sql_api import table_cases, get_current_user, \
    get_test_case_steps_by_id, connection, meta
from ..constants import get_ado_token_for_user, QUERY_LINK, WIQL_LINK, HEADERS, WORKITEM_LINK
# from utils.api import ado_parser
from sqlalchemy.sql import select


# connection, meta = sql_connection()


def get_query_name_by_query_id(query_id):
    """
    Returns query name by its id
    :param query_id:
    :return:
    """
    r_query = requests.get(QUERY_LINK + str(query_id), headers=HEADERS,
                           auth=('', get_ado_token_for_user(get_current_user)))
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
    r_query = requests.get(WIQL_LINK + str(query_id), headers=HEADERS,
                           auth=('', get_ado_token_for_user(get_current_user)))
    if r_query.status_code == 200:
        r_query.close()
        parsed_data = json.loads(str(r_query.text))
        test_case_urls_list = [test_case['url'] for test_case in parsed_data['workItems']]
        test_cases_ids_list = [test_case['id'] for test_case in parsed_data['workItems']]
        return dict(zip(test_cases_ids_list, test_case_urls_list))
    else:
        logger.critical(f"ADO returns status code {str(r_query.status_code)}. Check your ADO_TOKEN.")


def get_test_case_name(tc_id):
    r_query = requests.get(WORKITEM_LINK + str(tc_id), headers=HEADERS,
                           auth=('', get_ado_token_for_user(get_current_user)))
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


def check_access_to_test_case_ado(test_case_id):
    test_case_ado_id = connection.execute(select([table_cases.c.TEST_CASE_ADO_ID])
                                          .where(table_cases.c.TEST_CASE_ID == test_case_id)).fetchone()[0]
    r = requests.get(WORKITEM_LINK + str(test_case_ado_id), headers=HEADERS,
                     auth=('', get_ado_token_for_user(get_current_user)))
    if r.status_code == 200:
        return True
    else:
        return False


def check_access_to_ado_query(query_id):
    r = requests.get(QUERY_LINK + str(query_id), headers=HEADERS,
                     auth=('', get_ado_token_for_user(get_current_user)))
    if r.status_code == 200:
        return True
    else:
        return False


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
    for step in test_case_steps:
        is_changed = False
        for updated_step in test_case_steps_changes[:-1]:
            if step[0] == updated_step[0]:
                is_changed = True
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
        if not is_changed:
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

