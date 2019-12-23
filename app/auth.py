# from https://developers.google.com/identity/protocols/OAuth2WebServer
import google_auth_oauthlib.flow
from flask import url_for


def get_flow(state=None):
    args = ['/config/client_secret.json',
            ['https://www.googleapis.com/auth/spreadsheets']]
    kwargs = {}
    if state is not None:
        kwargs['state'] = state

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        *args, **kwargs)
    flow.redirect_uri = url_for('process_google_auth_response', _external=True)
    return flow
