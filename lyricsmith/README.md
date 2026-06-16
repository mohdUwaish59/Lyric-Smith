# lyricsmith — validation engine + generation loop (features 1–10)

The core of an AI songwriting assistant that writes lyrics to a **fixed melody**.
A local open-source LLM generates candidate lines; this engine deterministically
enforces syllable count, stress pattern, and rhyme, re-prompting the model with
exact diagnostics until only lines that actually fit the melody remain. The UI
is built separately on top of this engine.

## Install

```bash
pip install -e .            # installs the package + 'pronouncing'
pip install g2p_en          # optional but recommended: neural G2P for OOV words
```

After `pip install -e .` you can `import lyricsmith` from anywhere — no need to
run from a specific folder.

## Run

```bash
python demo.py              # all 10 features, offline (mock LLM)
python test_lyricsmith.py   # assertion suite
python real_llm_demo.py --backend ollama --model llama3.1   # live, local LLM
```

The package runs offline without `pronouncing`/`g2p_en` via a small embedded
fallback dictionary + heuristic, so the demo and tests work with no network.

## Local LLM backends (feature 7)

**Ollama**
```bash
ollama serve
ollama pull llama3.1
python real_llm_demo.py --backend ollama --model llama3.1
```

**vLLM** (OpenAI-compatible server; also works with TGI, LM Studio, etc.)
```bash
python -m vllm.entrypoints.openai.api_server --model meta-llama/Meta-Llama-3.1-8B-Instruct
python real_llm_demo.py --backend vllm --model meta-llama/Meta-Llama-3.1-8B-Instruct
```

Any callable `(prompt, n) -> list[str]` works as an LLM, so other providers
drop in trivially.

## Implemented features

| # | Feature | Where |
|---|---------|-------|
| 1 | Rhyme-scheme validation (ABBA etc.) | `rhyme.py` |
| 2 | Neural grapheme-to-phoneme (g2p_en) for out-of-vocabulary words | `phonetics.py` |
| 3 | Contraction / apostrophe handling (`don't`, `lovin'`, `'cause`) | `phonetics.py` |
| 4 | Whole-section validation (syllables + stress + rhyme at once) | `validator.py` |
| 5 | Strictness levels: STRICT / SUNG / LOOSE | `validator.py` |
| 6 | Near-miss scoring (rank failures, not just pass/fail) | `validator.py` |
| 7 | LLM candidate generation via local Ollama / vLLM | `generation.py`, `llm.py` |
| 8 | Repair loop: re-prompt with exact diagnostics until valid | `generation.py` |
| 9 | Retry budget + graceful fallback to best near-miss | `generation.py` |
| 10 | Rhyme-aware generation (anchor line constrains the rest) | `generation.py` |

## How OOV words are handled (feature 2)

A word is resolved in three tiers, with decreasing confidence:
1. **Dictionary** (CMU via `pronouncing`) — `confidence=high`, fully verifiable.
2. **Neural G2P** (`g2p_en`) — `confidence=medium`. Predicts real ARPAbet
   phonemes with stress, so OOV words (names, slang) become both
   stress-checkable AND rhyme-checkable.
3. **Heuristic** (vowel-group count, no phonemes) — `confidence=low`. Used only
   if `g2p_en` is not installed; such words are reported UNVERIFIABLE rather
   than wrongly passed or failed.

## Quick API

```python
from lyricsmith import LineSpec, Strictness, validate_line, generate_line
from lyricsmith.llm import OllamaClient

r = validate_line("The little boy asleep at night", LineSpec(8, "01010101"))
print(r.status, r.score, r.problems)        # PASS 0.0 []

llm = OllamaClient(model="llama3.1")
sr = generate_line(llm, meaning="introduce the boy alone",
                   spec=LineSpec(8, "01010101"))
print(sr.status, sr.accepted)
```

Strictness: `SUNG` (default) treats monosyllables and secondary stress as
flexible — the realistic setting for singing. `STRICT` enforces every syllable;
`LOOSE` checks syllable count only.

## Still to do (the UI layer)
Chat interface, per-song project model + persistence, template editor,
accept/reject workflow, export — all build on this engine.
