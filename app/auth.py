import google_auth_oauthlib.flow


def get_flow(state=None):
    args = ['/config/client_secret.json',
            ['https://www.googleapis.com/auth/spreadsheets']]
    kwargs = {}
    if state is not None:
        kwargs['state'] = state
    return google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        *args, **kwargs)
