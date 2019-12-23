"""A session-like object connected to the Firestore backend"""

import datetime
from google.cloud import firestore


class Session:

    def __init__(self, uid, expiry=30):
        self.db = firestore.Client()
        self.uid = uid
        self.doc_ref = self.db.collection(u'session').document(uid)
        self.expiry = expiry

    def get(self, key=None):
        doc_dict = self.doc_ref.get().to_dict()
        if doc_dict is None:
            return {}
        expires_at = datetime.datetime.fromtimestamp(
            doc_dict.get('expires_at', 0))
        if expires_at < datetime.datetime.utcnow():
            self.remove()
            return {}
        if key is not None:
            return doc_dict.get(key, None)
        else:
            return doc_dict

    def set(self, key, value):
        doc_dict = self.get()
        doc_dict[key] = value
        return self.save(doc_dict)

    def save(self, dict):
        expires_at = (datetime.datetime.utcnow()
                      + datetime.timedelta(self.expiry))
        dict['expires_at'] = expires_at.timestamp()
        self.doc_ref.set(dict)
        return self

    def delete(self, key):
        doc_dict = self.doc_ref.get().to_dict()
        if doc_dict is None:
            return {}
        value = doc_dict.pop(key, None)
        if value is None:
            return f'Key {key} was not found on the session'
        return self.save(doc_dict)

    def remove(self):
        self.doc_ref.set({})
        self.doc_ref.delete()
        return self
