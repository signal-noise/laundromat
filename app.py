import datetime
from flask import Flask, render_template, request, jsonify, abort, make_response
from session import Session

app = Flask(__name__)

# uid and cookie bits

uid = 'marcel@signal-noise.co.uk'
session = Session(uid)


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


@app.route('/set')
def set_session():
    session.save('state', 'blah blah')
    resp = make_response(render_template('index.html', title='set', message=session.get()))
    resp.set_cookie('session', uid)
    return resp


@app.route('/get')
def get_session():
    message = session.get('state')
    return render_template('index.html', title='get', message=message)


