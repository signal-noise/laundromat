# from https://developers.google.com/identity/protocols/OAuth2WebServer
import google.oauth2.credentials
import google_auth_oauthlib.flow

def get_flow(state=None):
    args = ['/config/client_secret.json',
        ['https://www.googleapis.com/auth/spreadsheets']]
    kwargs = {}
    if state is not None:
        kwargs['state'] = state
    return google_auth_oauthlib.flow.Flow.from_client_secrets_file(*args, **kwargs)

def get_auth_url(redirect_url):
    flow = get_flow()
    # flow.redirect_uri = redirect_url
    flow.redirect_uri = 'https://f467a14e.ngrok.io/oauth2callback'

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    return (authorization_url, state)
