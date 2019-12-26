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


@app.route('/')
def index():
    context = {}
    c = Cookie(request)
    context['message'] = c.session.pop('message', '')

    context['google_creds'] = c.session.get('google_credentials')
    context['github_creds'] = c.session.get('github_credentials')

    context['spreadsheet_id'] = request.args.get('s')
    if context['spreadsheet_id'] is not None:
        c.session.set('spreadsheet_id', context['spreadsheet_id'])
    else:
        context['spreadsheet_id'] = c.session.get('spreadsheet_id')

    context['repo_name'] = request.args.get('r')
    if context['repo_name'] is not None:
        c.session.set('repo_name', context['repo_name'])
    else:
        context['repo_name'] = c.session.get('repo_name')

    context['sheet_is_setup'] = False  # get a way to do this

    if context['google_creds'] is None or context['google_creds'] == {}:
        context['title'] = "Google authentication needed"
        context['instruction'] = "You need to sign in with your Google Account before you can go any further"
        context['action'] = url_for('trigger_google_auth')
        context['cta'] = "Login with Google"
    elif context['github_creds'] is None or context['github_creds'] == {}:
        context['title'] = "Github authentication needed"
        context['instruction'] = "You need to sign in with your Github Account before you can go any further"
        context['action'] = url_for('trigger_github_auth')
        context['cta'] = "Login with Github"
    elif context['spreadsheet_id'] is None:
        context['title'] = "No spreadsheet selected"
        context['instruction'] = "You need to select a spreadsheet before you can go any further"
        context['action'] = url_for('sheets')
        context['cta'] = "Select Sheet"
    elif context['repo_name'] is None:
        context['title'] = "No repository selected"
        context['instruction'] = "You need to select a repo before you can go any further"
        context['action'] = url_for('repos')
        context['cta'] = "Select Repo"
    elif context['sheet_is_setup'] is False:
        context['title'] = "Spreadsheet is not configured"
        context['instruction'] = "You need to setup your sheet. We can do this automatically right now"
        context['action'] = url_for('setup_sheet')
        context['cta'] = "Setup sheet"
    else:
        context['title'] = "All checks completed"
        context['instruction'] = "Let's send your sheet over!"
        context['action'] = url_for('sync')
        context['cta'] = "Send"

        if request.args.get('auto') == 'true':
            return c.redirect(url_for('sync'))

    return c.render_template(context=context)


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
        c.session.set('message', f'Error logging in to Google: {error}')
    else:
        complete_google_auth(c, request.url)
        c.session.set('message', "Google login succeeded")
    return c.redirect('/')


@app.route('/github_auth')
def trigger_github_auth():
    return get_github_auth_url()


@app.route('/github_oauth2callback')
def process_github_auth_response():
    c = Cookie(request)
    complete_github_auth(c)
    c.session.set('message', "Github login succeeded")
    return c.redirect('/')


@app.route('/logout')
def logout():
    c = Cookie(request)
    c.reset()
    c.session.set('message', "You've been logged out of Google and Github")
    return c.redirect('/')


@app.route('/choose_sheet')
def sheets():
    context = {}
    c = Cookie(request)
    context['message'] = c.session.pop('message', '')

    sheets = get_all_sheets(c)
    context['data'] = sheets
    context['title'] = "Select a sheet"
    context['instruction'] = "Choose which sheet to send over"
    context['description'] = "Only the sheets you've edited most recently appear here; if you don't see the one you expect please edit it and refresh this page."
    return c.render_template(context=context)


@app.route('/choose_repo')
def repos():
    context = {}
    c = Cookie(request)
    context['message'] = c.session.pop('message', '')

    repos = get_all_repos(c)
    context['data'] = repos
    context['title'] = "Select a repository"
    context['instruction'] = "Choose which repository to connect to this sheet"
    context['description'] = "Your most recently updated repos are shown here"
    return c.render_template(context=context)


@app.route('/setup_sheet')
def setup_sheet():
    context = {}
    c = Cookie(request)
    context['message'] = c.session.pop('message', '')

    context['data'] = 'sheet config here'
    context['title'] = "Setup the sheet"
    context['instruction'] = "Configure the details of the sync"
    context['description'] = "These details will be saved in a new worksheet, which you can edit directly in future"
    return c.render_template(context=context)


@app.route('/sync')
def sync():
    context = {}
    c = Cookie(request)
    context['message'] = c.session.pop('message', '')

    context['title'] = "Sync"
    context['instruction'] = "probably set a message and redirect i guess"
    context['description'] = ""
    return c.render_template(context=context)
