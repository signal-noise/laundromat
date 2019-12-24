from flask import request, url_for
from app import app
from app.google import (
    complete_auth as complete_google_auth,
    get_all_sheets,
    get_auth_url as get_google_auth_url,
)
from app.github import (
    complete_auth as complete_github_auth,
    get_all_repos,
    get_auth_url as get_github_auth_url,
)
from app.cookie import Cookie

app.secret_key = 'super secret key'


@app.route('/')
def index():
    c = Cookie(request)
    google_creds = c.session.get('google_credentials')
    if google_creds is not None and google_creds != {}:
        spreadsheet_id = c.session.get('spreadsheet_id')
        if spreadsheet_id is None:
            spreadsheet_id = request.args.get('s')
        if spreadsheet_id is not None:
            c.session.set('spreadsheet_id', spreadsheet_id)
            github_token = c.session.get('github_token')
            if github_token is not None:
                return c.redirect('/test_github')
            else:
                return c.redirect(url_for('trigger_github_auth'))
        else:
            (title, message) = ('great', 'choose a sheet (?s=xxx)')
    else:
        return c.redirect(url_for('trigger_google_auth'))

    return c.render_template('index.html', title=title, message=message)


@app.route('/logout')
def logout():
    c = Cookie(request)
    c.reset()
    return c.render_template(
        title='logged out', message='go to / to start again')


@app.route('/google_auth')
def trigger_google_auth():
    c = Cookie(request)
    url = get_google_auth_url(c)
    return c.redirect(url)


@app.route('/google_oauth2callback')
def process_google_auth_response():
    c = Cookie(request)
    error = request.args.get('error', None)
    if error is not None:
        return c.render_template('index.html',
                                 title="oAuth Error",
                                 message=error)
    complete_google_auth(c, request.url)
    return c.redirect('/')


@app.route('/github_auth')
def trigger_github_auth():
    return get_github_auth_url()


@app.route('/github_oauth2callback')
def process_github_auth_response():
    c = Cookie(request)
    complete_github_auth(c)
    return c.redirect('/test')


@app.route('/test_google')
def sheets():
    c = Cookie(request)
    repos = get_all_sheets(c)
    return c.render_template(title='choose a spreadsheet', message=repos)


@app.route('/test_github')
def repos():
    c = Cookie(request)
    repos = get_all_repos(c)
    return c.render_template(title='choose a repo', message=repos)
