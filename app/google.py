# from https://developers.google.com/identity/protocols/OAuth2WebServer
import logging
import pickle
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from flask import url_for

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

#
# Auth
#


def get_flow(state=None):
    """Configures the google-specific SDK that does the hard work"""
    args = ['/config/client_secret.json',
            ['https://www.googleapis.com/auth/drive.metadata.readonly',
             'https://www.googleapis.com/auth/drive',
             'https://www.googleapis.com/auth/drive.file',
             'https://www.googleapis.com/auth/drive.install',
             'https://www.googleapis.com/auth/spreadsheets',
             ]
            ]
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
        'scopes': credentials.scopes,
        'pickled': pickle.dumps(credentials)
    }
    )
    cookie.session.delete('state')
    return


#
# Getting lists and metadata for UI and setting config
#

def get_all_spreadsheets(cookie):
    creds_dict = cookie.session.get('google_credentials')
    creds = pickle.loads(creds_dict['pickled'])
    service = build('drive', 'v3', credentials=creds)
    results = service.files().list(
        q="mimeType='application/vnd.google-apps.spreadsheet'",
        orderBy="modifiedTime desc",
        fields="files(id, name)",
        pageSize=20,
        corpora="allDrives",
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
    ).execute()
    items = results.get('files', [])
    return items


def get_spreadsheet_raw(cookie, spreadsheet_id):
    creds_dict = cookie.session.get('google_credentials')
    creds = pickle.loads(creds_dict['pickled'])
    service = build('sheets', 'v4', credentials=creds)
    results = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id).execute()
    return results


def get_sheets(cookie, spreadsheet_id):
    return [x['properties']['title']
            for x in get_spreadsheet_raw(
                cookie, spreadsheet_id).get('sheets', [])
            if x['properties']['title'] != 'Laundromat']


def is_configured(cookie, spreadsheet_id):
    sheets = get_spreadsheet_raw(cookie, spreadsheet_id).get('sheets', [])
    for sheet in sheets:
        if sheet['properties']['title'] == 'Laundromat':
            return sheet['properties']['sheetId']
    return False


def get_or_create_config_sheet_id(cookie, spreadsheet_id):
    creds_dict = cookie.session.get('google_credentials')
    creds = pickle.loads(creds_dict['pickled'])
    service = build('sheets', 'v4', credentials=creds)

    sheet_id = is_configured(cookie, spreadsheet_id)
    if sheet_id is False:
        requests = [{
            "addSheet": {
                "properties": {
                    "title": "Laundromat"
                }
            }
        }]
        results = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        sheet_id = results['replies'][0]['addSheet']['properties']['sheetId']
    return sheet_id


def configure_spreadsheet(cookie, spreadsheet_id, config):
    sheet_id = get_or_create_config_sheet_id(cookie, spreadsheet_id)

    creds_dict = cookie.session.get('google_credentials')
    creds = pickle.loads(creds_dict['pickled'])
    service = build('sheets', 'v4', credentials=creds)
    requests = [{
        "updateCells": {
            "start": {
                "sheetId": sheet_id,
                "rowIndex": 0,
                "columnIndex": 0
            },
            "fields": "*",
            "rows": [
                {
                    "values": [
                        {
                            "userEnteredValue": {
                                "stringValue": "sheet_name"
                            }
                        },
                        {
                            "userEnteredValue": {
                                "stringValue": "repo_name"
                            }
                        },
                        {
                            "userEnteredValue": {
                                "stringValue": "repo_branch"
                            }
                        },
                        {
                            "userEnteredValue": {
                                "stringValue": "pr_target"
                            }
                        },
                        {
                            "userEnteredValue": {
                                "stringValue": "skip_pr"
                            }
                        },
                        {
                            "userEnteredValue": {
                                "stringValue": "repo_path"
                            }
                        },
                        {
                            "userEnteredValue": {
                                "stringValue": "file_name"
                            }
                        },
                    ]
                },
                {
                    "values": [
                        {
                            "userEnteredValue": {
                                "stringValue": config['spreadsheet_sheet']
                            }
                        },
                        {
                            "userEnteredValue": {
                                "stringValue": config['repo_name']
                            }
                        },
                        {
                            "userEnteredValue": {
                                "stringValue": config['repo_branch']
                            }
                        },
                        {
                            "userEnteredValue": {
                                "stringValue": config['pr_target']
                            }
                        },
                        {
                            "userEnteredValue": {
                                "boolValue": (True
                                              if config['skip_pr'] == 'on'
                                              else False)
                            }
                        },
                        {
                            "userEnteredValue": {
                                "stringValue": config['repo_path']
                            }
                        },
                        {
                            "userEnteredValue": {
                                "stringValue": config['file_name']
                            }
                        },
                    ]
                }
            ]
        }
    }]
    results = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={'requests': requests}).execute()
    return results


def get_config(cookie, spreadsheet_id):
    creds_dict = cookie.session.get('google_credentials')
    creds = pickle.loads(creds_dict['pickled'])
    service = build('sheets', 'v4', credentials=creds)
    datarange = 'Laundromat!A1:G2'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=datarange,
        majorDimension='COLUMNS',
    ).execute()
    config = {}
    for i in result['values']:
        config[i[0]] = i[1]
    return config


#
# CSV export
#


def to_csv_string(data):
    output = ""
    row_counter = 0
    for row in data:
        row_counter += 1
        cell_counter = 0
        for cell in row:
            if ',' in cell:
                row[cell_counter] = f'\"{cell}\"'
            cell_counter += 1
        output += ",".join(row)
        if row_counter < len(data):
            output += "\r\n"
    return output


def columnToLetter(column):
    letter = ''
    while column > 0:
        temp = (column - 1) % 26
        letter += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[temp]
        column = (column - temp - 1) / 26
    return letter


def get_data(cookie, spreadsheet_id):
    config = get_config(cookie, spreadsheet_id)
    metadata = get_spreadsheet_raw(cookie, spreadsheet_id)
    for item in metadata['sheets']:
        if item['properties']['title'] == config['sheet_name']:
            max_row = item['properties']['gridProperties']['rowCount']
            max_column = columnToLetter(
                item['properties']['gridProperties']['columnCount'])
    datarange = f'{config["sheet_name"]}!A1:{max_column}{max_row}'

    creds_dict = cookie.session.get('google_credentials')
    creds = pickle.loads(creds_dict['pickled'])
    service = build('sheets', 'v4', credentials=creds)

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=datarange,
    ).execute()

    return to_csv_string(result['values'])
