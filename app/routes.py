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
    context = {}
    c = Cookie(request)
    context['message'] = c.session.get('message', '')
    c.session.delete('message')

    google_creds = c.session.get('google_credentials')
    github_creds = c.session.get('github_credentials')

    context['spreadsheet_id'] = request.args.get('s')
    if context['spreadsheet_id'] is not None:
        c.session.set('spreadsheet_id', context['spreadsheet_id'])
    else:
        context['spreadsheet_id'] = c.session.get('spreadsheet_id')

    if google_creds is not None and google_creds != {}:
        if github_creds is not None:
            return c.redirect('/test_github')
        else:
            # return c.redirect(url_for('trigger_github_auth'))
            context['instruction'] = "You need to sign in with your Github Account before you can go any further"
            context['action'] = url_for('trigger_github_auth')
            context['cta'] = "Login with Github"
    else:
        context['instruction'] = "You need to sign in with your Google Account before you can go any further"
        context['action'] = url_for('trigger_google_auth')
        context['cta'] = "Login with Google"
        # return c.redirect(url_for('trigger_google_auth'))

    return c.render_template(context=context)


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
    return c.redirect('/')


@app.route('/test_google')
def sheets():
    context = {}
    c = Cookie(request)
    context['message'] = c.session.get('message', '')
    c.session.delete('message')

    sheets = get_all_sheets(c)
    context['message'] = sheets
    return c.render_template(context=context)


@app.route('/test_github')
def repos():
    context = {}
    c = Cookie(request)
    context['message'] = c.session.get('message', '')
    c.session.delete('message')

    repos = get_all_repos(c)
    context['message'] = repos
    return c.render_template(context=context)
