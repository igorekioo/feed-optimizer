from flask.sessions import SessionInterface, SessionMixin
from flask import Flask, Response, request
import pickle
from werkzeug.datastructures import CallbackDict
import os
import tempfile
import datetime

class PersistentSessionDict(CallbackDict, SessionMixin):
    def __init__(self, initial=None, sid=None):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.modified = False

class FileSystemSessionInterface(SessionInterface):
    def __init__(self, storage_path=None):
        if storage_path is None:
            storage_path = os.path.join(tempfile.gettempdir(), 'flask_session')
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)
        self.storage_path = storage_path

    def get_session_filename(self, sid):
        return os.path.join(self.storage_path, f'session_{sid}')

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            sid = os.urandom(16).hex()
            return PersistentSessionDict(sid=sid)
        
        filename = self.get_session_filename(sid)
        if os.path.exists(filename):
            try:
                with open(filename, 'rb') as f:
                    data = pickle.load(f)
                return PersistentSessionDict(data, sid=sid)
            except (IOError, pickle.PickleError):
                return PersistentSessionDict(sid=sid)
        return PersistentSessionDict(sid=sid)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        if not session:
            if session.modified:
                response.delete_cookie(
                    app.session_cookie_name,
                    domain=domain
                )
            return
        
        path = self.get_session_filename(session.sid)
        try:
            with open(path, 'wb') as f:
                pickle.dump(dict(session), f)
        except (IOError, pickle.PickleError):
            pass
        
        response.set_cookie(
            app.session_cookie_name,
            session.sid,
            expires=self.get_expiration_time(app, session),
            httponly=True,
            domain=domain
        )
    
    def get_expiration_time(self, app, session):
        if session.permanent:
            return datetime.datetime.now() + app.permanent_session_lifetime
        return None
