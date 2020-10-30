from flask import Blueprint, render_template, redirect, url_for, request, flash
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from .models import user
from flask_login import login_user, logout_user, login_required, current_user
from loguru import logger


auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    if current_user.is_authenticated == True:
        return redirect(url_for('main.test_suites'))
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    user_inst = user.query.filter_by(username=username).first()
    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database

    if not user_inst or not check_password_hash(user_inst.password, password):
        flash('Invalid credentials. Check you input and try again.')
        return redirect(url_for('auth.login')) # if the user doesn't exist or password is wrong, reload the page

    login_user(user_inst)
    # if the above check passes, then we know the user has the right credentials
    return redirect(url_for('main.test_suites'))

@auth.route('/signup')
def signup():
    if current_user.is_authenticated == True:
        return redirect(url_for('main.test_suites'))
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():
    username = request.form.get('username')
    password = request.form.get('password')
    token = request.form.get('token')

    new_user = user(username=username, password=generate_password_hash(password, method='sha256'), token=token)

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
