from flask import Blueprint, Flask, request, render_template, redirect, url_for, flash, send_file, g, session, current_app, stream_with_context

from .utils.api import sql_api
from .utils.api import async_functions
from .utils.api import ado_api
from flask_login import login_required, current_user
from loguru import logger
from .main_db_models import create_table
from . import *
from io import StringIO
import json
from flask import current_app as app
from .utils.utils import get_invites_table, generate_invite_codes, get_user_role, get_users_dict, set_new_user_role, change_password_for_user
from .utils.constants import USER_ROLES
from werkzeug.wrappers import Response
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy import create_engine, MetaData, Table, select, desc, and_, join


main = Blueprint('main', __name__, static_folder="static", static_url_path="")
create_table()

postgres_main = 'postgresql+psycopg2://user:user@localhost:5432/maindb'

# def sql_connection_team(db_name):
#     logger.critical(db_name)
#     engine = create_engine('postgresql+psycopg2://user:user@localhost:5432/'+db_name+'_db', echo=False, pool_recycle=2)
#     connection = engine.connect()
#     meta = MetaData()
#     meta.reflect(bind=engine)
#     return connection, meta

class TeamDbConnector:
    def __init__(self, db_name):
        self.db_name = db_name
        self.team_db_address = 'postgresql+psycopg2://user:user@localhost:5432/'+db_name+'_db'


    def create_connection(self):
        logger.warning(f"Connecting to {self.db_name} database")
        self.engine = create_engine(self.team_db_address, echo=False,
                               pool_recycle=2)
        self.connection = self.engine.connect()
        self.meta = MetaData()
        self.meta.reflect(bind=self.engine)
        return self.connection, self.meta


    def close_connection(self):
        self.connection.close()
        self.engine.dispose()


@main.errorhandler(404)
def invalid_route(e):
    return render_template("error404.html")


@main.route('/<team_name>/save_user/<suite_id>/<test_case_id>', methods=['POST'])
@login_required
def set_user_for_test_case(team_name, suite_id, test_case_id):
    try:
        data = request.get_json()
        logger.warning(data)
        tbc = TeamDbConnector(team_name)
        connection, meta = tbc.create_connection()
        sql_api.set_test_case_for_user(suite_id, test_case_id, data, connection, meta)
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    except:
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}


@main.route('/<team_name>/suites', methods=['GET'])
@login_required
def test_suites(team_name):
    tbc = TeamDbConnector(team_name)
    connection, meta = tbc.create_connection()
    test_suite_dict = sql_api.get_test_suites_from_database(connection, meta)
    tbc.close_connection()
    username = sql_api.get_current_user()
    return render_template('index.html', test_suite_dict=test_suite_dict,
                           username=username)


@main.route('/<team_name>/suites', methods=['POST'])
@login_required
def add_test_suite(team_name):
    if request.form["btn"] == "selectSuite":
        if request.method == 'POST':
            return redirect('/'+team_name+'/cases/' + request.form.get('test_suites'))
            # return redirect(url_for('main.test_cases_list', test_suite_name=request.form.get('test_suites')))

    query_id = request.form['query_id']
    if query_id == "":
        flash('Please, enter a valid Query ID')
        return redirect(url_for('main.test_suites', team_name=team_name))
    if ado_api.check_access_to_ado_query(query_id):
        tbc = TeamDbConnector(team_name)
        connection_t, meta_t = tbc.create_connection()
        async_functions.create_new_test_suite_in_db(str(query_id), connection_t, meta_t)
        tbc.close_connection()
        return redirect(url_for('main.test_suites', team_name=team_name))
    else:
        flash('Access denied. Please check your ADO Token')
        return redirect(url_for('main.test_suites', team_name=team_name))


@main.route('/<team_name>/cases/<suite_id>', methods=['GET', 'POST'])
@login_required
def test_cases_list(team_name, suite_id):
    tbc = TeamDbConnector(team_name)
    connection_t, meta_t = tbc.create_connection()
    test_cases_dict = sql_api.get_test_cases_from_db_by_suite_name(suite_id, connection_t, meta_t)
    test_suite_name = sql_api.get_test_suite_name_by_id(suite_id, connection_t, meta_t)
    tbc.close_connection()
    return render_template('test_cases_list.html', test_suite_name=test_suite_name, test_cases_dict=test_cases_dict,
                           username=sql_api.get_current_user(),
                           users_dict=sql_api.get_all_users(),
                           test_suite_id=suite_id)


@main.route('/<team_name>/cases/<suite_id>/<test_case_ado_id>', methods=['GET', 'POST'])
@login_required
def redirect_from_suite_to_run(team_name, suite_id, test_case_ado_id):
    tbc = TeamDbConnector(team_name)
    connection_t, meta_t = tbc.create_connection()
    test_case_id = sql_api.get_test_case_id_by_ado_id(suite_id, test_case_ado_id, connection_t, meta_t)
    tbc.close_connection()
    return redirect(url_for('main.test_run', test_suite_id=suite_id, test_case_id=test_case_id, team_name=team_name))


@main.route('/<team_name>/about', methods=['GET', 'POST'])
def about_page(team_name):
    if current_user.is_authenticated:
        return render_template("about.html", username=sql_api.get_current_user())
    else:
        return render_template("about_not_auth.html")


@main.route('/')
@login_required
def redirect_from_main():
    return redirect(url_for('main.test_suites', team_name=sql_api.get_current_user_team()))


@main.route('/<team_name>/settings', methods=['GET', 'POST'])
@login_required
def user_settings(team_name):
    if request.method == 'POST':
        data = request.get_json()
        if (len(data['token']) < 50):
            return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}
        else:
            if sql_api.update_user_token(data['token']) != 'failed':
                return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    return render_template('settings.html', username=sql_api.get_current_user(), team=sql_api.get_current_user_team())


@main.route('/<team_name>/save_test_result/<test_case_id>', methods=['POST'])
@login_required
def save_test_result(team_name, test_case_id):
    data = request.get_json()
    # logger.warning(data)
    # try:
    if data['testResult']['is_changed'] == 'False':
        # if True:
        tbc = TeamDbConnector(team_name)
        connection_t, meta_t = tbc.create_connection()
        sql_api.set_test_case_state(test_case_id, data, connection_t, meta_t)
        tbc.close_connection()
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:
        tbc = TeamDbConnector(team_name)
        connection_t, meta_t = tbc.create_connection()
        ado_response = ado_api.update_test_steps_in_ado(test_case_id, data, connection_t, meta_t)
        if ado_response == '200':
            sql_api.update_test_steps_sql(test_case_id, data, connection_t, meta_t)
            tbc.close_connection()
            return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
        else:
            tbc.close_connection()
            return json.dumps({'success': False}), 200, {ado_response}
    # except Exception as e:
    #     logger.error(e)
    #     return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}


@main.route('/<team_name>/run/<test_suite_id>/<test_case_id>')
@login_required
def test_run(team_name, test_suite_id, test_case_id):
    tbc = TeamDbConnector(team_name)
    connection_t, meta_t = tbc.create_connection()
    steps_data_list = sql_api.get_test_case_steps_by_id(test_case_id, connection_t, meta_t)
    test_case_name = sql_api.get_test_case_name_by_id(test_case_id, connection_t, meta_t)
    tbc.close_connection()
    return render_template("run.html", test_case_name=test_case_name, steps_data_list=steps_data_list)


@main.route('/<team_name>/cases/<suite_id>/<test_case_ado_id>/stat', methods=['GET', 'POST'])
@login_required
def redirect_from_suite_to_statistics(team_name, suite_id, test_case_ado_id):
    tbc = TeamDbConnector(team_name)
    connection_t, meta_t = tbc.create_connection()
    test_case_id = sql_api.get_test_case_id_by_ado_id(suite_id, test_case_ado_id, connection_t, meta_t)
    tbc.close_connection()
    return redirect(url_for('main.test_statistics', suite_id=suite_id, test_case_id=test_case_id))


@main.route('/<team_name>/statistics/<suite_id>/<test_case_id>')
@login_required
def test_statistics(team_name, suite_id, test_case_id):
    tbc = TeamDbConnector(team_name)
    connection_t, meta_t = tbc.create_connection()
    test_case_name = sql_api.get_test_case_name_by_id(test_case_id, connection_t, meta_t)
    tbc.close_connection()
    return render_template("statistics.html", test_case_name=test_case_name)


@main.route('/<team_name>/suitify')
@login_required
def suites_list(team_name):
    tbc = TeamDbConnector(team_name)
    connection_t, meta_t = tbc.create_connection()
    suites_list = sql_api.get_list_of_suites(connection_t, meta_t)
    suite_info_dict = sql_api.get_test_suites_info(connection_t, meta_t)
    _, suite_info_dict_detailed = sql_api.get_test_case_states_for_suites(suites_list, connection_t, meta_t)
    tbc.close_connection()
    return render_template("suite_list.html", username=sql_api.get_current_user(), suite_info=suite_info_dict,
                           suite_info_detailed=suite_info_dict_detailed)


@main.route('/<team_name>/checkaccess/<test_case_id>', methods=['POST'])
@login_required
def check_access_to_ado_item(team_name, test_case_id):
    tbc = TeamDbConnector(team_name)
    connection_t, meta_t = tbc.create_connection()
    if ado_api.check_access_to_test_case_ado(test_case_id, connection_t, meta_t):
        tbc.close_connection()
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:
        tbc.close_connection()
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}


@main.route('/<team_name>/getstatistics/<test_suite_id>/<case_ado_id>', methods=['GET'])
@login_required
def get_test_case_statistics(team_name, test_suite_id, case_ado_id):
    try:
        tbc = TeamDbConnector(team_name)
        connection_t, meta_t = tbc.create_connection()
        date, duration, test_suite, tester, state, failure_details = sql_api.get_test_run_date_duration(test_suite_id, case_ado_id, connection_t, meta_t)
        tbc.close_connection()
        return json.dumps({'success': True, 'duration': duration, 'date': date, 'suite_name': test_suite,
                           'tester': tester, 'state': state, 'failure_details': failure_details}), \
               200, {'ContentType': 'application/json'}
    except Exception as e:
        logger.critical(e)
        tbc.close_connection()
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
                               user_roles_list=USER_ROLES, teams=sql_api.get_teams_data_admin())
    else:
        return redirect(url_for("main.test_suites", team=sql_api.get_current_user_team()))


@main.route('/generate_invites/<num>', methods=['GET'])
@login_required
def generate_invites(num):
    if generate_invite_codes(num):
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}

@main.route('/create_team/<team_name>', methods=['GET'])
@login_required
def create_new_team(team_name):
    if sql_api.create_new_team(team_name):
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


@main.route('/<team_name>/suitereport/<suite_id>')
@login_required
def suite_reporter(team_name, suite_id):
    tbc = TeamDbConnector(team_name)
    connection_t, meta_t = tbc.create_connection()
    suite_name, suite_data_dict = sql_api.get_suite_statistics_by_id(suite_id, connection_t, meta_t)
    tbc.close_connection()
    meta_string = (render_template('report_template.html', suite_name=suite_name, suite_data=suite_data_dict))
    return Response(meta_string,
                    mimetype="text/plain",
                       headers={"Content-Disposition":
                                    "attachment;filename=TReport.html"})


@main.route('/<team_name>/deletesuite/<suite_id>')
@login_required
def delete_test_suite(team_name, suite_id):
    tbc = TeamDbConnector(team_name)
    connection_t, meta_t = tbc.create_connection()
    if sql_api.delete_test_suite(suite_id, connection_t, meta_t):
        tbc.close_connection()
        return redirect(url_for('main.suites_list'))
    else:
        tbc.close_connection()
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}

