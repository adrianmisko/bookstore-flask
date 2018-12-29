from flask import Flask
from config_template import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from elasticsearch import Elasticsearch

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
ma = Marshmallow(app)
auth = HTTPBasicAuth()
app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']])
CORS(app)

from app import routes, models

