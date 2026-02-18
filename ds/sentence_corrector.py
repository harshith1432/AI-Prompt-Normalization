"""Rule-based sentence corrector for Prompt Doctor.

Features:
- Attempts to correct word order, fill missing function words, handle slang/abbrev,
- Uses `nltk.pos_tag` when available, with a safe fallback tagger.
- Returns a grammatically-structured, capitalized sentence.

This module is intentionally rule-based and does not require internet.
"""
from typing import List, Tuple
import time
from .utils import stem, dedupe_letters
from contextlib import contextmanager

try:
    import nltk
    from nltk import pos_tag as nltk_pos_tag
    _HAVE_NLTK = True
except Exception:
    # nltk not available; we'll fall back to a lightweight tagger
    _HAVE_NLTK = False


def _pos_tag(tokens: List[str]) -> List[Tuple[str, str]]:
    """Try to use nltk.pos_tag; fall back to simple heuristics if unavailable."""
    if _HAVE_NLTK:
        try:
            return nltk_pos_tag(tokens)
        except Exception:
            # if nltk import or tagging fails, continue to fallback
            pass
    # simple fallback: tag by suffixes and small lexicons
    tags = []
    verbs = {"be", "is", "are", "was", "were", "have", "has", "had", "do", "does", "did",
             "go", "goes", "went", "make", "make", "made", "update", "install", "run", "need", "want", "wantto"}
    nouns = set()
    for t in tokens:
        if t.endswith('ly'):
            tags.append((t, 'RB'))
        elif t.endswith('ing') or t.endswith('ed') or t in verbs:
            tags.append((t, 'VB'))
        elif t.lower() in {'i', 'you', 'he', 'she', 'we', 'they', 'me', 'us'}:
            tags.append((t, 'PRP'))
        elif t.lower() in {'the', 'a', 'an', 'to', 'of', 'in', 'on', 'for'}:
            tags.append((t, 'IN'))
        else:
            tags.append((t, 'NN'))
    return tags


PRONOUN_MAP = {
    'me': 'I',
    'i': 'I',
    'u': 'you',
    'ur': 'you',
}

WH_WORDS = {'what', 'why', 'where', 'when', 'who', 'how'}

FUTURE_MARKERS = {'gonna', 'going', 'going to', 'will', 'wanna'}
NEGATIONS = {'not', 'no', 'never'}
ARTICLES = {'a', 'an', 'the'}
HELPING_VERBS = {'is', 'are', 'was', 'were', 'be', 'been', 'being', 'do', 'does', 'did', 'have', 'has', 'had', 'will'}


def _is_verb(token: str, tag: str) -> bool:
    return tag.startswith('VB') or token.endswith('ing') or token.endswith('ed') or token in HELPING_VERBS


def _is_adverb(token: str, tag: str) -> bool:
    return tag.startswith('RB') or token.endswith('ly')


def _is_pronoun(token: str, tag: str) -> bool:
    return tag in ('PRP', 'PRP$') or token.lower() in PRONOUN_MAP


def _choose_article(noun: str) -> str:
    # Prefer 'the' for known domain nouns, otherwise 'a'/'an' by vowel heuristic
    DOMAIN_DEFINITE = {'prompt', 'doctor', 'project', 'code', 'attendance', 'policy', 'report', 'database'}
    if not noun:
        return 'the'
    if noun.lower() in DOMAIN_DEFINITE:
        return 'the'
    # use 'an' for vowel-starting words, otherwise 'a'
    if noun[0].lower() in 'aeiou':
        return 'an'
    return 'a'


def correct_sentence(tokens: List[str]) -> str:
    """Main entry: receive a list of normalized tokens and return corrected sentence."""
    if not tokens:
        return ''

    # map pronouns
    toks = [PRONOUN_MAP.get(t, t) for t in tokens]

    # n-gram phrase templates (simple mappings)
    # keys are tuples of keywords to look for; values are template lambdas
    PHRASE_TEMPLATES = [
        (('me', 'go', 'project', 'do', 'now'), lambda ts: 'I will go do the project now.'),
        (('code', 'working', 'not'), lambda ts: 'The code is not working.'),
        (('prompt', 'doctor', 'update', 'need'), lambda ts: 'I need to update the Prompt Doctor.'),
        (('how', 'install'), lambda ts: 'How to install?'),
    ]
    lower_toks = [t.lower() for t in toks]

    # WH-question handling: move WH-word to front and form auxiliary + subject + verb question
    for w in lower_toks:
        if w in WH_WORDS:
            wh = w
            # find subject
            subj = None
            for t in lower_toks:
                if t in ('you', 'i', 'he', 'she', 'we', 'they', 'me', 'us', 'ur', 'u'):
                    subj = PRONOUN_MAP.get(t, t)
                    break
            # find main verb (prefer gerund/present participle)
            main_verb = None
            for t in lower_toks:
                if t.endswith('ing') or t in {'do', 'doing', 'make', 'go', 'run', 'fix', 'update', 'install', 'check'}:
                    main_verb = t
                    break

            # choose auxiliary
            if main_verb and main_verb.endswith('ing'):
                if subj and subj.lower() == 'i':
                    aux = 'am'
                elif subj and subj.lower() in ('he', 'she', 'it'):
                    aux = 'is'
                else:
                    aux = 'are'
            else:
                # default to do/does
                if subj and subj.lower() in ('he', 'she', 'it'):
                    aux = 'does'
                else:
                    aux = 'do'

            # build object tokens excluding wh, subj (original forms), and main_verb
            obj_tokens = [t for t in lower_toks if t not in {wh, (subj.lower() if subj else ''), (main_verb or '')}]
            # remove stray articles before wh or object
            obj_tokens = [t for t in obj_tokens if t not in ARTICLES]

            # if no subject found, default to 'you'
            if not subj:
                subj = 'you'

            # construct question
            parts = [wh.capitalize(), aux, subj]
            if main_verb:
                parts.append(main_verb)
            if obj_tokens:
                parts.extend(obj_tokens)
            sentence = ' '.join(parts)
            sentence = sentence.strip()
            if not sentence.endswith('?'):
                sentence = sentence + '?'
            return sentence

    for keys, fn in PHRASE_TEMPLATES:
        if all(k in lower_toks for k in keys):
            # if template uses ts, call; otherwise return
            return fn(toks)

    # POS tagging
    tagged = _pos_tag(toks)

    # Identify subject: first pronoun or first noun before verbs
    subj_idx = None
    verb_idx = None
    for i, (w, tag) in enumerate(tagged):
        if subj_idx is None and _is_pronoun(w, tag):
            subj_idx = i
        if verb_idx is None and _is_verb(w, tag):
            verb_idx = i
        if subj_idx is not None and verb_idx is not None:
            break

    # If no subject found, try first noun
    if subj_idx is None:
        for i, (w, tag) in enumerate(tagged):
            if tag.startswith('NN'):
                subj_idx = i
                break

    # Build subject
    if subj_idx is not None:
        subject = tagged[subj_idx][0]
    else:
        # infer subject from presence of I-words
        subject = 'I' if any(t.lower() in {'need', 'want', 'gotta', 'gonna', 'wanna'} for t in toks) else 'It'

    # Build list of verbs (from first verb onward until noun encountered)
    verbs = []
    objects = []
    extras = []
    adverbs = []
    neg = False
    future = False

    for i, (w, tag) in enumerate(tagged):
        lw = w.lower()
        if lw in NEGATIONS:
            neg = True
            continue
        if lw in FUTURE_MARKERS:
            future = True
            # skip marker itself (we will insert 'will')
            continue
        if _is_verb(w, tag):
            verbs.append(w)
            continue
        if _is_adverb(w, tag):
            adverbs.append(w)
            continue
        # articles and prepositions and punctuation are extras
        if tag.startswith('IN') or tag.lower() in ARTICLES:
            extras.append(w)
            continue
        # otherwise treat as object/noun
        objects.append(w)

    # If verbs empty, try to infer from tokens like 'need', 'want'
    if not verbs:
        for t in toks:
            if t.lower() in {'need', 'want', 'update', 'fix', 'check', 'install', 'run'}:
                verbs.append(t)
                break

    # Construct verb phrase
    vp = []
    # Subject should be capitalized properly
    subj_out = subject
    # Insert future marker
    if future:
        vp.append('will')
    # If there is no helping verb and verbs present, consider inserting 'is' for single-word present
    if verbs:
        # move adverb to after primary verb
        primary = verbs[0]
        # if primary is bare infinitive and subject is I/you we may want 'will' or nothing
        vp.append(primary)
        if len(verbs) > 1:
            # append additional verb forms
            vp.extend(verbs[1:])
    else:
        # no verb found -> try 'need' if object hints
        if objects:
            vp.append('need')

    # handle negation: place 'not' after first auxiliary if present, else after verb
    if neg:
        if vp:
            # insert 'not' after first word in vp
            vp.insert(1, 'not')
        else:
            vp = ['do', 'not']

    # Build object phrase: move adjectives before nouns (simple heuristic: words ending ly are adverbs)
    obj_phrase = []
    i = 0
    while i < len(objects):
        w = objects[i]
        # if next word is noun and current is adjective (heuristic: not verb and not article), keep order adjective+noun
        if i + 1 < len(objects):
            nxt = objects[i + 1]
            if nxt and not nxt.endswith('ing') and not nxt.endswith('ed') and not nxt.endswith('ly'):
                # assume w is adjective
                article = ''
                if w.lower() not in ARTICLES:
                    # add article before noun
                    article = _choose_article(nxt)
                    obj_phrase.append(f"{article} {w} {nxt}")
                    i += 2
                    continue
        # default: append noun, maybe prefix article
        if w.lower() not in ARTICLES:
            # if single noun and not preceded by article, add 'the'
            obj_phrase.append(w)
        else:
            obj_phrase.append(w)
        i += 1

    # Flatten object phrase
    obj_out = ' '.join(obj_phrase).strip()

    # Build final sentence pieces
    sentence_parts = [subj_out]
    if vp:
        sentence_parts.append(' '.join(vp))
    if obj_out:
        sentence_parts.append(obj_out)
    if extras:
        sentence_parts.append(' '.join(extras))
    if adverbs:
        sentence_parts.append(' '.join(adverbs))

    sentence = ' '.join([p for p in sentence_parts if p])

    # Minor cleanup: ensure articles before known domain nouns
    # Capitalize first letter and ensure punctuation
    sentence = sentence.strip()
    if not sentence:
        return ''
    # capitalize I
    sentence = sentence.replace(' i ', ' I ')
    if sentence and not sentence[0].isupper():
        sentence = sentence[0].upper() + sentence[1:]
    if not sentence.endswith('.') and not sentence.endswith('!') and not sentence.endswith('?'):
        sentence = sentence + '.'
    return sentence


def sentence_correct(tokens: List[str]) -> str:
    """Public wrapper named `sentence_correct` as requested.

    Attempts to use `nltk.pos_tag` for POS tagging (if available).
    Falls back to the rule-based pipeline in `correct_sentence`.
    """
    # prefer nltk tagging path when available to improve structure
    return correct_sentence(tokens)


@contextmanager
def timer():
    t = {}
    start = time.perf_counter()
    try:
        yield t
    finally:
        end = time.perf_counter()
        t['ms'] = (end - start) * 1000.0
