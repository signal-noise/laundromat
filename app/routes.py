from flask import request, url_for
from app import app
from app.google import (
    complete_auth as complete_google_auth,
    configure_spreadsheet,
    get_all_spreadsheets,
    get_auth_url as get_google_auth_url,
    get_data,
    get_sheets,
    is_configured,
)
from app.github import (
    complete_auth as complete_github_auth,
    get_all_repos,
    get_auth_url as get_github_auth_url,
    write_file,
)
from app.cookie import Cookie


@app.route('/')
def index():
    context = {}
    c = Cookie(request)
    context['message'] = c.session.pop('message')
    context['message_context'] = c.session.pop('message_context', 'info')
    context['google_creds'] = c.session.get('google_credentials')
    context['github_creds'] = c.session.get('github_credentials')

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

    context['sheet_is_setup'] = (
        context['google_creds'] is not None and
        context['spreadsheet_id'] is not None and
        is_configured(c, context['spreadsheet_id']) is not False)

    if context['google_creds'] is None or context['google_creds'] == {}:
        context['title'] = "Google authentication needed"
        context['instruction'] = (
            "You need to sign in with your Google Account"
            " before you can go any further")
        context['action'] = url_for('trigger_google_auth')
        context['cta'] = "Login with Google"
    elif context['github_creds'] is None or context['github_creds'] == {}:
        context['title'] = "Github authentication needed"
        context['instruction'] = (
            "You need to sign in with your Github Account"
            " before you can go any further")
        context['action'] = url_for('trigger_github_auth')
        context['cta'] = "Login with Github"
    elif context['spreadsheet_id'] is None:
        return c.redirect(url_for('sheets'))
    elif context['sheet_is_setup'] is False and context['repo_name'] is None:
        return c.redirect(url_for('repos'))
    elif context['sheet_is_setup'] is False:
        return c.redirect(url_for('setup_sheet'))
    else:
        if request.args.get('auto') == 'true':
            return c.redirect(url_for('sync'))

        context['title'] = "All checks completed"
        context['instruction'] = "Let's send your sheet over!"
        context['action'] = url_for('sync')
        context['cta'] = "Send"

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
        c.session.set('message_context', 'warning')
    else:
        complete_google_auth(c, request.url)
        c.session.set('message', "Google login succeeded")
        c.session.set('message_context', 'success')
    return c.redirect('/')


@app.route('/github_auth')
def trigger_github_auth():
    return get_github_auth_url()


@app.route('/github_oauth2callback')
def process_github_auth_response():
    c = Cookie(request)
    complete_github_auth(c)
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
    context = {}
    c = Cookie(request)
    context['message'] = c.session.pop('message')
    context['message_context'] = c.session.pop('message_context', 'info')
    context['google_creds'] = c.session.get('google_credentials')
    context['github_creds'] = c.session.get('github_credentials')

    sheets = get_all_spreadsheets(c)
    context['data'] = sheets
    context['title'] = "Select a sheet"
    context['instruction'] = "Choose which sheet to send over"
    context['description'] = (
        "Only the sheets you've edited most recently appear here; "
        "if you don't see the one you expect please edit it and "
        "refresh this page.")
    context['choice_var'] = 's'
    return c.render_template('chooser.html', context=context)


@app.route('/choose_repo')
def repos():
    context = {}
    c = Cookie(request)
    context['message'] = c.session.pop('message')
    context['message_context'] = c.session.pop('message_context', 'info')
    context['google_creds'] = c.session.get('google_credentials')
    context['github_creds'] = c.session.get('github_credentials')

    repos = get_all_repos(c)
    context['data'] = repos
    context['title'] = "Select a repository"
    context['instruction'] = "Choose which repository to connect to this sheet"
    context['description'] = "Your most recently updated repos are shown here"
    context['choice_var'] = 'r'
    context['name_field'] = 'full_name'
    return c.render_template('chooser.html', context=context)


@app.route('/setup_sheet', methods=['GET', 'POST'])
def setup_sheet():
    context = {}
    c = Cookie(request)
    context['message'] = c.session.pop('message')
    context['message_context'] = c.session.pop('message_context', 'info')
    context['google_creds'] = c.session.get('google_credentials')
    context['github_creds'] = c.session.get('github_credentials')
    context['spreadsheet_name'] = c.session.get('spreadsheet_name')

    context['title'] = "Setup the sheet"
    context['instruction'] = "Configure the details of the sync"
    context['description'] = (
        "These details will be saved in a new worksheet called 'Laundromat',"
        " which will be created on your selected spreadsheet. In future you"
        "  can edit this sheet directly, being careful since typos can break"
        " the script")

    context['all_sheets'] = get_sheets(c, c.session.get('spreadsheet_id'))

    if request.method == 'POST':
        if c.session.get('repo_name') != request.form.get("repo_name"):
            c.session.set('repo_name', request.form.get('repo_name'))
            c.session.delete('repo_id')

        config = request.form.to_dict()
        config['skip_pr'] = request.form.get('skip_pr')
        response = configure_spreadsheet(
            c, c.session.get('spreadsheet_id'), config)
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
    context = {}
    c = Cookie(request)
    context['message'] = c.session.pop('message')
    context['message_context'] = c.session.pop('message_context', 'info')
    context['google_creds'] = c.session.get('google_credentials')
    context['github_creds'] = c.session.get('github_credentials')

    context['title'] = "Sync"
    context['instruction'] = "probably set a message and redirect i guess"
    context['description'] = ""

    csv_str = get_data(c, c.session.get('spreadsheet_id'))
    context['data'] = write_file(c, csv_str)
    return c.render_template(context=context)
