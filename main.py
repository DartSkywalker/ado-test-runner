from flask import Blueprint, Flask, request, render_template, redirect, url_for, flash, send_file

from .utils.api import sql_api
from .utils.api import async_functions
from .utils.api import ado_api
from flask_login import login_required, current_user
from loguru import logger
from .models_data import create_table
from io import StringIO
import json
from .utils.utils import get_invites_table, generate_invite_codes, get_user_role, get_users_dict, set_new_user_role, change_password_for_user
from .utils.constants import USER_ROLES
from werkzeug.wrappers import Response


main = Blueprint('main', __name__, static_folder="static", static_url_path="")
create_table()


@main.errorhandler(404)
def invalid_route(e):
    return render_template("error404.html")


@main.route('/save_user/<suite_id>/<test_case_id>', methods=['POST'])
@login_required
def set_user_for_test_case(suite_id, test_case_id):
    try:
        data = request.get_json()
        logger.warning(data)
        sql_api.set_test_case_for_user(suite_id, test_case_id, data)
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    except:
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}


@main.route('/suites', methods=['GET'])
@login_required
def test_suites():
    return render_template('index.html', test_suite_dict=sql_api.get_test_suites_from_database(),
                           username=sql_api.get_current_user())


@main.route('/suites', methods=['POST'])
@login_required
def add_test_suite():
    if request.form["btn"] == "selectSuite":
        if request.method == 'POST':
            return redirect('/cases/' + request.form.get('test_suites'))
            # return redirect(url_for('main.test_cases_list', test_suite_name=request.form.get('test_suites')))

    query_id = request.form['query_id']
    if query_id == "" or len(query_id) < 36 or len(query_id) > 36:
        flash('Please, enter a valid Query ID')
        return redirect(url_for('main.test_suites'))
    if ado_api.check_access_to_ado_query(query_id):
        async_functions.create_new_test_suite_in_db(str(query_id))
        return redirect(url_for('main.test_suites'))
    else:
        flash('Access denied. Please check your ADO Token')
        return redirect(url_for('main.test_suites'))


@main.route('/cases/<suite_id>', methods=['GET', 'POST'])
@login_required
def test_cases_list(suite_id):
    test_cases_dict = sql_api.get_test_cases_from_db_by_suite_name(suite_id)
    test_suite_name = sql_api.get_test_suite_name_by_id(suite_id)
    return render_template('test_cases_list.html', test_suite_name=test_suite_name, test_cases_dict=test_cases_dict,
                           username=sql_api.get_current_user(),
                           users_dict=sql_api.get_all_users(),
                           test_suite_id=suite_id)


@main.route('/cases/<suite_id>/<test_case_ado_id>', methods=['GET', 'POST'])
@login_required
def redirect_from_suite_to_run(suite_id, test_case_ado_id):
    test_case_id = sql_api.get_test_case_id_by_ado_id(suite_id, test_case_ado_id)
    return redirect(url_for('main.test_run', test_suite_id=suite_id, test_case_id=test_case_id))


@main.route('/about', methods=['GET', 'POST'])
def about_page():
    if current_user.is_authenticated:
        return render_template("about.html", username=sql_api.get_current_user())
    else:
        return render_template("about_not_auth.html")


@main.route('/')
@login_required
def redirect_from_main():
    return redirect(url_for('main.test_suites'))


@main.route('/settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    if request.method == 'POST':
        data = request.get_json()
        if (len(data['token']) < 50):
            return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}
        else:
            if sql_api.update_user_token(data['token']) != 'failed':
                return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    return render_template('settings.html', username=sql_api.get_current_user())


@main.route('/save_test_result/<test_case_id>', methods=['POST'])
@login_required
def save_test_result(test_case_id):
    data = request.get_json()
    # logger.warning(data)
    # try:
    if data['testResult']['is_changed'] == 'False':
        # if True:
        sql_api.set_test_case_state(test_case_id, data)
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:
        ado_response = ado_api.update_test_steps_in_ado(test_case_id, data)
        if ado_response == '200':
            sql_api.update_test_steps_sql(test_case_id, data)
            return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
        else:
            return json.dumps({'success': False}), 200, {ado_response}
    # except Exception as e:
    #     logger.error(e)
    #     return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}


@main.route('/run/<test_suite_id>/<test_case_id>')
@login_required
def test_run(test_suite_id, test_case_id):
    steps_data_list = sql_api.get_test_case_steps_by_id(test_case_id)
    test_case_name = sql_api.get_test_case_name_by_id(test_case_id)
    return render_template("run.html", test_case_name=test_case_name, steps_data_list=steps_data_list)


@main.route('/cases/<suite_id>/<test_case_ado_id>/stat', methods=['GET', 'POST'])
@login_required
def redirect_from_suite_to_statistics(suite_id, test_case_ado_id):
    test_case_id = sql_api.get_test_case_id_by_ado_id(suite_id, test_case_ado_id)
    return redirect(url_for('main.test_statistics', suite_id=suite_id, test_case_id=test_case_id))


@main.route('/statistics/<suite_id>/<test_case_id>')
@login_required
def test_statistics(suite_id, test_case_id):
    test_case_name = sql_api.get_test_case_name_by_id(test_case_id)
    return render_template("statistics.html", test_case_name=test_case_name)


@main.route('/suitify')
@login_required
def suites_list():
    suites_list = sql_api.get_list_of_suites()
    suite_info_dict = sql_api.get_test_suites_info()
    _, suite_info_dict_detailed = sql_api.get_test_case_states_for_suites(suites_list)
    return render_template("suite_list.html", username=sql_api.get_current_user(), suite_info=suite_info_dict,
                           suite_info_detailed=suite_info_dict_detailed)


@main.route('/checkaccess/<test_case_id>', methods=['POST'])
@login_required
def check_access_to_ado_item(test_case_id):
    if ado_api.check_access_to_test_case_ado(test_case_id):
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}


@main.route('/getstatistics/<test_suite_id>/<case_ado_id>', methods=['GET'])
@login_required
def get_test_case_statistics(test_suite_id, case_ado_id):
    try:
        date, duration, test_suite, tester, state, failure_details = \
            sql_api.get_test_run_date_duration(test_suite_id, case_ado_id)
        logger.warning(failure_details)
        logger.warning(state)
        return json.dumps({'success': True, 'duration': duration, 'date': date, 'suite_name': test_suite,
                           'tester': tester, 'state': state, 'failure_details': failure_details}), \
               200, {'ContentType': 'application/json'}
    except:
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}



@main.route('/creator')
@login_required
def test_case_creator():
    return render_template('test_creator.html')


@main.route('/admin')
@login_required
def admin_panel():
    if get_user_role() == 'admin':
        ids, code, activated = get_invites_table()
        users_dict = get_users_dict()
        return render_template('admin_panel.html', ids=ids, code=code, activated=activated,
                               username=sql_api.get_current_user(), usersdict=users_dict,
                               user_roles_list=USER_ROLES)
    else:
        return redirect(url_for("main.test_suites"))


@main.route('/generate_invites/<num>', methods=['GET'])
@login_required
def generate_invites(num):
    if generate_invite_codes(num):
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}


@main.route('/change_user_role/<user_id>/<new_role>', methods=['GET'])
@login_required
def change_user_role(user_id, new_role):
    if get_user_role() == 'admin':
        if set_new_user_role(user_id, new_role):
            return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
        else:
            return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}


@main.route('/changepass', methods=['POST'])
@login_required
def change_user_password():
    data = request.get_json()
    if change_password_for_user(data['newpass']):
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}


@main.route("/checkinvite/<code>", methods=['POST'])
def check_valid_invite(code):
    logger.warning(code)
    return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}


@main.route('/suitereport/<suite_id>')
@login_required
def suite_reporter(suite_id):
    suite_name, suite_data_dict = sql_api.get_suite_statistics_by_id(suite_id)
    # logger.warning(suite_data_dict)
    return render_template('report_template.html', suite_name=suite_name, suite_data=suite_data_dict, suite_id=suite_id)
    # meta_string = (render_template('report_template.html', suite_name=suite_name, suite_data=suite_data_dict))
    # return Response(meta_string,
    #                 mimetype="text/plain",
    #                    headers={"Content-Disposition":
    #                                 "attachment;filename=TReport.html"})

@main.route('/suitereport/<suite_id>/download')
@login_required
def suite_reporter_download(suite_id):
    suite_name, suite_data_dict = sql_api.get_suite_statistics_by_id(suite_id)
    # logger.warning(suite_data_dict)
    meta_string = (render_template('report_template.html', suite_name=suite_name, suite_data=suite_data_dict))
    return Response(meta_string,
                    mimetype="text/plain",
                       headers={"Content-Disposition":
                                    "attachment;filename=TReport.html"})

@main.route('/deletesuite/<suite_id>')
@login_required
def delete_test_suite(suite_id):
    if sql_api.delete_test_suite(suite_id):
        return redirect(url_for('main.suites_list'))
    else:
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}


@main.route('/delete_test_case/<suite_id>', methods=['POST'])
@login_required
def delete_test_case_from_suite(suite_id):
    data = request.get_json()
    user_role = get_user_role()
    if user_role != 'engineer':
        for tc_ado_id in data['ado_ids']:
            sql_api.delete_test_case_from_suite(suite_id, tc_ado_id)
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:
        return json.dumps({'success': True}), 500, {'ContentType': 'application/json'}


@main.route("/suite_creator")
@login_required
def suite_creator():
    tc_dict = sql_api.get_all_test_cases()
    # logger.warning(tc_dict)
    return render_template('suites_creator.html', tc_data=tc_dict, username=sql_api.get_current_user())


@main.route("/suites_cases/<suite_id>")
@login_required
def get_all_test_cases_from_test_suite(suite_id):
    pass


@main.route("/suites_manager")
@login_required
def suites_manager():
    tc_dict = sql_api.get_all_test_cases()

    # logger.warning(tc_dict)
    return render_template('suites_manager.html', all_cases_dict=tc_dict, username=sql_api.get_current_user(), test_suite_dict=sql_api.get_test_suites_from_database())


@main.route("/get_suite_cases/<suite_id>")
@login_required
def get_test_cases_by_suite_id(suite_id):
    suite_cases = sql_api.get_test_cases_from_db_by_suite_name(suite_id)
    return json.dumps({'success': True, 'suite_cases': suite_cases}), 200, {'ContentType': 'application/json'}