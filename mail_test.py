from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from flask.ext.mail import Mail, Message
import os
from flask.ext.script import Manager

app = Flask(__name__)
manager = Manager(app)
mail = Mail(app)
# configuration


MAIL_SERVER='smtp.googlemail.com'
MAIL_PORT=465
MAIL_USE_TLS = False
MAIL_USE_SSL= True
MAIL_USERNAME = 'gj00403'
MAIL_PASSWORD = 'gaojian20'

ADMINS = ['gj00403@gmail.com']



if __name__=='__main__':
	manager.run()

