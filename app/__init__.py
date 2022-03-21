import os
import logging
from flask import Flask
from config import Config
from flask_mail import Mail
from flask_moment import Moment
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_view_counter import ViewCounter
from logging.handlers import RotatingFileHandler

import pymysql
pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = 'login'

mail = Mail(app)

bootstrap = Bootstrap(app)
moment = Moment(app)

view_counter = ViewCounter(app, db)


log_path = os.path.join(app.config['WRITE_PATH'], 'logs')

if not os.path.exists(log_path):
    os.mkdir(log_path)

file_handler = RotatingFileHandler(
    log_path + '/olirowanxyz_app.log',
    maxBytes=10000000,
    backupCount=10

)
file_handler.setFormatter(
    logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
)

file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)

app.logger.setLevel(logging.DEBUG)

app.logger.info("STARTED project")
app.logger.info("DEBUG = " + str(app.config["DEBUG"]))
app.logger.info("DBMS  = " + str(app.config["SQLALCHEMY_DATABASE_URI"]))

from app import routes, models, errors