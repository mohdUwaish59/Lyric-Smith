"""
generation.py — LLM generation + validation loop (features 7-10).

This module is LLM-provider-agnostic. It defines an LLMClient protocol; the
real app wires in Anthropic/OpenAI/etc., while tests use a deterministic mock.

Features:
  7. Candidate generation: ask the LLM for N candidates per line slot.
  8. Repair loop: failed candidates are re-prompted with the validator's exact
     diagnostics until they pass or the retry budget is exhausted.
  9. Retry budget + graceful fallback: returns the best near-miss if nothing
     converges, never an exception.
 10. Rhyme-aware generation: when a slot must rhyme with an already-accepted
     line, the rhyme constraint (and target rhyme sound) is injected into the
     prompt and enforced by the validator.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional

from .validator import (LineSpec, Strictness, validate_line)
from .rhyme import rhyme_keys_for_word, last_word, words_rhyme


# --------------------------------------------------------------------------
# LLM client protocol
# --------------------------------------------------------------------------

# An LLMClient is any callable: (prompt: str, n: int) -> list[str]
# returning n candidate lines. Kept deliberately minimal.
LLMClient = Callable[[str, int], list]


# --------------------------------------------------------------------------
# Prompt construction
# --------------------------------------------------------------------------

def _describe_stress(template: str) -> str:
    marks = []
    for i, c in enumerate(template, 1):
        if c == "1":
            marks.append(f"{i}=STRONG")
        elif c == "0":
            marks.append(f"{i}=weak")
        else:
            marks.append(f"{i}=any")
    return ", ".join(marks)


def build_prompt(meaning, spec: LineSpec, rhyme_with=None,
                 rhyme_sounds=None, feedback=None, prior_lines=None,
                 n_candidates=1):
    """Construct a generation prompt for one line slot."""
    p = []
    p.append("You are a professional lyricist writing song lyrics to fit an existing melody.")
    p.append("\nYour goal: Write creative, vivid, natural-sounding lyrics that express the meaning")
    p.append("while fitting the technical constraints perfectly.")
    p.append("\nIMPORTANT: Count syllables carefully before responding. Each word contributes syllables:")
    p.append("  - Example: 'beautiful' = beau-ti-ful = 3 syllables")
    p.append("  - Example: 'night' = 1 syllable, 'tonight' = to-night = 2 syllables")
    
    if prior_lines:
        p.append("\nLines already written in this section:")
        for pl in prior_lines:
            p.append(f"  - {pl}")
        p.append("Build on these lines. Use varied vocabulary. Avoid repetition.")
    
    p.append(f"\nMeaning/content for THIS line: {meaning}")
    p.append("Express this meaning with specific, concrete imagery. Avoid generic phrases.")
    p.append(f"\nTechnical constraints (must all be satisfied):")
    p.append(f"  - Exactly {spec.syllables} syllables (count carefully!).")
    p.append(f"  - Stress pattern (1=stressed, 0=unstressed): {spec.stress}")
    p.append(f"    i.e. {_describe_stress(spec.stress)}")
    
    # Add concrete examples for common syllable counts
    if spec.syllables == 8 and spec.stress == "01010101":
        p.append(f"  - Example of valid 8-syllable line with this pattern:")
        p.append(f"    'The boy a-lone with-in his room' (The=1, boy=1, a=0, lone=1, with=0, in=1, his=0, room=1)")
    elif spec.syllables == 10 and spec.stress == "0101010101":
        p.append(f"  - Example of valid 10-syllable line with this pattern:")
        p.append(f"    'The qui-et dark-ness wraps a-round him tight' (10 syllables, alternating stress)")
    if rhyme_with:
        p.append(f"  - Must rhyme with: \"{rhyme_with}\" "
                 f"(end-word \"{last_word(rhyme_with)}\").")
        if rhyme_sounds:
            p.append(f"    Target rhyme sound(s): {', '.join(sorted(rhyme_sounds))}.")
        p.append("    Use a natural rhyme, not just swapping one word.")
    if feedback:
        p.append(f"\nA previous attempt failed validation:")
        for f in feedback:
            p.append(f"  - {f}")
        p.append("Fix these issues while keeping the language natural and vivid.")
    if n_candidates and n_candidates > 1:
        p.append(f"\nGenerate {n_candidates} DISTINCT, creative options:")
        p.append(f"  - Use different vocabulary and imagery in each option")
        p.append(f"  - Make each line complete and natural")
        p.append(f"  - No numbering, no bullets, no commentary")
        p.append(f"  - Return exactly {n_candidates} lines, one per line")
    else:
        p.append("\nWrite one creative, natural-sounding line that fits all constraints.")
        p.append("Return ONLY the line text, nothing else.")
    return "\n".join(p)


# --------------------------------------------------------------------------
# Generation result
# --------------------------------------------------------------------------

@dataclass
class SlotResult:
    accepted: Optional[str]            # the winning line, or None
    status: str                        # PASS / UNVERIFIABLE / NO_CANDIDATE
    attempts: int
    best_near_miss: Optional[object] = None   # LineResult if nothing passed
    rejected: list = field(default_factory=list)  # (line, problems) log


def generate_line(llm: LLMClient, meaning, spec: LineSpec,
                  rhyme_with=None, prior_lines=None,
                  strictness=Strictness.SUNG,
                  candidates_per_round=6, max_rounds=4,
                  accept_unverifiable=False):
    """Generate one valid line via a generate-validate-repair loop.

    Returns SlotResult. Never raises on non-convergence: falls back to the
    best near-miss (feature 9).
    """
    rhyme_sounds = None
    if rhyme_with:
        ew = last_word(rhyme_with)
        rhyme_sounds = rhyme_keys_for_word(ew) if ew else None

    feedback = None
    attempts = 0
    best = None              # (score, LineResult)
    rejected_log = []
    problem_patterns = {}    # Track common problems across attempts
    last_best_score = float('inf')
    no_improvement_rounds = 0

    for _round in range(max_rounds):
        prompt = build_prompt(meaning, spec, rhyme_with, rhyme_sounds,
                              feedback, prior_lines,
                              n_candidates=candidates_per_round)
        candidates = llm(prompt, candidates_per_round)

        round_feedback = None
        round_problems = []
        for cand in candidates:
            cand = cand.strip()
            if not cand:
                continue
            attempts += 1
            res = validate_line(cand, spec, strictness)

            # Rhyme enforcement (feature 10).
            rhyme_ok, rhyme_verifiable = (True, True)
            if rhyme_with:
                rhyme_ok, rhyme_verifiable = words_rhyme(rhyme_with, cand)

            if res.status == "PASS" and rhyme_ok:
                return SlotResult(cand, "PASS", attempts, None, rejected_log)

            if (res.status == "UNVERIFIABLE" and rhyme_ok
                    and accept_unverifiable):
                return SlotResult(cand, "UNVERIFIABLE", attempts, res,
                                  rejected_log)

            # Build problems for logging + feedback.
            probs = list(res.problems)
            if res.status == "UNVERIFIABLE" and res.oov and not probs:
                probs.append(
                    f"unverifiable: out-of-dictionary word(s) {res.oov}")
            if rhyme_with and not rhyme_ok:
                if rhyme_verifiable:
                    probs.append(
                        f"does not rhyme with '{last_word(rhyme_with)}'")
                else:
                    probs.append(
                        f"rhyme with '{last_word(rhyme_with)}' unverifiable "
                        f"(end-word out of dictionary)")
            rejected_log.append((cand, probs))
            
            # Track problem patterns for better feedback
            for prob in probs:
                problem_patterns[prob] = problem_patterns.get(prob, 0) + 1
            round_problems.extend(probs)

            # Track best near-miss.
            rhyme_penalty = 0 if rhyme_ok else 5
            score = res.score + rhyme_penalty
            if best is None or score < best[0]:
                best = (score, res)

        # Check for improvement - early bailout if stuck
        if best and best[0] < last_best_score:
            last_best_score = best[0]
            no_improvement_rounds = 0
        else:
            no_improvement_rounds += 1
        
        # Early exit if no improvement for 3 consecutive rounds
        if no_improvement_rounds >= 3 and _round >= 2:
            break

        # Aggregate feedback: prioritize most common problems
        if round_problems and _round < max_rounds - 1:
            # Get unique problems sorted by frequency
            unique_probs = sorted(set(round_problems), 
                                key=lambda p: problem_patterns.get(p, 0), 
                                reverse=True)
            round_feedback = unique_probs[:3]  # Top 3 most common issues
        
        feedback = round_feedback

    # Exhausted budget (feature 9 fallback).
    if best is not None:
        return SlotResult(None, "NO_CANDIDATE", attempts, best[1], rejected_log)
    return SlotResult(None, "NO_CANDIDATE", attempts, None, rejected_log)


def generate_section(llm: LLMClient, slots, strictness=Strictness.SUNG,
                     candidates_per_round=6, max_rounds=4):
    """Generate a full section line by line, rhyme-aware (feature 10).

    slots: list of dicts, each:
        { "meaning": str, "spec": LineSpec, "rhyme_label": str }
    Lines sharing a rhyme_label must rhyme; the first accepted line in a group
    becomes the rhyme anchor for the rest.

    Returns (lines: list[Optional[str]], slot_results: list[SlotResult]).
    """
    accepted_lines = []
    anchor_for_label = {}     # label -> accepted line text
    results = []

    for slot in slots:
        spec = slot["spec"]
        label = slot.get("rhyme_label", ".")
        rhyme_with = anchor_for_label.get(label) if label not in ".-" else None

        sr = generate_line(
            llm, slot["meaning"], spec,
            rhyme_with=rhyme_with,
            prior_lines=accepted_lines or None,
            strictness=strictness,
            candidates_per_round=candidates_per_round,
            max_rounds=max_rounds,
        )
        results.append(sr)

        if sr.accepted:
            accepted_lines.append(sr.accepted)
            if label not in ".-" and label not in anchor_for_label:
                anchor_for_label[label] = sr.accepted
        else:
            accepted_lines.append(None)

    return [r.accepted for r in results], results
