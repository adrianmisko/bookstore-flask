import os


class Config(object):
    SECRET_KEY = '00000'
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL'] or None    #defaults to sqlite
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
