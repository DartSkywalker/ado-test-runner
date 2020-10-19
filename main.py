from flask import Blueprint, Flask, request, render_template, redirect, url_for
from .utils.api import ado_api
from flask_login import login_required, current_user
from loguru import logger
import models_data

main = Blueprint('main', __name__)
models_data.create_table()

@main.route('/suites', methods=['GET'])
@login_required
def test_suites():
    return render_template('index.html', test_suite_list=ado_api.get_test_suites_from_database(), username=ado_api.get_current_user())

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
    test_cases_dict = ado_api.get_test_cases_from_db_by_suite_name(test_suite_name)
    return render_template('test_cases_list.html', test_suite_name=test_suite_name, test_cases_dict=test_cases_dict, username=ado_api.get_current_user(),
                           users_dict=ado_api.get_all_users())

@main.route('/about', methods=['GET', 'POST'])
def about_page():
    if current_user.is_authenticated:
         return render_template("about.html", username=ado_api.get_current_user())
    else:
         return render_template("about_not_auth.html")
