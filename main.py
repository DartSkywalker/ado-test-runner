import requests
import json
import sqlite3
from sqlite3 import Error
import parser


ADO_TOKEN = ""
QUERY_ID = "abb94139-79de-4924-b2f1-73468d05fc20"
QUERY_LINK = "https://dev.azure.com/HAL-LMKRD/RESDEV/_apis/wit/queries/"
WIQL_LINK = "https://dev.azure.com/HAL-LMKRD/RESDEV/_apis/wit/wiql/"
HEADERS = {'Content-type': 'application/json'}
DB_NAME = "ado.db"

def create_db_connection(db_file):
    """
    Create a database connection to a SQLite database
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
        return conn
    except Error as e:
        print(e)

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
        print("Handle something")

def create_new_test_suite_in_db(query_id):
    test_cases_dict, test_suite_name = get_test_cases_urls_by_query_id(query_id), get_query_name_by_query_id(query_id)
    db_conn = create_db_connection(DB_NAME)
    db_cursor = db_conn.cursor()
    for id, url in test_cases_dict.items():
        print(id, url, test_suite_name)
        db_cursor.execute(f"INSERT INTO TEST_SUITES (TEST_SUITE_NAME, TEST_CASE_ID, TEST_CASE_URL) "
                          f"VALUES (?, ?, ?)", (test_suite_name, id, url))
        db_conn.commit()
    db_conn.close()

# ==========================  Parse Steps  ====================================================

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
        steps = parsed_data['fields']['Microsoft.VSTS.TCM.Steps']
        # print(steps)
        steps_list = parser.parse_html_steps(steps)
        return steps_list
print(get_test_case_steps_by_url("https://dev.azure.com/HAL-LMKRD/d54c5f94-240d-4817-b74e-82588f96c6ba/_apis/wit/workItems/7018"))
