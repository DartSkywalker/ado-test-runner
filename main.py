from flask import Blueprint, Flask, request, render_template, redirect, url_for
from .utils.api import ado_api
from flask_login import login_required, current_user


main = Blueprint('main', __name__)

@main.route('/suites', methods=['GET'])
@login_required
def test_suites():
    return render_template('index.html', test_suite_list=ado_api.get_test_suites_from_database())

@main.route('/suites', methods=['POST'])
@login_required
def add_test_suite():
    if request.form["btn"] == "selectSuite":
        if request.method == 'POST':
            return redirect(url_for('main.test_cases_list', test_suite_name=request.form.get('test_suites')))
    query_id = request.form['query_id']
    ado_api.create_new_test_suite_in_db(str(query_id))
    return redirect(url_for('main.test_suites'))

@main.route('/cases', methods=['GET', 'POST'])
@login_required
def test_cases_list():
    test_suite_name = request.args.get('test_suite_name')
    test_cases_list = ado_api.get_test_cases_from_db_by_suite_name(test_suite_name)
    return render_template('test_cases_list.html', test_suite_name=test_suite_name, test_cases_list=test_cases_list)
