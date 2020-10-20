from flask import Blueprint, Flask, request, render_template, redirect, url_for
from .utils.api import ado_api
from flask_login import login_required, current_user
from loguru import logger
from .models_data import create_table

main = Blueprint('main', __name__)
create_table()


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
                           users_dict=ado_api.get_all_users())


@main.route('/about', methods=['GET', 'POST'])
def about_page():
    if current_user.is_authenticated:
        return render_template("about.html", username=ado_api.get_current_user())
    else:
        return render_template("about_not_auth.html")


@main.route('/')
def redirect_from_main():
    return redirect(url_for('main.test_suites'))


@main.route('/save_test_result', methods=['POST'])
def save_test_result():
    data = request.get_json()
    print(data)
    return ("200")


# @main.route('/run')
@main.route('/run/<test_suite_id>/<test_case_id>')
def test_run(test_suite_id, test_case_id):
    ado_api.get_test_case_steps_by_id(1,16)
    return render_template("run.html", test_case_name='TEST_CASE_NAME')
