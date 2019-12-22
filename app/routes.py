from flask import request, url_for
from app import app
from app.auth import get_flow
from app.cookie import Cookie


@app.route('/')
def index():
    c = Cookie(request)
    google_creds = c.session.get('credentials')
    if google_creds is not None and google_creds != {}:
        (title, message) = ('great', c.session.get('credentials'))
    else:
        return c.redirect(url_for('trigger_google_auth', _external=True))

    return c.render_template('index.html', title=title, message=message)


@app.route('/authenticate')
def trigger_google_auth():
    c = Cookie(request)
    flow = get_flow()
    flow.redirect_uri = url_for('process_google_auth_response', _external=True)
    url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')
    c.session.save('state', state)
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
    return c.redirect('/')
