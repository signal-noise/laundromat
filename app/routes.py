import os

from flask import redirect, render_template, request, url_for
from app import app

from app.auth import get_auth_url, get_flow

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
    (url, state) = get_auth_url(url_for('process_google_auth_response', _external=True))
    return redirect(url)


@app.route('/oauth2callback')
def process_google_auth_response():
    error = request.args.get('error', None)
    if error is not None:
        return render_template('index.html', title="oAuth Error", message=error)
    
    auth_code = request.args['code']
    
    flow = get_flow(request.args['state'])
    flow.redirect_uri = 'https://f467a14e.ngrok.io/oauth2callback'# url_for('process_google_auth_response', _external=True)

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    return render_template('index.html', title="success", message=credentials.token)
