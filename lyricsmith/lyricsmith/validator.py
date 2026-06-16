"""
validator.py — Line and section validation.

Features:
  - Strictness levels (feature 5): STRICT / SUNG / LOOSE.
  - Near-miss scoring (feature 6): every line gets a numeric score and a list
    of concrete problems, so failures can be ranked and fed back to an LLM.
  - Multi-line section validation (feature 4): validate a whole verse against
    a template (per-line syllables + stress) AND a rhyme scheme in one call.

Status values: PASS, FAIL, UNVERIFIABLE.
"""

import itertools
from dataclasses import dataclass, field
from enum import Enum

from .phonetics import analyze_line
from .rhyme import validate_scheme


class Strictness(str, Enum):
    STRICT = "strict"   # every syllable must match template exactly
    SUNG = "sung"       # monosyllables + secondary stress flexible (default)
    LOOSE = "loose"     # only syllable COUNT is enforced; stress ignored


@dataclass
class LineSpec:
    """The formal requirement for one line."""
    syllables: int
    stress: str                 # template, len == syllables; chars 0/1/x
    rhyme_label: str = "."      # used only at section level

    def __post_init__(self):
        self.stress = self.stress.strip().lower()
        if len(self.stress) != self.syllables:
            raise ValueError(
                f"stress template '{self.stress}' length {len(self.stress)} "
                f"!= syllables {self.syllables}")


@dataclass
class LineResult:
    line: str
    status: str
    score: float                      # 0.0 = perfect, higher = worse
    problems: list = field(default_factory=list)
    chosen_combo: list = field(default_factory=list)   # stress per word
    oov: list = field(default_factory=list)

    @property
    def ok(self):
        return self.status == "PASS"


def _compatible(cmu_digit, template_char, monosyllabic, strictness):
    if template_char == "x":
        return True
    if strictness == Strictness.LOOSE:
        return True
    if strictness == Strictness.SUNG:
        if monosyllabic:
            return True
        if cmu_digit == "2":
            return True
    return cmu_digit == template_char


def validate_line(line, spec, strictness=Strictness.SUNG):
    """Validate a single line against a LineSpec. Returns LineResult."""
    if isinstance(spec, tuple):
        spec = LineSpec(spec[0], spec[1])
    words = analyze_line(line)
    oov = [w.token for w in words if not w.known]            # not in dictionary
    no_phones = [w.token for w in words if not w.phones_variants]  # truly unknown

    # Build per-word stress variant lists.
    variant_lists = [w.stress_variants for w in words]

    best = None  # (score, problems, combo)
    target = spec.syllables

    for combo in itertools.product(*variant_lists):
        line_stress = "".join(combo)
        problems = []
        score = 0.0

        # Syllable count check.
        diff = len(line_stress) - target
        if diff != 0:
            problems.append(
                f"syllable count {len(line_stress)} != target {target} "
                f"({'+' if diff > 0 else ''}{diff})")
            score += 10 * abs(diff)   # count errors dominate ranking
            if best is None or score < best[0]:
                best = (score, problems, combo)
            continue

        # Stress check (skipped entirely for LOOSE).
        if strictness != Strictness.LOOSE:
            i = 0
            for w, s in zip(words, combo):
                mono = len(s) == 1
                for digit in s:
                    if not _compatible(digit, spec.stress[i], mono, strictness):
                        has = "stress" if digit == "1" else "no stress"
                        want = spec.stress[i]
                        problems.append(
                            f"syllable {i+1} ('{w.token}'): has {has}, "
                            f"template wants '{want}'")
                        # low-confidence (G2P) mismatches penalized less
                        score += 0.5 if not w.known else 1.0
                    i += 1

        if not problems:
            status = "UNVERIFIABLE" if no_phones else "PASS"
            return LineResult(line, status, 0.0, [], list(combo), oov)

        if best is None or score < best[0]:
            best = (score, problems, combo)

    score, problems, combo = best
    status = "UNVERIFIABLE" if (no_phones and _only_unknown_problems(problems, words)) else "FAIL"
    return LineResult(line, status, score, problems, list(combo), oov)


def _only_unknown_problems(problems, words):
    """True if every problem stems from a phoneme-less (truly unknown) word, so
    the line is UNVERIFIABLE rather than a hard FAIL. Words resolved via g2p_en
    have phonemes and are treated as verifiable."""
    unknown = {w.token for w in words if not w.phones_variants}
    if not unknown:
        return False
    for p in problems:
        if p.startswith("syllable count"):
            return False              # structural error -> real FAIL
        if "('" in p:
            tok = p.split("('")[1].split("')")[0]
            if tok not in unknown:
                return False          # a known/g2p word mismatched -> real FAIL
    return True


@dataclass
class SectionResult:
    line_results: list
    rhyme: dict
    status: str        # PASS / FAIL / UNVERIFIABLE

    @property
    def ok(self):
        return self.status == "PASS"


def validate_section(lines, specs, rhyme_scheme=None,
                     strictness=Strictness.SUNG, check_distinct_rhymes=True):
    """Validate a full section (feature 4).

    lines: list[str]
    specs: list[LineSpec] (or (syllables, stress) tuples), same length
    rhyme_scheme: optional str (e.g. 'ABBA'); if None, derived from specs'
                  rhyme_label fields when present.
    """
    if len(lines) != len(specs):
        raise ValueError("lines and specs must be the same length")
    specs = [s if isinstance(s, LineSpec) else LineSpec(s[0], s[1]) for s in specs]

    line_results = [validate_line(l, s, strictness) for l, s in zip(lines, specs)]

    rhyme = None
    if rhyme_scheme is None and any(s.rhyme_label not in ".-" for s in specs):
        rhyme_scheme = "".join(s.rhyme_label for s in specs)
    if rhyme_scheme:
        rhyme = validate_scheme(lines, rhyme_scheme,
                                check_distinct=check_distinct_rhymes)

    # Aggregate status.
    statuses = {r.status for r in line_results}
    if rhyme and rhyme["violations"]:
        status = "FAIL"
    elif "FAIL" in statuses:
        status = "FAIL"
    elif "UNVERIFIABLE" in statuses or (rhyme and rhyme["unverifiable"]):
        status = "UNVERIFIABLE"
    else:
        status = "PASS"

    return SectionResult(line_results, rhyme or {}, status)
