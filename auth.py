from flask import Blueprint, render_template, redirect, url_for, request, flash, session, g, current_app
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from .models import user
from flask_login import login_user, logout_user, login_required, current_user
from loguru import logger
from .utils import utils
from .utils.api import sql_api
import json

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    if current_user.is_authenticated == True:
        return redirect(url_for('main.test_suites'))
    return render_template('registration.html', teams=sql_api.get_teams_list())

@auth.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    user_inst = user.query.filter_by(username=username).first()


    if not user_inst or not check_password_hash(user_inst.password, password):
        flash('Invalid credentials. Check you input and try again.')
        return redirect(url_for('auth.login'))

    login_user(user_inst)

    g.team_name = "GEOPH"

    # if the above check passes, then we know the user has the right credentials
    return redirect(url_for('main.test_suites', team_name=sql_api.get_current_user_team_db()))

@auth.route('/signup')
def signup():
    if current_user.is_authenticated == True:
        return redirect(url_for('main.test_suites'))
    return render_template('registration.html', sign_up_mode="true", teams=sql_api.get_teams_list())

@auth.route('/signup', methods=['POST'])
def signup_post():
    data = request.get_json()
    username = data['username']
    password = data['password']
    invite = data['invite']
    team_id = data['team']
    token = data['token']

    logger.warning(data)
    if not utils.validate_invite(invite):
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}
    else:
        new_user = user(username=username, password=generate_password_hash(password, method='sha256'), token=token,
                        role='engineer', team=team_id)

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
