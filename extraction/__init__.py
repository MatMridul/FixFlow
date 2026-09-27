"""FixFlow extraction package."""
from extraction.extractor import ExtractionOutcome, StructureExtractor, clean_llm_json
from extraction.llm_client import LLMChain, LLMError
from extraction.prompt import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
from extraction.provenance import compute_sentence_overlap, filter_provenance, split_into_sentences

__all__ = [
    "StructureExtractor",
    "ExtractionOutcome",
    "LLMChain",
    "LLMError",
    "clean_llm_json",
    "EXTRACTION_SYSTEM_PROMPT",
    "build_extraction_prompt",
    "filter_provenance",
    "split_into_sentences",
    "compute_sentence_overlap",
]

