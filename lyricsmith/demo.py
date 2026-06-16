#!/usr/bin/env python3
"""
demo.py — Exercises features 1-10 end-to-end.

Run:
    python demo.py
Uses a deterministic mock LLM so it runs offline. Swap MockLLM for a real
client (see real_llm_example below) to use Anthropic/OpenAI.
"""

from lyricsmith import (
    LineSpec, Strictness,
    validate_line, validate_section, validate_scheme,
    generate_line, generate_section,
    MockLLM,
    DICT_SOURCE,
)


def hr(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# --------------------------------------------------------------------------
# Feature 5 + 6: strictness levels & near-miss scoring
# --------------------------------------------------------------------------
def demo_strictness_and_scoring():
    hr("FEATURES 5 & 6 — strictness levels + near-miss scoring")
    line = "The beautiful boy alone"          # 7 syllables vs target 8
    spec = LineSpec(8, "01010101")
    for level in (Strictness.STRICT, Strictness.SUNG, Strictness.LOOSE):
        r = validate_line(line, spec, level)
        print(f'\n[{level.value}] "{line}"  -> {r.status}  (score {r.score})')
        for p in r.problems:
            print(f"    - {p}")

    print("\nNear-miss ranking of three candidates (target 8, 01010101):")
    cands = [
        "The little boy asleep at night",   # perfect
        "The little boy is fast asleep",     # check
        "A boy alone",                       # too short
    ]
    scored = [(c, validate_line(c, spec, Strictness.SUNG)) for c in cands]
    scored.sort(key=lambda x: x[1].score)
    for c, r in scored:
        print(f"    score {r.score:5.1f}  {r.status:12}  {c}")


# --------------------------------------------------------------------------
# Feature 1: rhyme scheme validation
# --------------------------------------------------------------------------
def demo_rhyme():
    hr("FEATURE 1 — rhyme scheme validation (ABBA)")
    lines = [
        "The little boy asleep at night",   # A  night
        "Silver moonlight on the floor",     # B  floor
        "Shadows resting by the door",       # B  door
        "The stars above are shining bright" # A  bright
    ]
    res = validate_scheme(lines, "ABBA")
    print(f"Scheme ABBA -> ok={res['ok']}")
    print(f"  groups: {res['groups']}")
    for v in res["violations"]:
        print(f"  VIOLATION: {v}")
    for u in res["unverifiable"]:
        print(f"  unverifiable: {u}")

    print("\nA deliberately broken scheme (line 3 won't rhyme):")
    broken = lines[:2] + ["Shadows resting on the wall", lines[3]]
    res2 = validate_scheme(broken, "ABBA")
    print(f"  ok={res2['ok']}")
    for v in res2["violations"]:
        print(f"  VIOLATION: {v}")


# --------------------------------------------------------------------------
# Feature 4: multi-line section validation
# --------------------------------------------------------------------------
def demo_section():
    hr("FEATURE 4 — full section validation (syllables + stress + rhyme)")
    lines = [
        "The little boy asleep at night",
        "Silver moonlight on the floor",
        "Shadows resting by the door",
        "The stars above are shining bright",
    ]
    specs = [
        LineSpec(8, "01010101", "A"),
        LineSpec(7, "1010101", "B"),
        LineSpec(7, "1010101", "B"),
        LineSpec(8, "01010101", "A"),
    ]
    sec = validate_section(lines, specs)
    print(f"Section status: {sec.status}")
    for lr in sec.line_results:
        print(f'  [{lr.status:12}] score {lr.score:4.1f}  "{lr.line}"')
        for p in lr.problems:
            print(f"        - {p}")
    if sec.rhyme:
        print(f"  rhyme ok: {sec.rhyme['ok']}  groups: {sec.rhyme['groups']}")


# --------------------------------------------------------------------------
# Features 2 & 3: G2P fallback + contractions
# --------------------------------------------------------------------------
def demo_oov_and_contractions():
    hr("FEATURES 2 & 3 — G2P fallback for OOV + contraction handling")
    from lyricsmith import analyze_word
    for w in ["Aaliyah", "Insta", "don't", "lovin'", "'cause", "moonlight"]:
        wa = analyze_word(w)
        kind = "known" if wa.known else "G2P guess"
        print(f"  {w:<10} -> stress {wa.stress_variants}  ({kind}, "
              f"confidence={wa.confidence})")

    print("\nValidating a line containing an OOV name:")
    r = validate_line("Aaliyah sings to me tonight", LineSpec(8, "01010101"))
    print(f'  status={r.status}  oov={r.oov}')
    for p in r.problems:
        print(f"    - {p}")


# --------------------------------------------------------------------------
# The generation loop (uses the packaged MockLLM for offline reproducibility)
# --------------------------------------------------------------------------
def demo_generation_loop():
    hr("FEATURES 7-10 — generate / validate / repair / rhyme-aware loop")
    llm = MockLLM()

    print("Single slot with repair loop (target 8 syll, 01010101):")
    sr = generate_line(
        llm,
        meaning="opener: introduce the boy alone in his room",
        spec=LineSpec(8, "01010101"),
        candidates_per_round=3, max_rounds=4,
    )
    print(f"  -> {sr.status}  accepted: {sr.accepted!r}  (attempts {sr.attempts})")
    for cand, probs in sr.rejected:
        print(f"     rejected: {cand!r} :: {probs}")

    print("\nRhyme-aware two-line generation (line 2 must rhyme with line 1):")
    slots = [
        {"meaning": "opener: introduce the boy alone",
         "spec": LineSpec(8, "01010101"), "rhyme_label": "A"},
        {"meaning": "a strong night-time image",
         "spec": LineSpec(7, "1010101"), "rhyme_label": "A"},
    ]
    lines, results = generate_section(llm, slots,
                                      candidates_per_round=3, max_rounds=4)
    for i, (ln, r) in enumerate(zip(lines, results), 1):
        print(f"  line {i}: [{r.status}] {ln!r}")


# --------------------------------------------------------------------------
# Wiring a REAL local LLM (run real_llm_demo.py for a live version)
# --------------------------------------------------------------------------
def real_llm_example():
    """
    from lyricsmith import generate_section, LineSpec
    from lyricsmith.llm import OllamaClient   # or VLLMClient

    llm = OllamaClient(model="llama3.1")      # ollama serve; ollama pull llama3.1
    # llm = VLLMClient(model="meta-llama/Meta-Llama-3.1-8B-Instruct")

    slots = [
        {"meaning": "introduce the boy alone in his room",
         "spec": LineSpec(8, "01010101"), "rhyme_label": "A"},
        {"meaning": "describe the quiet bedroom",
         "spec": LineSpec(10, "0101010101"), "rhyme_label": "B"},
        {"meaning": "suggest innocence or vulnerability",
         "spec": LineSpec(10, "0101010101"), "rhyme_label": "B"},
        {"meaning": "end with a strong visual image",
         "spec": LineSpec(8, "01010101"), "rhyme_label": "A"},
    ]
    lines, results = generate_section(llm, slots,
                                      candidates_per_round=6, max_rounds=5)
    for i, (ln, r) in enumerate(zip(lines, results), 1):
        print(i, r.status, ln)
    """
    pass


if __name__ == "__main__":
    print(f"Dictionary source: {DICT_SOURCE}")
    demo_strictness_and_scoring()
    demo_rhyme()
    demo_section()
    demo_oov_and_contractions()
    demo_generation_loop()
    print("\nDone.")
