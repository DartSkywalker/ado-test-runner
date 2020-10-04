from flask import Flask, request, render_template, redirect, url_for
from utils.api import ado_api

app = Flask(__name__)

@app.route('/suites', methods=['GET'])
def test_suites():
    return render_template('index.html', test_suite_list=ado_api.get_test_suites_from_database())

@app.route('/suites', methods=['POST'])
def add_test_suite():
    if request.form["selectSuite"] == "selectSuite":
        if request.method == 'POST':
            return redirect(url_for('test_cases_list', test_suite_name=request.form.get('test_suites')))
    query_id = request.form['query_id']
    print(query_id)
    ado_api.create_new_test_suite_in_db(str(query_id))
    return redirect(url_for('test_suites'))

@app.route('/cases', methods=['GET', 'POST'])
def test_cases_list():
    test_suite_name = request.args.get('test_suite_name')
    test_cases_list = ado_api.get_test_cases_from_db_by_suite_name(test_suite_name)
    return render_template('test_cases_list.html', test_suite_name=test_suite_name, test_cases_list=test_cases_list)