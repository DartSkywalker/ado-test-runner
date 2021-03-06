import datetime

from flask import g
from flask_login import current_user

from loguru import logger
from sqlalchemy import Table, select, and_, join

from . import ado_api
from .sql_connection import connection, meta, sql_connection, table_user, table_suites, table_cases, table_steps
from ..constants import WORKITEM_LINK


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


def get_test_cases_from_db_by_suite_id(test_suite_id):
    test_cases_list_db = connection.execute(select([table_cases.c.TEST_CASE_ADO_ID,
                                                    table_cases.c.TEST_CASE_NAME,
                                                    table_cases.c.STATUS,
                                                    table_cases.c.EXECUTED_BY,
                                                    table_cases.c.TEST_CASE_ID])
        .order_by((table_cases.c.TEST_CASE_ID)).where(
        table_cases.c.TEST_SUITE_ID == test_suite_id)).fetchall()
    test_cases_id_list = [test_case[4] for test_case in test_cases_list_db]
    test_cases_ado_id_list = [test_case[0] for test_case in test_cases_list_db]
    test_cases_name_list = [test_case[1] for test_case in test_cases_list_db]
    test_cases_status = [test_case[2] for test_case in test_cases_list_db]
    test_cases_executed = [test_case[3] for test_case in test_cases_list_db]
    test_cases_link_list = ["https://dev.azure.com/HAL-LMKRD/RESDEV/_workitems/edit/" + str(tc_id) for tc_id in
                            test_cases_ado_id_list]

    test_case_dict = dict(zip(test_cases_id_list, zip(test_cases_name_list, test_cases_link_list,
                                                      test_cases_status, test_cases_executed, test_cases_ado_id_list)))
    return test_case_dict


# print(len(get_test_cases_from_db_by_suite_id(31)))

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
    try:
        query = select([table_cases.c.TEST_CASE_ID]).where(and_(table_cases.c.TEST_SUITE_ID == suite_id,
                                                                table_cases.c.TEST_CASE_ADO_ID == test_case_ado_id))
        test_case_id = connection.execute(query).fetchone()[0]
        return test_case_id
    except Exception as e:
        logger.critical("Test case: %s was not found in suite: %s" % (test_case_ado_id, suite_id))
        logger.critical(e)
        return False


def get_test_case_ado_id_by_id(test_case_id):
    try:
        query = select([table_cases.c.TEST_CASE_ADO_ID]).where(table_cases.c.TEST_CASE_ID == test_case_id)
        test_case_id = connection.execute(query).fetchone()[0]
        return test_case_id
    except Exception as e:
        logger.critical(f"Test case: {test_case_id} was not found in suite")
        logger.critical(e)
        return False


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
        [table_cases.c.CHANGE_STATE_DATE, table_cases.c.DURATION_SEC, table_suites.c.TEST_SUITE_NAME,
         table_cases.c.EXECUTED_BY, table_cases.c.STATUS, table_cases.c.TEST_CASE_ID,
         table_suites.c.TEST_SUITE_ID]).select_from(
        join(table_suites, table_cases, table_suites.c.TEST_SUITE_ID == table_cases.c.TEST_SUITE_ID))
                                   .where(table_cases.c.TEST_CASE_ADO_ID == case_ado_id)).fetchall()

    execution_date = [datetime.datetime.strptime(str(data[0]), '%Y-%m-%d %H:%M:%S.%f').strftime("%b %d %Y %H:%M:%S") for
                      data in data_list]
    duration = [str(data[1]) for data in data_list]
    test_suite = [str(data[2]) for data in data_list]
    tester = [str(data[3]) for data in data_list]
    state = [str(data[4]) for data in data_list]
    tc_id = [str(data[5]) for data in data_list]
    test_suite_id = [str(data[6]) for data in data_list]

    failure_details = []

    for i in range(0, len(state)):
        # if state[i] == 'Failed':
        step_data = connection.execute(select([table_steps.c.STEP_NUMBER, table_steps.c.DESCRIPTION,
                                               table_steps.c.EXPECTED_RESULT, table_steps.c.STEP_STATUS,
                                               table_steps.c.COMMENT]).select_from(
            join(table_cases, table_steps, table_cases.c.TEST_CASE_ID == table_steps.c.TEST_CASE_ID)).
            where(
            and_(table_steps.c.TEST_CASE_ID == tc_id[i], table_cases.c.TEST_SUITE_ID == test_suite_id[i],
                 table_steps.c.STEP_STATUS == 'Failed'))).fetchall()

        step_num = [str(data[0]) for data in step_data]
        descr = [str(data[1]) for data in step_data]
        expected = [str(data[2]) for data in step_data]
        comment = [str(data[4]) if str(data[4]) != 'None' else "" for data in step_data]

        failure_details.append([step_num, comment])
        # else:
        #     failure_details.append("")
    return execution_date, duration, test_suite, tester, state, failure_details


def get_failure_details_report(test_suite_id, case_ado_id):
    data_list = connection.execute(select(
        [table_cases.c.CHANGE_STATE_DATE, table_cases.c.DURATION_SEC, table_suites.c.TEST_SUITE_NAME,
         table_cases.c.EXECUTED_BY, table_cases.c.STATUS, table_cases.c.TEST_CASE_ID,
         table_suites.c.TEST_SUITE_ID]).select_from(
        join(table_suites, table_cases, table_suites.c.TEST_SUITE_ID == table_cases.c.TEST_SUITE_ID))
        .where(
        and_(table_cases.c.TEST_CASE_ADO_ID == case_ado_id, table_cases.c.TEST_SUITE_ID == test_suite_id))).fetchall()

    state = [str(data[4]) for data in data_list]
    tc_id = [str(data[5]) for data in data_list]
    test_suite_id = [str(data[6]) for data in data_list]

    failure_details = []

    for i in range(0, len(state)):
        # if state[i] == 'Failed':
        step_data = connection.execute(select([table_steps.c.STEP_NUMBER, table_steps.c.DESCRIPTION,
                                               table_steps.c.EXPECTED_RESULT, table_steps.c.STEP_STATUS,
                                               table_steps.c.COMMENT]).select_from(
            join(table_cases, table_steps, table_cases.c.TEST_CASE_ID == table_steps.c.TEST_CASE_ID)).
            where(
            and_(table_steps.c.TEST_CASE_ID == tc_id[i], table_cases.c.TEST_SUITE_ID == test_suite_id[i],
                 table_steps.c.STEP_STATUS == 'Failed'))).fetchall()

        step_num = [str(data[0]) for data in step_data]
        descr = [str(data[1]) for data in step_data]
        expected = [str(data[2]) for data in step_data]
        comment = [str(data[4]) if str(data[4]) != 'None' else "" for data in step_data]

        failure_details.append([step_num, descr, expected, comment])
        # else:
        #     failure_details.append("")
    return failure_details


def get_test_case_failures_statistics(test_suite_id, case_ado_id):
    data_list = connection.execute(select(
        [table_cases.c.CHANGE_STATE_DATE, table_cases.c.DURATION_SEC, table_suites.c.TEST_SUITE_NAME]).select_from(
        join(table_suites, table_cases, table_suites.c.TEST_SUITE_ID == table_cases.c.TEST_SUITE_ID))
                                   .where(table_cases.c.TEST_CASE_ADO_ID == case_ado_id)).fetchall()


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
                .values(STATUS=str(test_case_result), EXECUTED_BY=str(user), DURATION_SEC=str(test_run_duration),
                        CHANGE_STATE_DATE=datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f'))
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


def get_suite_statistics_by_id(suite_id):
    suite_name = connection.execute(select([table_suites.c.TEST_SUITE_NAME])
                                    .where(table_suites.c.TEST_SUITE_ID == suite_id)).fetchone()[0]

    test_cases_data = connection.execute(select([table_cases.c.TEST_CASE_ADO_ID, table_cases.c.TEST_CASE_NAME,
                                                 table_cases.c.STATUS, table_cases.c.EXECUTED_BY,
                                                 table_cases.c.DURATION_SEC, table_cases.c.CHANGE_STATE_DATE,
                                                 table_cases.c.TEST_CASE_ID])
                                         .order_by(table_cases.c.STATUS)
                                         .where(table_cases.c.TEST_SUITE_ID == suite_id)).fetchall()

    tc_ado_id = [str(data[0]) for data in test_cases_data]
    tc_name = [str(data[1]) for data in test_cases_data]
    tc_state = [str(data[2]) if str(data[2]) != "Ready" else "🤔  Not Executed" for data in test_cases_data]
    tc_state = [state.replace("Passed", "✅  Passed")
                    .replace("Failed", "❌  Failed")
                    .replace("Pause", "⏸  Pause")
                    .replace("Blocked", "🚫  Blocked") for state in tc_state]
    tc_executed_by = [str(data[3]) if str(data[3]) != "None" else "" for data in test_cases_data]
    tc_duration = [str(data[4]) if str(data[4]) != "None" else "" for data in test_cases_data]
    tc_changed_date = [datetime.datetime.strptime(str(data[5]), '%Y-%m-%d %H:%M:%S.%f').strftime("%b %d %Y %H:%M") for
                       data in test_cases_data]
    tc_failure_details = []
    for tc_id in tc_ado_id:
        tc_failure_details.append(get_failure_details_report(suite_id, tc_id))

    tc_db_id = [str(data[6]) for data in test_cases_data]

    suite_data_dict = dict(zip(tc_db_id,
                               zip(tc_name, tc_state, tc_executed_by, tc_duration, tc_changed_date, tc_failure_details,
                                   tc_ado_id)))
    return suite_name, suite_data_dict


def get_test_cases_with_steps_by_suite_id(suite_id):
    test_cases_list_db = connection.execute(select([table_cases.c.TEST_CASE_ID])
                                            .where(table_cases.c.TEST_SUITE_ID == suite_id)).fetchall()
    test_case_ids = [test_case[0] for test_case in test_cases_list_db]
    return test_case_ids


def delete_test_suite(suite_id):
    try:
        test_cases_ids = get_test_cases_with_steps_by_suite_id(suite_id)

        for tc_id in test_cases_ids:
            connection.execute(table_steps.delete().where(table_steps.c.TEST_CASE_ID == tc_id))

        connection.execute(table_cases.delete().where(table_cases.c.TEST_SUITE_ID == suite_id))
        connection.execute(table_suites.delete().where(table_suites.c.TEST_SUITE_ID == suite_id))
        return True
    except Exception as e:
        logger.critical(e)
        return False


def delete_test_case_from_suite(suite_id, tc_id):
    try:
        # tc_id = get_test_case_id_by_ado_id(suite_id, test_case_ado_id)
        # if tc_id == False:
        #     return False

        connection.execute(table_steps.delete().where(table_steps.c.TEST_CASE_ID == tc_id))
        connection.execute(table_cases.delete().where(table_cases.c.TEST_CASE_ID == tc_id))
        return True
    except Exception as e:
        logger.critical(e)
        return False


# delete_test_case_from_suite('2','75712')

def get_all_test_cases():
    test_cases_db = connection.execute(select([table_cases.c.TEST_CASE_ADO_ID,
                                               table_cases.c.TEST_CASE_NAME,
                                               table_cases.c.TEST_CASE_ID]).distinct()).fetchall()
    tc_ado_id = [str(data[0]) for data in test_cases_db]
    tc_name = [str(data[1]) for data in test_cases_db]
    tc_db_id = [str(data[2]) for data in test_cases_db]
    return dict(zip(tc_ado_id, zip(tc_name, tc_db_id)))


def create_suite(test_suite_name):
    try:
        g.user = current_user.get_id()
        query = select([table_user.c.username]).where(table_user.c.id == g.user)
        user = connection.execute(query).fetchall()

        connection.execute(table_suites.insert().values(TEST_SUITE_NAME=test_suite_name,
                                                        CREATED_BY=str(user[0][0])))

        test_suite_ids = connection.execute(select([table_suites.c.TEST_SUITE_ID])
            .where(
            table_suites.c.TEST_SUITE_NAME == str(test_suite_name))).fetchall()
        test_suite_id = test_suite_ids[len(test_suite_ids) - 1][0]
        print(test_suite_id)
        return test_suite_id
    except Exception as e:
        logger.critical(e)
        return False


# create_suite("source_suite")


def add_test_case_to_the_suite(test_suite_id, test_case_id):
    try:
        test_suite_name = get_test_suite_name_by_id(test_suite_id)
        test_case_ado_id = get_test_case_ado_id_by_id(test_case_id)
        test_case_name = get_test_case_name_by_id(test_case_id)
        test_case_steps = get_test_case_steps_by_id(test_case_id)

        logger.debug("Test case: " + str(test_case_name))

        connection.execute(table_cases.insert().values(TEST_SUITE_ID=str(test_suite_id),
                                                       TEST_CASE_ADO_ID=str(test_case_ado_id),
                                                       TEST_CASE_NAME=str(test_case_name),
                                                       STATUS='Ready'))
        for test_steps in test_case_steps:
            test_sql_case_ids = connection.execute(select([table_cases.c.TEST_CASE_ID])
                .where(
                table_cases.c.TEST_CASE_ADO_ID == test_case_ado_id)).fetchall()
            test_sql_case_id = sorted(test_sql_case_ids)[len(test_sql_case_ids) - 1][0]
            # print(test_sql_case_id)
            connection.execute(table_steps.insert().values(TEST_CASE_ID=int(test_sql_case_id),
                                                           STEP_NUMBER=str(test_steps[0]),
                                                           DESCRIPTION=test_steps[1],
                                                           EXPECTED_RESULT=test_steps[2]))
        logger.info(f"'{test_case_name}' was successfully added to the test suite '{test_suite_name}'")
        return True
    except Exception as e:
        logger.critical(e)
        return False


# add_test_case_to_the_suite(31,202)


def copy_test_cases_from_existing_suite(source_suite_id, target_suite_id):
    try:
        list_of_test_cases = get_test_cases_from_db_by_suite_id(source_suite_id)
        for test_case in list_of_test_cases:
            add_test_case_to_the_suite(target_suite_id, test_case)
        return True
    except Exception as e:
        logger.critical(e)
        return False
# copy_test_cases_from_existing_suite(23,35)


def update_test_case_to_the_latest_revision(test_case_id):
    try:
        test_case_ado_id = get_test_case_ado_id_by_id(test_case_id)
        url = WORKITEM_LINK + str(test_case_ado_id)
        test_case_name = ado_api.get_test_case_name(test_case_ado_id)

        if test_case_name is None:
            return False

        test_case_steps_list = ado_api.get_test_case_steps_by_url(url)

        suite_id = connection.execute(select([table_cases.c.TEST_SUITE_ID]).
                                      where(table_cases.c.TEST_CASE_ID == test_case_id)).fetchone()[0]

        delete_test_case_from_suite(suite_id, test_case_id)

        connection.execute(table_cases.insert().values(TEST_SUITE_ID=str(suite_id),
                                                       TEST_CASE_ADO_ID=str(test_case_ado_id),
                                                       TEST_CASE_NAME=str(test_case_name),
                                                       STATUS='Ready'))

        step_number = 1

        for test_steps in test_case_steps_list:
            test_sql_case_ids = connection.execute(select([table_cases.c.TEST_CASE_ID])
                                                   .where(
                table_cases.c.TEST_CASE_ADO_ID == test_case_ado_id)).fetchall()
            test_sql_case_id = sorted(test_sql_case_ids)[len(test_sql_case_ids) - 1][0]
            connection.execute(table_steps.insert().values(TEST_CASE_ID=int(test_sql_case_id),
                                                           STEP_NUMBER=str(step_number),
                                                           DESCRIPTION=test_steps[0],
                                                           EXPECTED_RESULT=test_steps[1]))
            step_number += 1

        return True
    except Exception as e:
        logger.critical(e)
        return False
# update_test_case_to_the_latest_revision(682)


def add_step_to_existing_test_case(test_case_id, step_number, description, expected_result):
    try:
        test_case_steps_list = get_test_case_steps_by_id(test_case_id)

        if step_number <= len(test_case_steps_list) + 1 and len(test_case_steps_list) > 0:
            test_case_steps_list.insert(step_number - 1, [step_number, description, expected_result])
        elif len(test_case_steps_list) == 0:
            test_case_steps_list = [[step_number, description, expected_result]]
        else:
            logger.critical("Step Number is incorrect")
            raise Exception

        connection.execute(table_steps.delete().where(table_steps.c.TEST_CASE_ID == test_case_id))

        step_number = 1

        for test_steps in test_case_steps_list:
            connection.execute(table_steps.insert().values(TEST_CASE_ID=int(test_case_id),
                                                           STEP_NUMBER=str(step_number),
                                                           DESCRIPTION=test_steps[1],
                                                           EXPECTED_RESULT=test_steps[2]))
            step_number += 1
        return True
    except Exception as e:
        logger.critical(e)
        return False
# add_step_to_existing_test_case(683, 3, "middle insert", "test Expected")


def delete_test_step(test_case_id, step_number):
    try:
        test_case_steps_list = get_test_case_steps_by_id(test_case_id)

        if step_number > len(test_case_steps_list):
            logger.critical("Step Number is incorrect")
            raise Exception

        test_case_steps_list.pop(step_number-1)

        connection.execute(table_steps.delete().where(table_steps.c.TEST_CASE_ID == test_case_id))

        step_number = 1

        for test_steps in test_case_steps_list:
            connection.execute(table_steps.insert().values(TEST_CASE_ID=int(test_case_id),
                                                           STEP_NUMBER=str(step_number),
                                                           DESCRIPTION=test_steps[1],
                                                           EXPECTED_RESULT=test_steps[2]))
            step_number += 1
        return True

    except Exception as e:
        logger.critical(e)
        return False
# print(delete_test_step(1373, 1))

def update_test_step(tc_id, step_num, step_descr, step_expected):
    try:
        update_statement = table_steps.update().where(and_
                                                      (table_steps.c.TEST_CASE_ID == tc_id,
                                                       table_steps.c.STEP_NUMBER == step_num)) \
            .values(DESCRIPTION=step_descr, EXPECTED_RESULT=step_expected)
        connection.execute(update_statement)
        return True
    except Exception as e:
        logger.critical(e)
        return False