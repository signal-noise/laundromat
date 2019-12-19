from flask import Flask, redirect, render_template, request, url_for
import google_auth_oauthlib.flow

app = Flask(__name__)


def get_flow(state=None):
    args = ['/config/client_secret.json',
            ['https://www.googleapis.com/auth/spreadsheets']]
    kwargs = {}
    if state is not None:
        kwargs['state'] = state
    return google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            *args, **kwargs)


def get_auth_url(redirect_url):
    flow = get_flow()
    flow.redirect_uri = redirect_url or url_for('process_google_auth_response', _external=True)

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    return (authorization_url, state)


def no_spreadsheet_id():
    return ('Error', "You must set a Spreadsheet ID from Google Sheets")


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
    (url, state) = get_auth_url(
        url_for('process_google_auth_response', _external=True))
    return redirect(url)


@app.route('/oauth2callback')
def process_google_auth_response():
    error = request.args.get('error', None)
    if error is not None:
        return render_template('index.html',
                               title="oAuth Error",
                               message=error)

    flow = get_flow(request.args['state'])
    flow.redirect_uri = url_for('process_google_auth_response', _external=True)

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    return render_template('index.html',
                           title="success",
                           message=credentials.token)
