from flask import request, url_for
from authlib.integrations.flask_client import OAuth
import os
from app import app
from app.auth import get_flow
from app.cookie import Cookie

app.secret_key = 'super secret key'
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


@app.route('/')
def index():
    c = Cookie(request)
    google_creds = c.session.get('google_credentials')
    if google_creds is not None and google_creds != {}:
        spreadsheet_id = c.session.get('spreadsheet_id')
        if spreadsheet_id is None:
            spreadsheet_id = request.args.get('s')
        if spreadsheet_id is not None:
            c.session.set('spreadsheet_id', spreadsheet_id)
            github_token = c.session.get('github_token')
            if github_token is not None:
                return c.redirect('/test')
            else:
                return c.redirect(url_for('trigger_github_auth'))
        else:
            (title, message) = ('great', 'choose a sheet (?s=xxx)')
    else:
        return c.redirect(url_for('trigger_google_auth'))

    return c.render_template('index.html', title=title, message=message)


@app.route('/logout')
def kill_auth():
    c = Cookie(request)
    c.reset()
    return c.render_template(title='logged out', message='go to / to start again')


@app.route('/google_auth')
def trigger_google_auth():
    c = Cookie(request)
    flow = get_flow()
    url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')
    c.session.set('state', state)
    return c.redirect(url)


@app.route('/oauth2callback')
def process_google_auth_response():
    c = Cookie(request)
    error = request.args.get('error', None)
    if error is not None:
        return c.render_template('index.html',
                                 title="oAuth Error",
                                 message=error)
    state = c.session.get('state')
    flow = get_flow(state)
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    c.session.set('google_credentials', {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes}
    )
    c.session.delete('state')
    return c.redirect('/')


@app.route('/login')
def trigger_github_auth():
    redirect_uri = url_for('authorize', _external=True)
    return oauth.github.authorize_redirect(redirect_uri)


@app.route('/authorize')
def authorize():
    c = Cookie(request)
    token = oauth.github.authorize_access_token()
    c.session.set('github_token', token)
    return c.redirect('/test')


@app.route('/test')
def repos():
    c = Cookie(request)
    resp = oauth.github.get('/user/repos', token=c.session.get('github_token'))
    repos = resp.json()
    return c.render_template(title='choose a repo', message=repos)
