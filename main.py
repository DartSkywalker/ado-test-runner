from flask import Blueprint, Flask, request, render_template, redirect, url_for
from .utils.api import ado_api
from flask_login import login_required, current_user
from loguru import logger
from .models_data import create_table
import json

main = Blueprint('main', __name__, static_folder="static", static_url_path="")
create_table()

@main.route('/save_user/<suite_id>/<test_case_id>', methods=['POST'])
@login_required
def set_user_for_test_case(suite_id, test_case_id):
    # try:
    data = request.get_json()
    logger.warning(data)
    ado_api.set_test_case_for_user(suite_id, test_case_id, data)
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    # except:
    #     return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}

@main.route('/suites', methods=['GET'])
@login_required
def test_suites():
    return render_template('index.html', test_suite_dict=ado_api.get_test_suites_from_database(),
                           username=ado_api.get_current_user())


@main.route('/suites', methods=['POST'])
@login_required
def add_test_suite():
    if request.form["btn"] == "selectSuite":
        if request.method == 'POST':
            return redirect('/cases/' + request.form.get('test_suites'))
            # return redirect(url_for('main.test_cases_list', test_suite_name=request.form.get('test_suites')))
    query_id = request.form['query_id']
    ado_api.create_new_test_suite_in_db(str(query_id))
    return redirect(url_for('main.test_suites'))


@main.route('/cases/<suite_id>', methods=['GET', 'POST'])
@login_required
def test_cases_list(suite_id):
    test_cases_dict = ado_api.get_test_cases_from_db_by_suite_name(suite_id)
    test_suite_name = ado_api.get_test_suite_name_by_id(suite_id)
    return render_template('test_cases_list.html', test_suite_name=test_suite_name, test_cases_dict=test_cases_dict,
                           username=ado_api.get_current_user(),
                           users_dict=ado_api.get_all_users(),
                           test_suite_id=suite_id)


@main.route('/cases/<suite_id>/<test_case_ado_id>', methods=['GET', 'POST'])
@login_required
def redirect_from_suite_to_run(suite_id, test_case_ado_id):
    test_case_id = ado_api.get_test_case_id_by_ado_id(suite_id, test_case_ado_id)
    return redirect(url_for('main.test_run', test_suite_id=suite_id, test_case_id=test_case_id))


@main.route('/about', methods=['GET', 'POST'])
@login_required
def about_page():
    if current_user.is_authenticated:
        return render_template("about.html", username=ado_api.get_current_user())
    else:
        return render_template("about_not_auth.html")


@main.route('/')
@login_required
def redirect_from_main():
    return redirect(url_for('main.test_suites'))

@main.route('/settings')
@login_required
def user_settings():
    return render_template('settings.html', username=ado_api.get_current_user())

@main.route('/save_test_result/<test_case_id>', methods=['POST'])
@login_required
def save_test_result(test_case_id):
    data = request.get_json()
    logger.warning(data)
    try:
        ado_api.set_test_case_state(test_case_id, data)
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    except Exception as e:
        logger.error(e)
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}

@main.route('/run/<test_suite_id>/<test_case_id>')
@login_required
def test_run(test_suite_id, test_case_id):
    steps_data_list = ado_api.get_test_case_steps_by_id(test_suite_id, test_case_id)
    test_case_name = ado_api.get_test_case_name_by_id(test_case_id)
    return render_template("run.html", test_case_name=test_case_name, steps_data_list=steps_data_list)


@main.route('/cases/<suite_id>/<test_case_ado_id>/stat', methods=['GET', 'POST'])
@login_required
def redirect_from_suite_to_statistics(suite_id, test_case_ado_id):
    test_case_id = ado_api.get_test_case_id_by_ado_id(suite_id, test_case_ado_id)
    return redirect(url_for('main.test_statistics', suite_id=suite_id, test_case_id=test_case_id))


@main.route('/statistics/<suite_id>/<test_case_id>')
@login_required
def test_statistics(suite_id, test_case_id):
    test_case_name = ado_api.get_test_case_name_by_id(test_case_id)
    return render_template("statistics.html", test_case_name=test_case_name)

@main.route('/suitify')
@login_required
def suites_list():
    suite_info_dict = ado_api.get_test_suites_info()
    return render_template("suite_list.html", username=ado_api.get_current_user(), suite_info=suite_info_dict)