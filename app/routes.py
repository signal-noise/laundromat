from flask import request, url_for
from app import app
from app.auth import get_flow
from app.cookie import Cookie


@app.route('/')
def index():
    c = Cookie(request)
    google_creds = c.session.get('google_credentials')
    if google_creds is not None and google_creds != {}:
        spreadsheet_id = request.args.get('s')
        if spreadsheet_id is not None:
            c.session.set('spreadsheet_id', spreadsheet_id)
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


@app.route('/github_auth')
def trigger_github_auth():
    c = Cookie(request)
    return c.render_template('index.html', title='GH', message='okaaay')
