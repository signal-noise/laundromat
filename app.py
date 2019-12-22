import datetime
from flask import Flask, render_template, request, jsonify, abort, make_response
from cookie import Cookie


app = Flask(__name__)


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
    c = Cookie(request)
    c.session.save('state', 'foo bar')
    return c.render_template('index.html', title='set', message=c.session.get())


@app.route('/get')
def get_session():
    c = Cookie(request)
    message = c.session.get('state')
    return render_template('index.html', title='get', message=message)
