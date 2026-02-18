from rapidfuzz.distance import Levenshtein as Lev


class BKNode:
    def __init__(self, word: str):
        self.word = word
        self.children = {}  # distance -> BKNode


class BKTree:
    def __init__(self):
        self.root = None
        # keep a set of all words added for robust fallback matching
        self.words = set()

    def add(self, word: str):
        if not word:
            return
        self.words.add(word)
        if self.root is None:
            self.root = BKNode(word)
            return
        node = self.root
        while True:
            d = Lev.distance(word, node.word)
            if d in node.children:
                node = node.children[d]
            else:
                node.children[d] = BKNode(word)
                break

    def query(self, word: str, max_dist: int = 1):
        """Return list of (distance, candidate) for candidates within max_dist."""
        if self.root is None:
            # still try fallback against words set
            return [(Lev.distance(word, w), w) for w in sorted(self.words) if Lev.distance(word, w) <= max_dist]
        candidates = []
        stack = [self.root]
        while stack:
            node = stack.pop()
            d = Lev.distance(word, node.word)
            if d <= max_dist:
                candidates.append((d, node.word))
            lo = d - max_dist
            hi = d + max_dist
            for dist_k, child in node.children.items():
                if lo <= dist_k <= hi:
                    stack.append(child)
        # sort by distance then word
        candidates.sort(key=lambda x: (x[0], x[1]))
        # If tree search produced few or no candidates, fallback to scanning words set
        if len(candidates) == 0 and self.words:
            fb = []
            for w in self.words:
                d2 = Lev.distance(word, w)
                if d2 <= max_dist:
                    fb.append((d2, w))
            fb.sort(key=lambda x: (x[0], x[1]))
            # merge unique
            seen = {c[1] for c in candidates}
            for item in fb:
                if item[1] not in seen:
                    candidates.append(item)
        return candidates


class SymSpellIndex:
    """A very small reference deletes index similar to SymSpell.

    This is optional and not used by the main app, but provided for reference.
    """
    def __init__(self, max_edit_distance=1):
        self.max_edit_distance = max_edit_distance
        self.deletes = {}  # delete_form -> set(original_word)

    def _deletes_for_word(self, word):
        deletes = set()
        splits = [(word[:i], word[i:]) for i in range(len(word)+1)]
        for i in range(len(word)):
            deletes.add(word[:i] + word[i+1:])
        return deletes

    def add(self, word: str):
        for d in self._deletes_for_word(word):
            self.deletes.setdefault(d, set()).add(word)

    def lookup(self, term: str):
        return self.deletes.get(term, set())
