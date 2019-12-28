
from flask import (render_template as flask_render_template,
                   make_response, redirect as flask_redirect)
import uuid
from app.session import Session


class Cookie:

    def __init__(self, request):
        self.retrieve_session_cookie(request)
        self.session = Session(self.uid)

    def reset(self):
        self.session.remove()
        self.uid = self.generate_uuid()
        self.session = Session(self.uid)

    def get_session(self):
        return self.session

    def retrieve_session_cookie(self, request):
        if 'sessionid' in request.cookies:
            self.uid = request.cookies['sessionid']
        else:
            self.uid = self.generate_uuid()
        return self.uid

    def generate_uuid(self):
        return str(uuid.uuid4())

    def render_template(self, *args, **kwargs):
        if args is None or len(args) == 0:
            args = ('index.html', )
        if 'context' in kwargs:
            for k, v in kwargs['context'].items():
                kwargs[k] = v
        resp = make_response(flask_render_template(*args, **kwargs))
        resp.set_cookie('sessionid', self.uid)
        return resp

    def redirect(self, url):
        resp = make_response(flask_redirect(url))
        resp.set_cookie('sessionid', self.uid)
        return resp
