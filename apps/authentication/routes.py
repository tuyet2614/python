# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from IPython.display import display, HTML
from cProfile import label
from os import sep
from cv2 import dft
from flask import render_template, redirect, request, url_for
from flask_login import (
    current_user,
    login_user,
    logout_user
)
from sqlalchemy import false

from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import Users
import csv
from apps.authentication.util import verify_pass

import pandas as pd
import pygal

data = pd.read_csv("covid.csv", sep=",")


@blueprint.route('/')
def route_default():
    return redirect(url_for('authentication_blueprint.login'))


# Login & Registration

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        username = request.form['username']
        password = request.form['password']

        # Locate user
        user = Users.query.filter_by(username=username).first()

        # Check the password
        if user and verify_pass(password, user.password):

            login_user(user)
            return redirect(url_for('authentication_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template('accounts/login.html',
                               msg='Wrong user or password',
                               form=login_form)

    if not current_user.is_authenticated:
        return render_template('accounts/login.html',
                               form=login_form)
    return redirect(url_for('home_blueprint.index'))


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username = request.form['username']
        email = request.form['email']
        role = request.form['role']
        photo = request.form['photo']

        # Check usename exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Username already registered',
                                   success=False,
                                   form=create_account_form)

        # Check email exists
        user = Users.query.filter_by(email=email).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Email already registered',
                                   success=False,
                                   form=create_account_form)

        # else we can create the user
        user = Users(**request.form)
        db.session.add(user)
        db.session.commit()

        return render_template('accounts/register.html',
                               msg='User created please <a href="/login">login</a>',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('accounts/register.html', form=create_account_form)


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login'))


@blueprint.route('/userprofile')
def userprofile():
    return render_template('accounts/userprofile.html', user=current_user)


@blueprint.route('/chart')
def charts():
    global Chart
    #data = pd.read_csv("covid.csv")
    myselect = request.args.get("selected")
    myoption = request.args.get("optioned")
    global mean_per_state 
    if myoption == "mean":
        mean_per_state = data.groupby('country')['cases'].mean()
    if myoption == "sum":
        mean_per_state = data.groupby('country')['cases'].sum()
    if myoption == "max":
        mean_per_state = data.groupby('country')['cases'].max()
    if myoption == "min":
        mean_per_state = data.groupby('country')['cases'].min()
    if myoption == "count":
        mean_per_state = data.groupby('country')['cases'].count()
    top_15_states = mean_per_state[:20]
        
    if myselect == "bar":
        #Draw the bar chart
        Chart = pygal.Bar(height=400)
        [Chart.add(x[0], x[1]) for x in top_15_states.items()]
        
    elif myselect == "pie":
        Chart = pygal.Pie(height=400)
        [Chart.add(x[0], x[1]) for x in top_15_states.items()]
    
    elif myselect == "donut":
        Chart = pygal.SolidGauge(inner_radius=0.70)
        [Chart.add(x[0], [{"value": x[1] * 100}])
         for x in top_15_states.head().iteritems()]
            
    return render_template('home/chart.html', rendered_chart=Chart.render(is_unicode=True))
    
    
    


@blueprint.route('/data', methods=['GET', 'POST'])
def getStudent():
    
    #df = pd.read_csv('advanced_python.csv', sep=';')
    if request.method == "POST":
        mysearch = request.form.get('search')
        if mysearch != "":
            result = data[data["country"] == mysearch]
            #print(studentcode)
            return render_template('home/data.html', rows=result.iterrows())
    return render_template('home/data.html', rows=data.iterrows())


# Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500
