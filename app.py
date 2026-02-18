r"""
Run Instructions:

1. Create a virtual environment (Python 3.10+):
   python -m venv venv; venv\Scripts\activate
2. Install dependencies:
   pip install -r requirements.txt
3. Run the app:
   python app.py
4. Open http://127.0.0.1:5000/ in your browser.

This Flask app demonstrates normalization, BK-Tree spelling correction,
intent detection, inverted-index retrieval, and short-term conversation memory.
"""

import json
import os
from flask import Flask, render_template, request, jsonify
from ds.utils import normalize, tokenize, timer
from ds.bktree import BKTree
from ds.inverted_index import InvertedIndex
from ds.memory import ConversationMemory
from ds.sentence_corrector import sentence_correct, timer as sc_timer

APP_ROOT = os.path.dirname(__file__)
DATA_DIR = os.path.join(APP_ROOT, "data")
DICT_PATH = os.path.join(DATA_DIR, "dictionary.txt")
DOCS_DIR = os.path.join(DATA_DIR, "docs")
USER_LEARN_PATH = os.path.join(DATA_DIR, "user_learned.txt")
USER_COUNTS_PATH = os.path.join(DATA_DIR, "user_counts.json")

app = Flask(__name__)

# Initialize components
bk = BKTree()
index = InvertedIndex()
mem = ConversationMemory(maxlen=8)

INTENT_KEYWORDS = {
    'policy': ["proxy", "attendance", "fine", "rule", "policy"],
    'tech': ["camera", "model", "accuracy", "latency", "database", "schema"],
    'howto': ["how", "steps", "guide", "setup", "install", "run"],
}

Dictionary = set()


def load_resources():
    # load dictionary
    if os.path.exists(DICT_PATH):
        with open(DICT_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                w = line.strip()
                if w:
                    Dictionary.add(w)
                    bk.add(w)
    # load user-learned tokens (persisted)
    if os.path.exists(USER_LEARN_PATH):
        with open(USER_LEARN_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                w = line.strip()
                if not w or w.startswith('#'):
                    continue
                Dictionary.add(w)
                bk.add(w)
    # load docs
    if os.path.exists(DOCS_DIR):
        for fn in os.listdir(DOCS_DIR):
            path = os.path.join(DOCS_DIR, fn)
            if os.path.isfile(path) and fn.endswith('.txt'):
                with open(path, 'r', encoding='utf-8') as f:
                    text = f.read()
                index.add_doc(fn, text)
                # also add document tokens into dictionary and BK-Tree so spell correction knows domain words
                from ds.utils import tokenize
                for t in set(tokenize(text)):
                    if t and t not in Dictionary:
                        Dictionary.add(t)
                        bk.add(t)
    # load persisted user-learned counts
    global USER_COUNTS
    USER_COUNTS = {}
    try:
        import json
        if os.path.exists(USER_COUNTS_PATH):
            with open(USER_COUNTS_PATH, 'r', encoding='utf-8') as f:
                USER_COUNTS = json.load(f) or {}
    except Exception:
        USER_COUNTS = {}


def detect_intent(text: str) -> str:
    terms = set(tokenize(text))
    # also add stems for intent scoring
    from ds.utils import stem
    stem_terms = {stem(t) for t in terms}
    best = 'chat'
    best_score = 0
    for intent, keywords in INTENT_KEYWORDS.items():
        score = len((terms | stem_terms) & set(keywords))
        if score > best_score:
            best_score = score
            best = intent
    return best


@app.route('/')
def index_route():
    return render_template('index.html')


@app.route('/api/process', methods=['POST'])
def api_process():
    payload = request.get_json(force=True)
    text = payload.get('text', '')
    opts = payload.get('opts', {}) if isinstance(payload.get('opts', {}), dict) else {}
    do_spell = bool(opts.get('spell', True))
    do_retrieve = bool(opts.get('retrieve', True))

    stages = {}

    # Normalize
    with timer() as t:
        norm = normalize(text)
    stages['normalize'] = {'ms': t['ms'], 'normalized': norm}

    # Tokenize and Spell Correction
    corrections = []
    with timer() as t:
        tokens = tokenize(text)
        corrected_tokens = []
        from ds.utils import dedupe_letters
        for tok in tokens:
            if not do_spell:
                corrected_tokens.append(tok)
                corrections.append({'token': tok, 'candidates': []})
                continue

            if tok in Dictionary:
                corrected_tokens.append(tok)
                corrections.append({'token': tok, 'candidates': []})
                continue

            # try deduped form (handle heeey, pleeeease -> heey/please)
            ded = dedupe_letters(tok)
            if ded != tok and ded in Dictionary:
                corrected_tokens.append(ded)
                corrections.append({'token': tok, 'candidates': [ded]})
                continue

            # Query BK-Tree for original token
            cands = bk.query(tok, max_dist=1)
            # if no candidates, query deduped form as fallback
            if not cands and ded != tok:
                cands = bk.query(ded, max_dist=1)

            # top 3 unique words
            top = []
            for d, w in cands:
                if w not in top:
                    top.append(w)
                if len(top) >= 3:
                    break

            # If still empty, also try simple scan of Dictionary for small distances
            if not top:
                # linear scan fallback (only for small dictionaries)
                fb = []
                from rapidfuzz.distance import Levenshtein as Lev
                for w in Dictionary:
                    d2 = Lev.distance(tok, w)
                    if d2 <= 1:
                        fb.append((d2, w))
                fb.sort(key=lambda x: (x[0], x[1]))
                for d2, w in fb[:3]:
                    if w not in top:
                        top.append(w)

            corrections.append({'token': tok, 'candidates': top})
            corrected_tokens.append(top[0] if top else (ded if ded != tok else tok))
        corrected_text = ' '.join(corrected_tokens)
    stages['tokenize_spell'] = {'ms': t['ms'], 'tokens': tokens, 'corrections': corrections, 'corrected_text': corrected_text}

    # Sentence correction (rule-based)
    with sc_timer() as st:
        sent_corr = sentence_correct(corrected_tokens)
    stages['sentence'] = {'ms': st['ms'], 'corrected': sent_corr}

    # Intent detection
    with timer() as t:
        intent = detect_intent(corrected_text)
    stages['intent'] = {'ms': t['ms'], 'intent': intent}

    # Retrieval
    retrieved = []
    with timer() as t:
        if do_retrieve:
            retrieved = index.search_all(corrected_text)
        else:
            retrieved = []
    stages['retrieval'] = {'ms': t['ms'], 'docs': retrieved}

    # Prefer sentence-corrected text (if available) for the assistant reply
    display_text = sent_corr if sent_corr else corrected_text

    # Prepare reply (show the sentence-corrected version)
    reply = f"Intent={intent}; Found docs={retrieved}; You said: {display_text}"

    # Append to memory
    mem.add('user', text)
    mem.add('assistant', reply)

    # Frequency-based online learning: only persist tokens once seen >= THRESHOLD times
    learned = []
    try:
        import time, json
        toks = tokenize(text)
        THRESHOLD = 2
        for tok in set(toks):
            if len(tok) < 3:
                continue
            if tok in Dictionary:
                continue
            if not any(c.isalpha() for c in tok):
                continue

            # increment count
            prev = int(USER_COUNTS.get(tok, 0))
            USER_COUNTS[tok] = prev + 1

            # only accept token once threshold reached
            if USER_COUNTS[tok] >= THRESHOLD:
                # add to dictionary and bk-tree and inverted index
                Dictionary.add(tok)
                bk.add(tok)
                doc_id = f'user_msg_{int(time.time()*1000)}_{tok}'
                index.add_doc(doc_id, tok)
                learned.append(tok)
                # persist durable list
                try:
                    with open(USER_LEARN_PATH, 'a', encoding='utf-8') as uf:
                        uf.write(tok + '\n')
                except Exception:
                    pass

        # persist counts
        try:
            with open(USER_COUNTS_PATH, 'w', encoding='utf-8') as cf:
                json.dump(USER_COUNTS, cf, indent=2)
        except Exception:
            pass
    except Exception:
        learned = []

    res = {
        'stages': stages,
        'reply': reply,
        'memory': mem.as_list(),
        'learned': learned,
    }
    return jsonify(res)


if __name__ == '__main__':
    load_resources()
    app.run(host='127.0.0.1', port=5000, debug=True)
