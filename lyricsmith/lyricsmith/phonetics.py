"""
phonetics.py — Phonetic analysis layer.

Responsibilities:
  - Look up word pronunciations (CMU Pronouncing Dictionary, with an embedded
    fallback so the package runs offline).
  - Normalize/expand contractions and handle apostrophes.
  - Extract per-syllable stress strings.
  - Provide a grapheme-to-phoneme (G2P) fallback so out-of-vocabulary words
    (names, slang, neologisms) get a best-effort syllable count AND stress
    guess instead of failing silently.
  - Expose rhyme keys (used by rhyme.py).

Stress digits follow CMU convention: 1 = primary, 2 = secondary, 0 = unstressed.
"""

import re

# --------------------------------------------------------------------------
# Dictionary backend
# --------------------------------------------------------------------------

try:
    import pronouncing

    def _raw_phones(word: str):
        return pronouncing.phones_for_word(word.lower())

    DICT_SOURCE = "CMU Pronouncing Dictionary (pronouncing)"
    HAVE_CMU = True
except ImportError:
    # Minimal embedded fallback so demos/tests run with no network or install.
    _FALLBACK = {
        "a": ["AH0"], "the": ["DH AH0"], "and": ["AH0 N D"], "in": ["IH0 N"],
        "his": ["HH IH1 Z"], "her": ["HH ER0"], "at": ["AE1 T"], "of": ["AH0 V"],
        "to": ["T UW1"], "i": ["AY1"], "is": ["IH1 Z"], "on": ["AA1 N"],
        "by": ["B AY1"], "no": ["N OW1"], "so": ["S OW1"], "now": ["N AW1"],
        "little": ["L IH1 T AH0 L"], "boy": ["B OY1"], "girl": ["G ER1 L"],
        "alone": ["AH0 L OW1 N"], "asleep": ["AH0 S L IY1 P"],
        "night": ["N AY1 T"], "light": ["L AY1 T"], "bright": ["B R AY1 T"],
        "room": ["R UW1 M"], "quiet": ["K W AY1 AH0 T"],
        "bedroom": ["B EH1 D R UW2 M"], "shadows": ["SH AE1 D OW0 Z"],
        "shadow": ["SH AE1 D OW0"], "window": ["W IH1 N D OW0"],
        "moonlight": ["M UW1 N L AY2 T"], "sleeping": ["S L IY1 P IH0 NG"],
        "softly": ["S AO1 F T L IY0"], "dreams": ["D R IY1 M Z"],
        "dream": ["D R IY1 M"], "lies": ["L AY1 Z"], "still": ["S T IH1 L"],
        "silver": ["S IH1 L V ER0"], "falls": ["F AO1 L Z"],
        "across": ["AH0 K R AO1 S"], "floor": ["F L AO1 R"],
        "door": ["D AO1 R"], "more": ["M AO1 R"],
        "stars": ["S T AA1 R Z"], "keep": ["K IY1 P"], "deep": ["D IY1 P"],
        "watch": ["W AA1 CH"], "above": ["AH0 B AH1 V"], "love": ["L AH1 V"],
        "record": ["R EH1 K ER0 D", "R IH0 K AO1 R D"],
        "beautiful": ["B Y UW1 T AH0 F AH0 L"],
        "every": ["EH1 V ER0 IY0", "EH1 V R IY0"],
        "heart": ["HH AA1 R T"], "beats": ["B IY1 T S"], "beat": ["B IY1 T"],
        "slow": ["S L OW1"], "world": ["W ER1 L D"],
        "outside": ["AW1 T S AY1 D", "AW0 T S AY1 D"],
        "fades": ["F EY1 D Z"], "away": ["AH0 W EY1"], "day": ["D EY1"],
        "whisper": ["W IH1 S P ER0"], "drifting": ["D R IH1 F T IH0 NG"],
        "through": ["TH R UW1"], "dark": ["D AA1 R K"],
        "beneath": ["B IH0 N IY1 TH"], "silent": ["S AY1 L AH0 N T"],
        "winter": ["W IH1 N T ER0"], "sky": ["S K AY1"], "high": ["HH AY1"],
        "cold": ["K OW1 L D"], "hold": ["HH OW1 L D"], "old": ["OW1 L D"],
        "wonderful": ["W AH1 N D ER0 F AH0 L"],
        "memories": ["M EH1 M ER0 IY0 Z"],
        "surround": ["S ER0 AW1 N D"], "him": ["HH IH1 M"],
        "tonight": ["T AH0 N AY1 T"], "moon": ["M UW1 N"],
        "small": ["S M AO1 L"], "tall": ["T AO1 L"], "wall": ["W AO1 L"],
        "eyes": ["AY1 Z"], "skies": ["S K AY1 Z"], "cries": ["K R AY1 Z"],
        "close": ["K L OW1 Z", "K L OW1 S"], "sound": ["S AW1 N D"],
        "ground": ["G R AW1 N D"], "found": ["F AW1 N D"],
        "fear": ["F IH1 R"], "near": ["N IH1 R"], "tear": ["T IH1 R", "T EH1 R"],
        "warm": ["W AO1 R M"], "storm": ["S T AO1 R M"],
        "don't": ["D OW1 N T"], "can't": ["K AE1 N T"],
        "won't": ["W OW1 N T"], "i'm": ["AY1 M"], "it's": ["IH1 T S"],
    }

    def _raw_phones(word: str):
        return list(_FALLBACK.get(word.lower(), []))

    DICT_SOURCE = "embedded fallback dictionary (install 'pronouncing' for full coverage)"
    HAVE_CMU = False


# --------------------------------------------------------------------------
# Contractions & normalization
# --------------------------------------------------------------------------

# Contractions whose pronunciation may not be in the dictionary; we map them
# to either a single dictionary key or an expansion that is.
_CONTRACTION_EXPAND = {
    "don't": "dont", "won't": "wont", "can't": "cant", "i'm": "im",
    "it's": "its", "he's": "hes", "she's": "shes", "that's": "thats",
    "there's": "theres", "what's": "whats", "let's": "lets",
    "i've": "ive", "we've": "weve", "they've": "theyve",
    "i'll": "ill", "we'll": "well", "you'll": "youll", "they'll": "theyll",
    "i'd": "id", "we'd": "wed", "you'd": "youd", "they'd": "theyd",
    "you're": "youre", "we're": "were", "they're": "theyre",
    "isn't": "isnt", "aren't": "arent", "wasn't": "wasnt",
    "weren't": "werent", "didn't": "didnt", "doesn't": "doesnt",
    "wouldn't": "wouldnt", "couldn't": "couldnt", "shouldn't": "shouldnt",
}

# Common "-in'" colloquial endings -> "-ing" so the dictionary resolves them.
def _normalize_word(word: str):
    """Return a list of candidate dictionary lookups for a raw token,
    in priority order."""
    w = word.lower().strip()
    cands = [w]
    if w in _CONTRACTION_EXPAND:
        cands.append(_CONTRACTION_EXPAND[w])
    # lovin' -> loving, runnin' -> running
    if w.endswith("in'"):
        cands.append(w[:-2] + "g")   # in' -> ing
    # strip a trailing possessive/clipped apostrophe: rock'n -> rockn? skip
    if w.endswith("'"):
        cands.append(w[:-1])
    # 'cause -> cause, 'round -> round
    if w.startswith("'"):
        cands.append(w[1:])
    return cands


def tokenize(line: str):
    """Split a lyric line into word tokens, keeping internal apostrophes."""
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?'?", line)


# --------------------------------------------------------------------------
# Stress extraction
# --------------------------------------------------------------------------

def stress_string(phones: str) -> str:
    """'L IH1 T AH0 L' -> '10'."""
    return "".join(ch for ch in phones if ch.isdigit())


# --------------------------------------------------------------------------
# G2P fallback for out-of-vocabulary words
# --------------------------------------------------------------------------

_VOWELS = "aeiouy"


def _syllabify_count(word: str) -> int:
    """Estimate syllable count by counting vowel groups, with silent-e rule."""
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 1
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups)
    # silent final 'e' (rule of thumb), but not for -le, -ee, -ie, -ye
    if w.endswith("e") and n > 1 and not w.endswith(("le", "ee", "ie", "ye", "ue")):
        n -= 1
    return max(1, n)


def g2p_stress_guess(word: str) -> str:
    """Best-effort stress pattern for an OOV word.

    Heuristic: single syllable -> '1'. Multi-syllable -> primary stress on the
    first syllable by default (the most common English pattern for content
    words), everything else unstressed. This is intentionally simple and
    marked low-confidence; a neural G2P model can be dropped in later behind
    this same function signature.
    """
    n = _syllabify_count(word)
    if n <= 1:
        return "1"
    return "1" + "0" * (n - 1)


# --------------------------------------------------------------------------
# Neural G2P backend (g2p_en) — predicts real phonemes for OOV words
# --------------------------------------------------------------------------

_G2P = None
_G2P_TRIED = False
_ARPABET_RE = re.compile(r"^[A-Z]{1,3}[0-2]?$")


def _get_g2p():
    """Lazily load g2p_en.G2p() once (it loads a model + nltk data)."""
    global _G2P, _G2P_TRIED
    if _G2P_TRIED:
        return _G2P
    _G2P_TRIED = True
    try:
        from g2p_en import G2p
        _G2P = G2p()
    except Exception:
        _G2P = None      # not installed / failed to load -> heuristic fallback
    return _G2P


def g2p_phones(word: str):
    """Predict a CMU-style phone string for an OOV word using g2p_en.

    Returns e.g. 'AA2 L IY1 AA0' for 'Aaliyah', or None if g2p_en is
    unavailable. Because the output is real ARPAbet with stress digits, the
    word becomes both stress-checkable AND rhyme-checkable.
    """
    g2p = _get_g2p()
    if g2p is None:
        return None
    clean = re.sub(r"[^A-Za-z']", "", word)
    if not clean:
        return None
    try:
        toks = g2p(clean)
    except Exception:
        return None
    phs = [t for t in toks if _ARPABET_RE.match(t)]
    return " ".join(phs) if phs else None


# --------------------------------------------------------------------------
# Public word analysis
# --------------------------------------------------------------------------

class WordAnalysis:
    """Phonetic analysis of a single token."""

    __slots__ = ("token", "lookup", "stress_variants", "phones_variants",
                 "known", "confidence")

    def __init__(self, token, lookup, stress_variants, phones_variants,
                 known, confidence):
        self.token = token
        self.lookup = lookup                  # dictionary key actually used
        self.stress_variants = stress_variants  # list[str], e.g. ['10', '01']
        self.phones_variants = phones_variants  # list[str] raw CMU phones
        self.known = known                    # bool: found in dictionary
        self.confidence = confidence          # 'high' | 'low'

    def syllable_counts(self):
        return sorted({len(s) for s in self.stress_variants})

    def __repr__(self):
        tag = "" if self.known else " (G2P)"
        return f"<{self.token}:{'/'.join(self.stress_variants)}{tag}>"


def analyze_word(token: str) -> WordAnalysis:
    """Analyze a token. Priority: dictionary -> neural G2P -> heuristic.

    confidence: 'high' (dictionary), 'medium' (g2p_en phonemes),
                'low' (vowel-count heuristic, no phonemes available).
    """
    # 1. Dictionary (with contraction/colloquial normalization).
    for lk in _normalize_word(token):
        prons = _raw_phones(lk)
        if prons:
            seen, sv, pv = set(), [], []
            for p in prons:
                s = stress_string(p)
                if s and s not in seen:
                    seen.add(s)
                    sv.append(s)
                    pv.append(p)
            return WordAnalysis(token, lk, sv, pv, known=True, confidence="high")

    # 2. Neural G2P (real phonemes -> stress AND rhyme verifiable).
    phones = g2p_phones(token)
    if phones:
        s = stress_string(phones)
        if s:
            return WordAnalysis(token, token.lower(), [s], [phones],
                                known=False, confidence="medium")

    # 3. Heuristic last resort (count only, no phonemes -> rhyme unverifiable).
    guess = g2p_stress_guess(token)
    return WordAnalysis(token, token.lower(), [guess], [], known=False,
                        confidence="low")


def analyze_line(line: str):
    """Return list[WordAnalysis] for a line."""
    return [analyze_word(t) for t in tokenize(line)]
