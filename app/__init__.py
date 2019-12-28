import os
from flask import Flask
from flask_bootstrap import Bootstrap

app = Flask(__name__)
bootstrap = Bootstrap(app)

app.secret_key = os.environ.get('SECRET_KEY')

from app import routes  # noqa
