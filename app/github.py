import base64
import datetime
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


def complete_auth():
    return oauth.github.authorize_access_token()


#
# Getting lists and metadata for UI etc
#

def get_all_repos(credentials):
    resp = oauth.github.get(
        '/user/repos?sort="pushed"',
        token=credentials)
    return resp.json()


#
# CSV import
#

def sha_if_file_exists(credentials, repo_name, path, file_name):
    url = (f'/repos/{repo_name}/contents/'
           f'{path}{file_name}')
    resp = oauth.github.get(
        url,
        token=credentials
    ).json()
    if 'message' in resp and resp['message'] == 'Not Found':
        return False
    elif 'type' in resp and (
            resp['type'] == 'file' or resp['type'] == 'symlink'):
        return resp['sha']
    else:
        # it's a directory
        return False


def create_branch(credentials, repo_name, pr_target, branch):
    resp = oauth.github.get(
        f'repos/{repo_name}/git/refs/heads/{pr_target}',
        token=credentials,
    ).json()
    sha = resp['object']['sha']
    resp = oauth.github.post(
        f'repos/{repo_name}/git/refs',
        json={
            'sha': sha,
            'ref': f'refs/heads/{branch}',
        },
        token=credentials,
    ).json()
    return resp


def write_file(credentials, repo_name, path, file_name, branch, data, file_sha=False):
    url = (f'/repos/{repo_name}/contents/'
           f'{path}{file_name}')

    params = {
        'message': 'Automatically committed by the Laundromat',
        'content': base64.b64encode(data.encode('utf-8')).decode('utf-8'),
        'branch': branch
    }

    if file_sha is not False:
        params['sha'] = file_sha

    oauth.github.put(
        url,
        json=params,
        token=credentials,
    ).json()


def create_pr(credentials, repo_name, pr_target, branch):
    params = {
        'title': 'CSV updated',
        'head': branch,
        'base': pr_target,
        'body': 'PR automatically created by Laundromat',
    }
    resp = oauth.github.post(
        f'repos/{repo_name}/pulls',
        json=params,
        token=credentials,
    ).json()
    return resp


def send_file(credentials, config, data):
    file_sha = sha_if_file_exists(
        credentials, config['repo_name'], config['repo_path'], config['file_name'])

    branch = config['repo_branch']
    if branch == '__auto__':
        branch = f'laundromat_{str(datetime.datetime.now().timestamp())[0:10]}'
        create_branch(credentials,
                      config['repo_name'], config['pr_target'], branch)
    write_file(credentials,
               config['repo_name'], config['repo_path'], config['file_name'], branch, data, file_sha)
    create_pr(credentials,
              config['repo_name'], config['pr_target'], branch)

    # TODO verify this is actually working before returning true

    return True
