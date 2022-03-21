from datetime import datetime
from functools import wraps
from flask import current_app, request, Response
from flask.cli import AppGroup
from flask_sqlalchemy import SQLAlchemy
from werkzeug.wrappers.response import Response as WZResponse


class ViewCounter():
    _vc_cli = AppGroup('vc')
    TABLENAME = "vc_requests"

    def __init__(self, app=None, db=None):
        self.app = app
        self.db = db
        self.requests = None
        if app is not None:
            self.init_app(app, db)

    def init_app(self, app, db):
        db_default = app.config.get(
            'SQLALCHEMY_DATABASE_URI',
            'sqlite:///:memory:'
            )
        app.config.setdefault('VIEWCOUNT_DB', db_default)
        app.cli.add_command(ViewCounter._vc_cli)
        self.requests = ViewCounter.init_table(app, db)

    @staticmethod
    def init_table(app, db):
        meta = db.MetaData()
        requests = db.Table(
            ViewCounter.TABLENAME, meta,
            db.Column('id', db.Integer, primary_key=True),
            db.Column('year', db.Integer, nullable=False),
            db.Column('month', db.Integer, nullable=False),
            db.Column('day', db.Integer, nullable=False),
            db.Column('hour', db.Integer, nullable=False),
            db.Column('minute', db.Integer, nullable=False),
            db.Column('ip', db.String(64), nullable=False),
            db.Column('user_agent', db.String(200), nullable=False),
            db.Column('path', db.String(250), nullable=False),
            db.Column('status', db.Integer, nullable=False),
            db.Column('args', db.String(200), nullable=True),
        )
        meta.create_all(db.engine)
        return requests

    @staticmethod
    def check_status(response):
        if isinstance(response, str):
            return 200
        elif isinstance(response, tuple):
            if len(response) == 3:
                return response[1]
            elif len(response) == 2:
                if isinstance(response[1], int):
                    return response[1]
                elif isinstance(response[1], dict):
                    return 200
        elif issubclass(response.__class__, (Response, WZResponse)):
            return response.status_code

    def add_view(self, dt, ip, user_agent, path, status, params):
        ins = self.requests.insert().values(
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=dt.hour,
            minute=dt.minute,
            ip=ip,
            user_agent=user_agent[:180],
            path=path,
            status=status,
            args=params[:180])
        self.db.session.execute(ins)
        self.db.session.commit()

    def count(self, f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            dt = datetime.now()
            ip = request.access_route[0]
            user_agent = request.user_agent.string
            try:
                path, params = request.full_path.split('?')
            except ValueError:
                path = request.path
                params = None

            res = f(*args, **kwargs)
            status = self.check_status(res)
            self.add_view(dt, ip, user_agent, path, status, params)
            return res
        return decorated_function

    @_vc_cli.command('init')
    def init_view_counter(self):
        """Proxy to the table init"""
        db = SQLAlchemy(current_app)
        ViewCounter.init_table(current_app, db)
