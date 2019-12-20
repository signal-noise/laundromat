"""A fake session-like object connected to the Firestore backend"""

import datetime
from google.cloud import firestore


class Session:

    def __init__(self, uid, expiry=30):
        self.db = firestore.Client()
        self.uid = uid
        self.doc_ref = self.db.collection(u'session').document(uid)
        self.expiry = expiry


    def get(self, key = None):
        doc_dict = self.doc_ref.get().to_dict()
        if doc_dict is None:
            return {}
        expires_at = datetime.datetime.fromtimestamp(doc_dict['expires_at'])
        if expires_at < datetime.datetime.utcnow():
            self.remove()
            return {}
        if key is not None:
            return doc_dict.get(key, None)
        else:
            return doc_dict

    def save(self, key, value):
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(self.expiry)
        doc_dict = self.get()
        doc_dict[key] = value
        doc_dict['expires_at'] = expires_at.timestamp()
        self.doc_ref.set(doc_dict)
        return self

    def remove(self):
        self.doc_ref.set({})
        return self