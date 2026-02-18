from .utils import tokenize
from collections import defaultdict
from .utils import stem

class InvertedIndex:
    def __init__(self):
        self.postings = defaultdict(set)  # term -> set(doc_id)
        self.docs = {}  # doc_id -> raw text

    def add_doc(self, doc_id: str, text: str):
        self.docs[doc_id] = text
        terms = set(tokenize(text))
        for t in terms:
            self.postings[t].add(doc_id)
            # also index stemmed form for broader matching
            s = stem(t)
            if s and s != t:
                self.postings[s].add(doc_id)

    def search_all(self, query: str):
        terms = [t for t in tokenize(query) if t]
        if not terms:
            return []
        sets = [self.postings.get(t, set()) for t in terms]
        # intersection
        res = set(sets[0]) if sets else set()
        for s in sets[1:]:
            res &= s
        return list(res)

    def get_doc(self, doc_id: str):
        return self.docs.get(doc_id)
