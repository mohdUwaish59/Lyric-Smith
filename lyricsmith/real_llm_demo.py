#!/usr/bin/env python3
"""
real_llm_demo.py — Live generation against a local open-source LLM.

Generates the exact 4-line verse from the client's brief (boy asleep alone),
with per-line syllable + stress constraints and an ABBA rhyme scheme, using
the generate-validate-repair loop. Only validated lines are shown.

Prereqs (pick ONE backend):

  Ollama:
    1. install from https://ollama.com
    2. ollama serve
    3. ollama pull llama3.1        (or mistral, qwen2.5, etc.)
    4. python real_llm_demo.py --backend ollama --model llama3.1

  vLLM (OpenAI-compatible):
    1. pip install vllm
    2. python -m vllm.entrypoints.openai.api_server \
         --model meta-llama/Meta-Llama-3.1-8B-Instruct
    3. python real_llm_demo.py --backend vllm \
         --model meta-llama/Meta-Llama-3.1-8B-Instruct

Also recommended for OOV coverage: pip install g2p_en
"""

import argparse

from lyricsmith import LineSpec, Strictness, generate_section
from lyricsmith.llm import OllamaClient, VLLMClient


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["ollama", "vllm"], default="ollama")
    ap.add_argument("--model", default="llama3.1")
    ap.add_argument("--host", default=None,
                    help="override server URL (e.g. http://localhost:11434)")
    ap.add_argument("--candidates", type=int, default=8,
                    help="candidates per round")
    ap.add_argument("--rounds", type=int, default=6, help="max repair rounds")
    ap.add_argument("--strictness", choices=["strict", "sung", "loose"],
                    default="sung")
    args = ap.parse_args()

    if args.backend == "ollama":
        llm = OllamaClient(model=args.model,
                           host=args.host or "http://localhost:11434")
    else:
        llm = VLLMClient(model=args.model,
                         host=args.host or "http://localhost:8000")

    strictness = Strictness(args.strictness)

    # The verse from the client's brief.
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

    print(f"Backend: {args.backend}  model: {args.model}  "
          f"strictness: {args.strictness}\n")
    print("Generating verse (ABBA, 8/10/10/8 syllables)...\n")

    lines, results = generate_section(
        llm, slots, strictness=strictness,
        candidates_per_round=args.candidates, max_rounds=args.rounds)

    for i, (ln, r) in enumerate(zip(lines, results), 1):
        spec = slots[i - 1]["spec"]
        print(f"Line {i}  [{r.status}]  "
              f"(target {spec.syllables} syll, {spec.stress}, "
              f"rhyme {slots[i-1]['rhyme_label']}, attempts {r.attempts})")
        print(f"   {ln if ln else '<<< no valid line found in budget >>>'}")
        if not ln and r.best_near_miss:
            print(f"   closest: {r.best_near_miss.line!r} "
                  f"-> {r.best_near_miss.problems}")
        print()


if __name__ == "__main__":
    main()
