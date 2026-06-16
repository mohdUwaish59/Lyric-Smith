"""
rhyme.py — Rhyme detection and rhyme-scheme validation (feature 1).

Approach:
  - The "rhyme key" of a word is the portion of its pronunciation from the
    last stressed vowel to the end (the standard definition of a perfect
    rhyme nucleus + coda). Two line endings rhyme if they share a rhyme key.
  - A rhyme scheme like "ABBA" requires: lines mapped to the same letter
    rhyme; lines mapped to different letters should NOT rhyme (optional check).
"""

from .phonetics import analyze_word, tokenize

_VOWEL_PHONEMES = {
    "AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY",
    "IH", "IY", "OW", "OY", "UH", "UW",
}


def _rhyme_key_from_phones(phones: str):
    """Given a CMU phone string, return the rhyme key: phonemes from the last
    stressed (1) vowel onward, stripped of stress digits. Falls back to the
    last vowel if no primary stress is marked."""
    parts = phones.split()
    last_stressed_idx = None
    last_vowel_idx = None
    for i, ph in enumerate(parts):
        base = ph.rstrip("012")
        if base in _VOWEL_PHONEMES:
            last_vowel_idx = i
            if ph.endswith("1"):
                last_stressed_idx = i
    start = last_stressed_idx if last_stressed_idx is not None else last_vowel_idx
    if start is None:
        return None
    tail = parts[start:]
    return " ".join(p.rstrip("012") for p in tail)


def rhyme_keys_for_word(word: str):
    """All rhyme keys for a word (one per pronunciation variant).

    For OOV words (no phones), returns [] — rhyme cannot be verified."""
    wa = analyze_word(word)
    keys = set()
    for phones in wa.phones_variants:
        k = _rhyme_key_from_phones(phones)
        if k:
            keys.add(k)
    return keys


def last_word(line: str):
    toks = tokenize(line)
    return toks[-1] if toks else None


def words_rhyme(line_a: str, line_b: str):
    """Return (rhymes: bool, verifiable: bool).

    rhymes is True if any pronunciation of the two end-words shares a rhyme
    key. verifiable is False if either end-word is OOV (no phones)."""
    wa, wb = last_word(line_a), last_word(line_b)
    if not wa or not wb:
        return False, False
    ka, kb = rhyme_keys_for_word(wa), rhyme_keys_for_word(wb)
    if not ka or not kb:
        return False, False           # at least one OOV -> unverifiable
    # identity (same word) is usually NOT considered a true rhyme in songwriting
    if wa.lower() == wb.lower():
        return False, True
    return bool(ka & kb), True


def validate_scheme(lines, scheme, check_distinct=True):
    """Validate a list of lines against a rhyme scheme string.

    lines:  list[str], one per scheme position
    scheme: str like "ABBA" (case-insensitive); same letter -> must rhyme.
            Use "." or "-" for a line with no rhyme constraint.
    check_distinct: if True, lines with DIFFERENT letters must NOT rhyme.

    Returns dict: { ok, groups, violations[], unverifiable[] }.
    """
    scheme = scheme.strip().upper()
    if len(scheme) != len(lines):
        raise ValueError(
            f"Scheme length ({len(scheme)}) != number of lines ({len(lines)})"
        )

    groups = {}
    for letter, line in zip(scheme, lines):
        if letter in ".-":
            continue
        groups.setdefault(letter, []).append(line)

    violations, unverifiable = [], []

    # Within-group: every pair must rhyme.
    for letter, grp in groups.items():
        for i in range(len(grp)):
            for j in range(i + 1, len(grp)):
                rhymes, verifiable = words_rhyme(grp[i], grp[j])
                end_i, end_j = last_word(grp[i]), last_word(grp[j])
                if not verifiable:
                    unverifiable.append(
                        f"'{end_i}' / '{end_j}' (group {letter}): contains "
                        f"out-of-vocabulary word; rhyme not verifiable")
                elif not rhymes:
                    violations.append(
                        f"'{end_i}' and '{end_j}' (group {letter}) do not rhyme")

    # Across-group: different letters should NOT rhyme (optional).
    if check_distinct:
        letters = [l for l in groups]
        reps = {l: groups[l][0] for l in letters}
        for a in range(len(letters)):
            for b in range(a + 1, len(letters)):
                la, lb = letters[a], letters[b]
                rhymes, verifiable = words_rhyme(reps[la], reps[lb])
                if verifiable and rhymes:
                    violations.append(
                        f"groups {la} and {lb} rhyme but should be distinct "
                        f"('{last_word(reps[la])}' / '{last_word(reps[lb])}')")

    return {
        "ok": not violations,
        "groups": {k: [last_word(x) for x in v] for k, v in groups.items()},
        "violations": violations,
        "unverifiable": unverifiable,
    }
