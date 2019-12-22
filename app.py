from flask import (Flask, redirect, render_template, request, url_for)
import google_auth_oauthlib.flow
from cookie import Cookie


app = Flask(__name__)


def no_spreadsheet_id():
    return ('Error', "You must set a Spreadsheet ID from Google Sheets")


def get_flow(state=None):
    args = ['/config/client_secret.json',
            ['https://www.googleapis.com/auth/spreadsheets']]
    kwargs = {}
    if state is not None:
        kwargs['state'] = state
    return google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        *args, **kwargs)


@app.route('/')
def index():
    spreadsheet_id = request.args.get('s', None)
    if spreadsheet_id is not None:
        title = 'G Suite permissions'
        message = f'Great, looking at {spreadsheet_id}'
    else:
        (title, message) = no_spreadsheet_id()

    return render_template('index.html', title=title, message=message)


@app.route('/authenticate')
def trigger_google_auth():
    c = Cookie(request)
    flow = get_flow()
    flow.redirect_uri = url_for('process_google_auth_response', _external=True)
    url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')
    c.session.save('state', state)
    return redirect(url)


@app.route('/oauth2callback')
def process_google_auth_response():
    error = request.args.get('error', None)
    if error is not None:
        return render_template('index.html',
                               title="oAuth Error",
                               message=error)
    c = Cookie(request)
    state = c.session.get('state')
    flow = get_flow(state)
    flow.redirect_uri = url_for('process_google_auth_response', _external=True)
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    c.session.save('credentials', {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes}
    )
    return render_template('index.html',
                           title="success",
                           message=credentials.token)
