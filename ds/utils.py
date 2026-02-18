import re
import time
from contextlib import contextmanager

ABBREVIATIONS = {
    # pronouns / short words
    "u": "you",
    "ur": "your",
    "urs": "yours",
    "r": "are",
    "y": "why",
    "ya": "you",
    "yall": "you all",
    "y'all": "you all",

    # polite / common phrases
    "pls": "please",
    "plz": "please",
    "thx": "thanks",
    "tx": "thanks",
    "ty": "thank you",
    "tyvm": "thank you very much",
    "tysm": "thank you so much",
    "yw": "you're welcome",
    "np": "no problem",
    "sry": "sorry",
    "soz": "sorry",
    "kk": "okay",

    # internet/chat slang
    "lol": "laughing out loud",
    "lmao": "laughing my ass off",
    "rofl": "rolling on the floor laughing",
    "jk": "just kidding",
    "omg": "oh my god",
    "wtf": "what the heck",
    "wth": "what the heck",
    "brb": "be right back",
    "bbl": "be back later",
    "gtg": "got to go",
    "g2g": "got to go",
    "ttyl": "talk to you later",
    "ttfn": "ta ta for now",
    "imo": "in my opinion",
    "imho": "in my humble opinion",
    "fyi": "for your information",
    "asap": "as soon as possible",
    "afaik": "as far as i know",
    "irl": "in real life",

    # common short forms
    "idk": "i don't know",
    "idc": "i don't care",
    "ikr": "i know right",
    "tbqh": "to be quite honest",
    "tbh": "to be honest",
    "omw": "on my way",
    "nvm": "never mind",
    "bruh": "bro",

    # abbreviations for time/date
    "tmrw": "tomorrow",
    "2moro": "tomorrow",
    "2day": "today",
    "tdy": "today",
    "2nite": "tonight",
    "l8r": "later",
    "b4": "before",

    # numbers/text shorthand
    "gr8": "great",
    "bday": "birthday",
    "plzrd": "please regard",

    # directions / short commands
    "re": "regarding",
    "cc": "carbon copy",
    "pk": "player kill",

    # modal verbs / contractions (typed without apostrophes often)
    "im": "i am",
    "ive": "i have",
    "id": "i would",
    "dont": "do not",
    "cant": "cannot",
    "wont": "will not",
    "couldnt": "could not",
    "shouldnt": "should not",
    "wouldnt": "would not",

    # common conversational shortenings
    "gonna": "going to",
    "wanna": "want to",
    "gotta": "got to",
    "hafta": "have to",
    "kinda": "kind of",
    "sorta": "sort of",
    "lemme": "let me",
    "gimme": "give me",

    # cause / because variants
    "cuz": "because",
    "cuz/" : "because",
    "bcoz": "because",
    "bc": "because",

    # affirmations / negatives
    "ya": "yes",
    "yah": "yes",
    "yep": "yes",
    "yup": "yes",
    "nah": "no",
    "nope": "no",

    # email / org / misc
    "addr": "address",
    "msg": "message",
    "msgs": "messages",
    "info": "information",
    "cfg": "configuration",
    "config": "configuration",

    # computing / tech shorthand
    "db": "database",
    "srv": "server",
    "svc": "service",
    "ui": "user interface",
    "ux": "user experience",
    "api": "application programming interface",
    "repo": "repository",
    "dev": "developer",
    "prod": "production",
    "stg": "staging",

    # meeting / collaboration
    "appt": "appointment",
    "mtg": "meeting",
    "min": "minutes",
    "hrs": "hours",

    # education / attendance domain additions
    "attn": "attendance",
    "attend": "attend",
    "attended": "attended",
    "abs": "absent",
    "absent": "absent",
    "stud": "student",
    "inst": "instructor",
    "prof": "professor",
    "sec": "section",
    "sem": "semester",

    # common verbs / short forms
    "chk": "check",
    "checkin": "check in",
    "checkout": "check out",
    "reg": "register",
    "regd": "registered",

    # common web/chat shortcuts
    "plsplz": "please",
    "thnx": "thanks",
    "tnx": "thanks",

    # misc casual words
    "tho": "though",
    "cos": "because",
    "cya": "see you",
    "ttys": "talk to you soon",

    # keyboard typos / common alternate spellings
    "teh": "the",
    "recieve": "receive",
    "adress": "address",
    "definately": "definitely",
    "seperate": "separate",

    # support / help
    "faq": "frequently asked questions",
    "helpdesk": "help desk",
    "support": "support",

    # finance / penalties domain
    "fine": "fine",
    "pen": "penalty",

    # short phrases
    "howto": "how to",
    "setup": "set up",
    "install": "install",
    "run": "run",

    # file / document
    "doc": "document",
    "docs": "documents",
    "readme": "read me",

    # misc contractions without apostrophes commonly typed
    "hes": "he is",
    "shes": "she is",
    "theyre": "they are",
    "were": "we are",

    # plural / simple typo corrections
    "reports": "report",
    "reporting": "report",
    "logins": "login",

    # polite closings
    "regards": "regards",
    "cheers": "cheers",

    # add several more short forms and common internet acronyms
    "nb": "nota bene",
    "imo": "in my opinion",
    "fomo": "fear of missing out",
    "tbd": "to be decided",
    "tba": "to be announced",
    "eta": "estimated time of arrival",
    "poc": "point of contact",
    "pto": "paid time off",

    # extra polite / filler phrases
    "plshelp": "please help",
    "plsadvise": "please advise",

    # short manual convenience mappings
    "cmd": "command",
    "usr": "user",
    "pwd": "password",
    "passwd": "password",

    # extended casual forms
    "wat": "what",
    "wot": "what",
    "wanna": "want to",
    "gonna": "going to",
    "lemme": "let me",

    # filler and emphasis
    "obvs": "obviously",
    "totes": "totally",
    "lolz": "laughing out loud",

    # keep a few domain-specific short forms
    "hallticket": "hall ticket",
    "invig": "invigilator",
    "invigilation": "invigilation",
    
        # Basic shortcuts
    "u": "you",
    "ur": "your",
    "urs": "yours",
    "r": "are",
    "wt": "what",
    "wat": "what",
    "wht": "what",
    "wats": "what is",
    "gonna": "going to",
    "wanna": "want to",
    "gotta": "got to",
    "cuz": "because",
    "bcoz": "because",
    "bcuz": "because",
    "becoz": "because",
    "pls": "please",
    "plz": "please",
    "plss": "please",
    "pzl": "please",

    # Your style mistakes (you ALWAYS type these 😭🔥)
    "giv": "give",
    "gimme": "give me",
    "givme": "give me",
    "broo": "bro",
    "bruhh": "bro",
    "brooo": "bro",
    "frnd": "friend",
    "frnds": "friends",
    "wrng": "wrong",
    "srsly": "seriously",
    "realy": "really",
    "rlly": "really",
    "tomm": "tomorrow",
    "tomo": "tomorrow",
    "tmrw": "tomorrow",
    "ystrday": "yesterday",
    "tday": "today",

    # Harshith typos (you type these 100% 😂)
    "undastand": "understand",
    "undestand": "understand",
    "undrstnd": "understand",
    "belve": "believe",
    "pleze": "please",
    "promant": "prompt",
    "promant": "prompt",
    "dout": "doubt",
    "abt": "about",
    "abt.": "about",
    "imprimpreshve": "impressive",
    "aplicatn": "application",
    "applctn": "application",
    "projct": "project",
    "projt": "project",
    "whch": "which",
    "wich": "which",
    "wichh": "which",
    "dsa": "data structures",
    "dasa": "data structures",

    # Kannada-English style (your vibe 😭🔥)
    "maga": "bro",
    "machaa": "bro",
    "macha": "bro",
    "kandaa": "bro",
    "lo": "bro",
    "da": "bro",
    "ene": "what",
    "yenu": "what",
    "gotilla": "don't know",
    "illa": "no",
    "haudu": "yes",
    "nodu": "see",
    "beka": "need",
    "beku": "need",
    "madno": "let's do",
    "madidya": "did you do",
    "madbeku": "need to do",

    # Chat slang
    "omg": "oh my god",
    "idk": "I don't know",
    "ikr": "I know right",
    "afaik": "as far as I know",
    "asap": "as soon as possible",
    "lol": "laughing",
    "lmao": "laughing",
    "tho": "though",
    "btw": "by the way",
    "ngl": "not gonna lie",

    # Soft corrections
    "u r": "you are",
    "u wanna": "you want to",
    "i wanna": "I want to",
    "i gonna": "I am going to",
}

# Fallback punctuation removal (compatible with Python's `re`)
FALLBACK_PUNCT_RE = re.compile(r"[^\w\s']+", re.UNICODE)


def normalize(text: str) -> str:
    """Lowercase, remove punctuation, expand common abbreviations."""
    if not text:
        return ""
    s = text.lower()
    # Replace common abbreviations as whole words
    for k, v in ABBREVIATIONS.items():
        s = re.sub(rf"\b{k}\b", v, s)
    # Attempt to remove punctuation; use fallback regex since \p{P} may not work
    s = FALLBACK_PUNCT_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def tokenize(text: str) -> list:
    """Normalize then split on whitespace."""
    n = normalize(text)
    if not n:
        return []
    # basic tokenization
    toks = n.split()
    # apply de-elongation per token (e.g., heeeyy -> heey)
    return [dedupe_letters(t) for t in toks]


def dedupe_letters(word: str, max_run: int = 2) -> str:
    """Reduce letter runs to at most `max_run` occurrences.

    Example: 'pleeeease' -> 'pleease' if max_run=2. This helps map elongated informal words
    to dictionary forms while preserving common double letters.
    """
    if not word:
        return word
    # replace any character that repeats 3 or more times with max_run occurrences
    def _repl(m):
        ch = m.group(1)
        return ch * max_run

    return re.sub(r"(.)\1{2,}", _repl, word)


def stem(word: str) -> str:
    """Lightweight stemming: remove common English suffixes.

    This is not a full Porter stemmer but helps map plural/inflected forms
    to a common root for matching and retrieval.
    """
    if not word:
        return word
    # order matters: longer suffixes first
    suffixes = ['ization', 'ations', 'ation', 'ingly', 'edly', 'ness', 'ment', 'able', 'ible', 'tion', 'sion', 'ing', 'ed', 'es', 's', 'ly']
    for suf in suffixes:
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            return word[: -len(suf)]
    return word


@contextmanager
def timer():
    """Context manager that yields a dict and sets the elapsed ms after exit.

    Usage:
        with timer() as t:
            do_work()
        print(t['ms'])
    """
    t = {}
    start = time.perf_counter()
    try:
        yield t
    finally:
        end = time.perf_counter()
        t['ms'] = (end - start) * 1000.0
