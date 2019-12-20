"""A fake session-like object connected to the Firestore backend"""

from google.cloud import firestore


class Session:

    def __init__(self, uid):
        self.db = firestore.Client()
        self.uid = uid
        self.doc_ref = self.db.collection(u'session').document(uid)


    def get(self, key = None):
        doc_dict = self.doc_ref.get().to_dict()
        if doc_dict is None:
            doc_dict = {}
        if key is not None:
            print(f'getting {key}')
            return doc_dict.get(key, None)
        else:
            return doc_dict

    def save(self, key, value):
        doc_dict = self.get()
        print('-----------------------')
        print(doc_dict)
        doc_dict[key] = value
        self.doc_ref.set(doc_dict)
        return doc_dict

    def remove(self):
        self.doc_ref.set({})
        return True