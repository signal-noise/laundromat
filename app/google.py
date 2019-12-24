# from https://developers.google.com/identity/protocols/OAuth2WebServer
import google_auth_oauthlib.flow
from flask import url_for


def get_flow(state=None):
    """Configures the google-specific SDK that does the hard work"""
    args = ['/config/client_secret.json',
            ['https://www.googleapis.com/auth/spreadsheets']]
    kwargs = {}
    if state is not None:
        kwargs['state'] = state

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        *args, **kwargs)
    flow.redirect_uri = url_for('process_google_auth_response', _external=True)
    return flow


def get_auth_url(cookie):
    """Does the initial part of the auth request work"""
    flow = get_flow()
    url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')
    cookie.session.set('state', state)
    return url


def complete_auth(cookie, url):
    state = cookie.session.get('state')
    flow = get_flow(state)
    flow.fetch_token(authorization_response=url)
    credentials = flow.credentials
    cookie.session.set('google_credentials', {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes}
    )
    cookie.session.delete('state')
    return


def get_all_sheets(cookie):
    return []
