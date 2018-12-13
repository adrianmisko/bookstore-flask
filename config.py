import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = '00000'
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/bookstore?user=oliwia&password=OLIwia8462'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

