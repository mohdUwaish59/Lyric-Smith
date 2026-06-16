"""
lyricsmith — phonetic validation + LLM generation loop for songwriting to a
fixed melody.

Public API:
    from lyricsmith import (
        LineSpec, Strictness,
        validate_line, validate_section,
        validate_scheme,
        generate_line, generate_section, build_prompt,
        analyze_word, analyze_line,
    )
"""

from .phonetics import (analyze_word, analyze_line, DICT_SOURCE, HAVE_CMU,
                        g2p_stress_guess, g2p_phones)
from .rhyme import (validate_scheme, words_rhyme, rhyme_keys_for_word)
from .validator import (LineSpec, Strictness, LineResult, SectionResult,
                        validate_line, validate_section)
from .generation import (generate_line, generate_section, build_prompt,
                         SlotResult)
from .llm import OllamaClient, VLLMClient, MockLLM, clean_lines

__all__ = [
    "LineSpec", "Strictness", "LineResult", "SectionResult", "SlotResult",
    "validate_line", "validate_section", "validate_scheme",
    "words_rhyme", "rhyme_keys_for_word",
    "generate_line", "generate_section", "build_prompt",
    "analyze_word", "analyze_line", "g2p_stress_guess", "g2p_phones",
    "OllamaClient", "VLLMClient", "MockLLM", "clean_lines",
    "DICT_SOURCE", "HAVE_CMU",
]

__version__ = "0.3.0"
