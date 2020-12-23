import pytest

import utils.api.sql_connection
from ...utils.api import sql_api

TEST_SUITE_ID = 7
TEST_CASE_ID = 224
TEST_CASE_ADO_ID = 7029
TC_NAME = "New Model, Built/Unbuilt, In Memory, Saved to OW - session save restore"


@pytest.fixture(scope="session")
def connection():
    conn, meta = utils.api.sql_connection.sql_connection()
    return conn, meta


def test_get_test_suites_from_database(connection):
    all_test_suites = sql_api.get_test_suites_from_database()
    assert isinstance(all_test_suites, dict)
    for key, value in all_test_suites.items():
        assert isinstance(key, int)
        assert isinstance(value, str)


def test_get_test_suite_name_by_id(connection):
    assert sql_api.get_test_suite_name_by_id(TEST_SUITE_ID) == 'Design Cases'


def test_get_test_cases_from_db_by_suite_id(connection):
    test_cases_dict = sql_api.get_test_cases_from_db_by_suite_id(TEST_SUITE_ID)
    assert isinstance(test_cases_dict, dict)
    assert len(test_cases_dict) != 0
    for key, values in test_cases_dict.items():
        assert isinstance(key, int)
        assert isinstance(values[0], str)
        assert isinstance(values[1], str)
        assert isinstance(values[2], str)
        assert isinstance(values[4], int)
        assert values[3] is None or isinstance(values[3], str)


def test_get_all_users(connection):
    users = sql_api.get_all_users()
    assert isinstance(users, dict)
    for key, value in users.items():
        assert isinstance(key, int)
        assert isinstance(value, str)


def test_get_test_case_steps_by_id(connection):
    steps_list = sql_api.get_test_case_steps_by_id(TEST_CASE_ID)
    assert isinstance(steps_list, list)
    assert len(steps_list) != 0
    for step in steps_list:
        assert isinstance(step, list)
        assert isinstance(step[0], int)
        assert isinstance(step[1], str)
        assert isinstance(step[2], str)
        assert step[3] is None or isinstance(step[3], str)
        assert step[4] is None or isinstance(step[4], str)


def test_get_test_suites_info(connection):
    suites_info = sql_api.get_test_suites_info()
    assert isinstance(suites_info, dict)
    assert len(suites_info) != 0
    for key, value in suites_info.items():
        assert isinstance(key, int)
        assert isinstance(value, tuple)
        assert len(value) == 8
        assert isinstance(value[0], str)
        assert isinstance(value[1] and value[2] and
                          value[3] and value[4] and value[5], int)
        assert isinstance(value[6], str)
        assert isinstance(value[7], str)


def test_get_test_case_name_by_id(connection):
    tc_name = sql_api.get_test_case_name_by_id(TEST_CASE_ID)
    assert isinstance(tc_name, str)
    assert len(tc_name) != 0
    assert tc_name == TC_NAME


def test_get_test_case_id_by_ado_id(connection):
    tc_db_id = sql_api.get_test_case_id_by_ado_id(TEST_SUITE_ID, TEST_CASE_ADO_ID)
    assert tc_db_id == TEST_CASE_ID


def test_get_test_case_ado_id_by_id(connection):
    tc_ado_id = sql_api.get_test_case_ado_id_by_id(TEST_CASE_ID)
    assert tc_ado_id == TEST_CASE_ADO_ID


def test_get_test_case_states_for_suites(connection):
    suites_list = sql_api.get_list_of_suites()
    result, result_detailed = sql_api.get_test_case_states_for_suites(suites_list)
    assert isinstance(result, dict)
    for key, value in result.items():
        assert isinstance(key, int)
        assert isinstance(value, dict)
        for key_sub, value_sub in value.items():
            assert isinstance(key_sub, str)
            assert isinstance(value_sub, int)
    for key, value in result_detailed.items():
        assert isinstance(key, int)
        assert isinstance(value, dict)
        for key_sub, value_sub in value.items():
            assert isinstance(key_sub, str)
            assert isinstance(value_sub, list)