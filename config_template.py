import os


class Config(object):
    SECRET_KEY = '00000'
    SQL_ALCHEMY_TRACK_MODIFICATIONS = False
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
