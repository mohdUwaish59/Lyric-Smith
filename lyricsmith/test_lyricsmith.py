#!/usr/bin/env python3
"""
test_lyricsmith.py — lightweight assertion tests (no pytest dependency).
Run: python test_lyricsmith.py
Note: some assertions depend on dictionary coverage; the ones here use words
present in the embedded fallback so they pass offline. With 'pronouncing'
installed they remain valid.
"""

from lyricsmith import (
    LineSpec, Strictness, validate_line, validate_section, validate_scheme,
    generate_line, words_rhyme, analyze_word,
)

passed = failed = 0


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ok   {name}")
    else:
        failed += 1
        print(f"  FAIL {name}")


print("Validation:")
check("perfect line passes",
      validate_line("The little boy asleep at night", LineSpec(8, "01010101")).status == "PASS")
check("short line fails",
      validate_line("A boy alone", LineSpec(8, "01010101")).status == "FAIL")
check("loose ignores stress",
      validate_line("Silver silver silver night", LineSpec(7, "0000000"), Strictness.LOOSE).status
      in ("PASS", "UNVERIFIABLE"))
check("wildcard template matches",
      validate_line("Silver moonlight on the floor", LineSpec(7, "xxxxxxx")).status == "PASS")

print("Multiple pronunciations:")
check("record passes as verb (0101)",
      validate_line("Record the night", LineSpec(4, "0101")).status == "PASS")
check("record passes as noun (1001)",
      validate_line("Record the night", LineSpec(4, "1001")).status == "PASS")

print("Rhyme:")
r, v = words_rhyme("asleep at night", "shining bright")
check("night/bright rhyme", r and v)
r2, v2 = words_rhyme("on the floor", "by the wall")
check("floor/wall do not rhyme", (not r2) and v2)
check("ABBA scheme validates",
      validate_scheme(
          ["asleep at night", "on the floor", "by the door", "shining bright"],
          "ABBA")["ok"])

print("OOV / G2P:")
wa = analyze_word("Znxqyl")
check("OOV word gets a G2P guess", (not wa.known) and len(wa.stress_variants) == 1)

print("Section:")
sec = validate_section(
    ["The little boy asleep at night", "Silver moonlight on the floor",
     "Shadows resting by the door", "The stars are shining bright"],
    [LineSpec(8, "01010101", "A"), LineSpec(7, "1010101", "B"),
     LineSpec(7, "1010101", "B"), LineSpec(7, "0101011", "A")])
check("section returns a status", sec.status in ("PASS", "FAIL", "UNVERIFIABLE"))

print("Generation loop:")
class _LLM:
    def __call__(self, prompt, n):
        return ["A boy alone", "The little boy asleep at night"][:n]
sr = generate_line(_LLM(), "introduce the boy", LineSpec(8, "01010101"),
                   candidates_per_round=2, max_rounds=2)
check("repair loop accepts a valid line", sr.status == "PASS" and sr.accepted)

print(f"\n{passed} passed, {failed} failed")
exit(1 if failed else 0)
