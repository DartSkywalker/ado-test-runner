from flask import Flask, request, render_template, redirect, url_for
from utils.api import ado_api

app = Flask(__name__)

@app.route('/suites', methods=['GET'])
def test_suites():
    return render_template('suites.html', test_suite_list=ado_api.get_test_suites_from_database())

@app.route('/suites', methods=['POST'])
def add_test_suite():
    query_id = request.form['query_id']
    print(query_id)
    ado_api.create_new_test_suite_in_db(str(query_id))
    return redirect(url_for('test_suites'))

