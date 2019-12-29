import os
import pickle
from flask import request, url_for
from google.auth.exceptions import RefreshError
from app import app
from app.google import (
    complete_auth as complete_google_auth,
    configure_spreadsheet,
    get_all_spreadsheets,
    get_auth_url as get_google_auth_url,
    get_config,
    get_data,
    get_sheets,
    is_configured,
)
from app.github import (
    complete_auth as complete_github_auth,
    get_all_repos,
    get_auth_url as get_github_auth_url,
    send_file,
)
from app.cookie import Cookie


def init_request_vars():
    context = {}
    c = Cookie(request)
    context['message'] = c.session.pop('message')
    context['message_context'] = c.session.pop('message_context', 'info')
    context['google_creds'] = c.session.get('google_credentials')
    context['github_creds'] = c.session.get('github_credentials')
    return c, context


@app.route('/')
def index():
    c, context = init_request_vars()
    context['spreadsheet_id'] = request.args.get('s')
    context['spreadsheet_name'] = request.args.get('n')
    if context['spreadsheet_id'] is not None:
        c.session.set('spreadsheet_id', context['spreadsheet_id'])
        c.session.set('spreadsheet_name', context['spreadsheet_name'])
        if context['message'] is None:
            context['message'] = (
                f'Spreadsheet selected: {context["spreadsheet_name"]}')
            context['message_context'] = 'success'
    else:
        context['spreadsheet_id'] = c.session.get('spreadsheet_id')

    context['repo_id'] = request.args.get('r')
    context['repo_name'] = request.args.get('n')
    if context['repo_id'] is not None:
        c.session.set('repo_id', context['repo_id'])
        c.session.set('repo_name', context['repo_name'])
        if context['message'] is None:
            context['message'] = f'Repository selected: {context["repo_name"]}'
            context['message_context'] = 'success'
    else:
        context['repo_name'] = c.session.get('repo_name')

    try:
        context['sheet_is_setup'] = (
            context['google_creds'] is not None and
            context['spreadsheet_id'] is not None and
            is_configured(
                context['google_creds'],
                context['spreadsheet_id']) is not False)
    except RefreshError:
        context['title'] = "Google Authentication expired"
        context['instruction'] = (
            "You need to login to Google again.")
        context['action'] = url_for('trigger_google_auth')
        context['cta'] = "Login with Google"
        return c.render_template(context=context)

    context['auto'] = request.args.get('auto')
    if context['auto'] is not None:
        c.session.set('auto', context['auto'])
    else:
        context['auto'] = c.session.get('auto')

    if context['google_creds'] is None or context['google_creds'] == {}:
        context['title'] = "Login"
        context['instruction'] = (
            "You need to sign in with your Google Account"
            " before you can go any further, in order"
            " to access your spreadsheets")
        context['action'] = url_for('trigger_google_auth')
        context['cta'] = "Login with Google"
    elif context['github_creds'] is None or context['github_creds'] == {}:
        context['title'] = "Login again"
        context['instruction'] = (
            "You need to sign in with your Github Account"
            " before you can go any further, in order"
            " to access your repositories")
        context['action'] = url_for('trigger_github_auth')
        context['cta'] = "Login with Github"
    elif context['spreadsheet_id'] is None:
        return c.redirect(url_for('sheets'))
    elif context['sheet_is_setup'] is False and context['repo_name'] is None:
        return c.redirect(url_for('repos'))
    elif context['sheet_is_setup'] is False:
        return c.redirect(url_for('setup_sheet'))
    else:
        if context['auto'] == 'true':
            return c.redirect(url_for('sync'))

        if request.args.get('complete') == 'true':
            context['title'] = "All done"
            context['instruction'] = (
                "Your sheet has been sent to "
                f'<a href="https://github.com/{c.session.get("config").get("repo_name")}/pulls">'
                f'the repo</a>'
                " and is ready for you to pick up there.")
        else:
            context['title'] = "Ready for service wash!"
            context['instruction'] = (
                "All checks completed. Setup your sheet for"
                " easier direct sync in future.")
            context['action'] = url_for('instructions')
            context['cta'] = "Set your sheet up"

    return c.render_template(context=context)


@app.route('/google_auth')
def trigger_google_auth():
    c = Cookie(request)
    url, state = get_google_auth_url()
    c.session.set('state', state)
    return c.redirect(url)


@app.route('/google_oauth2callback')
def process_google_auth_response():
    c = Cookie(request)
    error = request.args.get('error', None)
    if error is not None:
        c.session.set('message', f'Error logging in to Google: {error}')
        c.session.set('message_context', 'warning')
    else:
        state = c.session.get('state')
        creds = complete_google_auth(state, request.url)
        c.session.set('google_credentials',
                      pickle.dumps(creds))
        c.session.delete('state')
        c.session.set('message', "Google login succeeded")
        c.session.set('message_context', 'success')
    return c.redirect('/')


@app.route('/github_auth')
def trigger_github_auth():
    return get_github_auth_url()


@app.route('/github_oauth2callback')
def process_github_auth_response():
    c = Cookie(request)
    token = complete_github_auth()
    c.session.set('github_credentials', token)
    c.session.set('message', "Github login succeeded")
    c.session.set('message_context', 'success')
    return c.redirect('/')


@app.route('/logout')
def logout():
    c = Cookie(request)
    c.reset()
    c.session.set('message', "You've been logged out of Google and Github")
    c.session.set('message_context', 'success')
    return c.redirect('/')


@app.route('/choose_sheet')
def sheets():
    c, context = init_request_vars()

    try:
        sheets = get_all_spreadsheets(c.session.get('google_credentials'))
    except RefreshError:
        context['title'] = "Google Authentication expired"
        context['instruction'] = (
            "You need to login to Google again.")
        context['action'] = url_for('trigger_google_auth')
        context['cta'] = "Login with Google"
        return c.render_template(context=context)

    context['data'] = sheets
    context['title'] = "Select a sheet"
    context['instruction'] = "Choose which sheet to send to the Laundromat"
    context['description'] = (
        "Only the sheets you've edited most recently appear here; "
        "if you don't see the one you expect please edit it and "
        "refresh this page.")
    context['choice_var'] = 's'
    return c.render_template('chooser.html', context=context)


@app.route('/choose_repo')
def repos():
    c, context = init_request_vars()

    repos = get_all_repos(c.session.get('github_credentials'))
    context['data'] = repos
    context['title'] = "Select a repository"
    context['instruction'] = "Choose which repository to connect to this sheet"
    context['description'] = (
        "Your most recently updated repos are shown here"
        "if you don't see the one you expect please edit it and "
        "refresh this page.")
    context['choice_var'] = 'r'
    context['name_field'] = 'full_name'
    return c.render_template('chooser.html', context=context)


@app.route('/setup_sheet', methods=['GET', 'POST'])
def setup_sheet():
    c, context = init_request_vars()

    try:
        context['all_sheets'] = get_sheets(
            context['google_creds'], c.session.get('spreadsheet_id'))
    except RefreshError:
        context['title'] = "Google Authentication expired"
        context['instruction'] = (
            "You need to login to Google again.")
        context['action'] = url_for('trigger_google_auth')
        context['cta'] = "Login with Google"
        return c.render_template(context=context)

    context['spreadsheet_name'] = c.session.get('spreadsheet_name')

    context['title'] = "Setup the sheet"
    context['instruction'] = (
        "Configure the details of how the"
        " sheet ends up in the repository")
    context['description'] = (
        "These details will be saved in a new worksheet called 'Laundromat',"
        " which will be created on your selected spreadsheet. In future you"
        "  can edit this sheet directly, being careful since typos can break"
        " the script")

    if request.method == 'POST':
        if c.session.get('repo_name') != request.form.get("repo_name"):
            c.session.set('repo_name', request.form.get('repo_name'))
            c.session.delete('repo_id')

        config = request.form.to_dict()
        config['skip_pr'] = request.form.get('skip_pr')
        response = configure_spreadsheet(
            context['google_creds'], c.session.get('spreadsheet_id'), config)
        c.session.set('config', config)
        if len(response['replies']) > 0:
            c.session.set('message', 'Spreadsheet configured successfully')
            c.session.set('message_context', 'success')
            return c.redirect('/')
        else:
            c.session.set(
                'message', 'Something went wrong configuring the spreadsheet')
            c.session.set('message_context', 'error')

    context['spreadsheet_sheet'] = request.form.get(
        "spreadsheet_sheet") or c.session.get('spreadsheet_sheet')
    context['repository_name'] = request.form.get(
        "repo_name") or c.session.get('repo_name')
    context['repo_branch'] = c.session.get("repo_branch") or '__auto__'
    context['pr_target'] = c.session.get("pr_target") or 'master'
    context['skip_pr'] = c.session.get("skip_pr") or False
    context['repo_path'] = c.session.get("repo_path") or 'data'
    context['file_name'] = c.session.get("file_name") or 'copy.csv'

    return c.render_template('setup.html', context=context)


@app.route('/sync')
def sync():
    c, context = init_request_vars()
    if (context['google_creds'] is None or
            context['google_creds'] == {} or
            context['github_creds'] is None or
            context['github_creds'] == {}):
        url = '/?auto=true'
        if request.args.get('s') is not None:
            url += f'&s={request.args.get("s")}'
        if request.args.get('n') is not None:
            url += f'&n={request.args.get("n")}'
        return c.redirect(url)
    context['title'] = "Sync"
    context['instruction'] = "probably set a message and redirect i guess"
    context['description'] = ""

    try:
        config = get_config(context['google_creds'],
                            c.session.get('spreadsheet_id'))
    except RefreshError:
        context['title'] = "Google Authentication expired"
        context['instruction'] = (
            "You need to login to Google again.")
        context['action'] = url_for('trigger_google_auth')
        context['cta'] = "Login with Google"
        return c.render_template(context=context)

    c.session.set('config', config)
    csv_str = get_data(context['google_creds'],
                       c.session.get('spreadsheet_id'), config)
    outcome = send_file(context['github_creds'],
                        c.session.get('config'), csv_str)

    if (outcome is True):
        c.session.set('message', 'Sync completed successfully')
        c.session.set('message_context', 'success')
        c.session.delete('auto')
        return c.redirect('/?complete=true')
    else:
        context['message'] = 'Something went wrong'
        context['message_context'] = 'error'

    return c.render_template(context=context)


@app.route('/instructions')
def instructions():
    c, context = init_request_vars()
    context['action'] = url_for('sync')
    context['cta'] = "Just sync the data now"
    context['base_url'] = os.environ.get('BASE_URL')
    return c.render_template('instructions.html', context=context)


@app.errorhandler(404)
def not_found_error(error):
    c, _ = init_request_vars()
    return c.render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    c, _ = init_request_vars()
    return c.render_template('500.html'), 500
