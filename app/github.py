import base64
import datetime
import json
import os

from authlib.integrations.flask_client import OAuth
from flask import url_for

from app import app


#
# Auth
#

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


#
# Getting lists and metadata for UI etc
#

def get_all_repos(cookie):
    resp = oauth.github.get(
        '/user/repos?sort="pushed"',
        token=cookie.session.get('github_credentials'))
    return resp.json()


#
# CSV import
#

def check_if_file_exists(cookie):
    config = cookie.session.get('config')
    url = f'/repos/{config["repo_name"]}/contents/{config["repo_path"]}{config["file_name"]}'
    resp = oauth.github.get(
        url,
        token=cookie.session.get('github_credentials')).json()
    if 'message' in resp and resp['message'] == 'Not Found':
        return False
    elif 'type' in resp and (resp['type'] == 'file' or resp['type'] == 'symlink'):
        return resp['sha']
    else:
        # directory
        return False


def create_branch(cookie, config, branch):
    resp = oauth.github.get(
        f'repos/{config["repo_name"]}/git/refs/heads/{config["pr_target"]}',
        token=cookie.session.get('github_credentials'),
    ).json()
    print(resp)
    sha = resp['object']['sha']
    resp = oauth.github.post(
        f'repos/{config["repo_name"]}/git/refs',
        json={
            'sha': sha,
            'ref': f'refs/heads/{branch}',
        },
        token=cookie.session.get('github_credentials'),
    ).json()
    print(resp)
    return resp


def write_file(cookie, data):
    config = cookie.session.get('config')
    url = f'/repos/{config["repo_name"]}/contents/{config["repo_path"]}{config["file_name"]}'
    file_sha = check_if_file_exists(cookie)
    branch = config['repo_branch']
    if branch == '__auto__':
        branch = f'laundromat_{str(datetime.datetime.now().timestamp())[0:10]}'
        create_branch(cookie, config, branch)

    params = {
        'message': 'Automatically committed by the Laundromat',
        'content': base64.b64encode(data.encode('utf-8')).decode('utf-8'),
        'branch': branch
    }

    if file_sha is not False:
        params['sha'] = file_sha

    resp = oauth.github.put(
        url,
        json=params,
        token=cookie.session.get('github_credentials'),
    ).json()

    return resp
