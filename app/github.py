import os

from authlib.integrations.flask_client import OAuth
from flask import url_for

from app import app

oauth = OAuth(app)
oauth.register(
    name='github',
    client_id=os.environ.get('GITHUB_CLIENT_ID'),
    client_secret=os.environ.get('GITHUB_CLIENT_SECRET'),
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)


def get_auth_url():
    redirect_uri = url_for('process_github_auth_response', _external=True)
    return oauth.github.authorize_redirect(redirect_uri)


def complete_auth(cookie):
    token = oauth.github.authorize_access_token()
    cookie.session.set('github_credentials', token)
    return


def get_all_repos(cookie):
    resp = oauth.github.get(
        '/user/repos?sort="pushed"', token=cookie.session.get('github_credentials'))
    return resp.json()
