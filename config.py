import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):

    SERVER_NAME = os.environ.get('SERVER_NAME') or "localhost:5000"

    SECRET_KEY = os.environ.get('SECRET_KEY') or "123456"
    ENVIRONMENT_TYPE = os.environ.get('ENVIRONMENT_TYPE') or "DEBUG"

    BACKUP_PATH = os.environ.get('BACKUP_PATH') or './'
    WRITE_PATH = os.environ.get('WRITE_PATH') or './'

    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') \
        or 'sqlite:///' + os.path.join(WRITE_PATH, 'app.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    BLOG_ADMIN_USER = os.environ.get('BLOG_ADMIN_USER') or "olirowanxyz"
    BLOG_ADMIN_ID = os.environ.get('BLOG_ADMIN_ID') or 1

    MYSQL_DB_NAME = os.environ.get('MYSQL_DB_NAME')
    MYSQL_BACKUP_USER = os.environ.get('MYSQL_BACKUP_USER')
    MYSQL_BACKUP_PASS = os.environ.get('MYSQL_BACKUP_PASS')

    ADMINS = ['admin@olirowan.xyz']
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')

    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY')
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY')

    # SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE') or True
    # REMEMBER_COOKIE_SECURE = os.environ.get('REMEMBER_COOKIE_SECURE') or True
    # SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY') or True
    # REMEMBER_COOKIE_HTTPONLY = os.environ.get('REMEMBER_COOKIE_HTTPONLY') or True

    SITE_WIDTH = 800
    POSTS_PER_PAGE = 5
