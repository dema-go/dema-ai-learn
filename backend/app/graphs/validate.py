from __future__ import annotations

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, Field

FULLWIDTH_START = 0xFF01
FULLWIDTH_END = 0xFF5E
ASCII_OFFSET = 0xFEE0


class GeneratedQuestion(BaseModel):
    knowledge_point: str
    question_type: Literal["single", "true_false"]
    stem: str
    options: list[str] = Field(min_length=2, max_length=4)
    answer_index: int = Field(ge=0, le=3)
    source_span: str
    explanation: str
    distractor_rationale: str = ""


def _fullwidth_to_halfwidth(text: str) -> str:
    chars: list[str] = []
    for char in text:
        code = ord(char)
        if FULLWIDTH_START <= code <= FULLWIDTH_END:
            chars.append(chr(code - ASCII_OFFSET))
        elif char == "\u3000":
            chars.append(" ")
        else:
            chars.append(char)
    return "".join(chars)


def normalize_for_match(text: str) -> str:
    nfkc = unicodedata.normalize("NFKC", text)
    half = _fullwidth_to_halfwidth(nfkc)
    return re.sub(r"\s+", "", half)


def span_in_source(span: str, source: str) -> bool:
    needle = normalize_for_match(span)
    haystack = normalize_for_match(source)
    return bool(needle) and needle in haystack


def validate_question(question: GeneratedQuestion, source: str) -> list[str]:
    reasons: list[str] = []
    span = question.source_span.strip()
    if not (8 <= len(span) <= 120):
        reasons.append("span_length_invalid")
    if not span_in_source(span, source):
        reasons.append("span_not_in_source")
    if question.answer_index >= len(question.options) or question.answer_index < 0:
        reasons.append("answer_index_out_of_range")
        return reasons
    if question.question_type == "true_false" and len(question.options) != 2:
        reasons.append("true_false_option_count")
    if question.question_type == "single" and not (3 <= len(question.options) <= 4):
        reasons.append("single_option_count")

    correct = question.options[question.answer_index].strip()
    if correct and correct in question.stem.replace(" ", ""):
        reasons.append("stem_leaks_answer")
    elif correct and correct in question.stem:
        reasons.append("stem_leaks_answer")

    if question.question_type == "single" and correct and not _option_supported_by_span(correct, span):
        reasons.append("unsupported_answer")

    if question.question_type == "single":
        for index, option in enumerate(question.options):
            if index == question.answer_index:
                continue
            compact = option.strip()
            if len(compact) >= 8 and span_in_source(compact, span) and compact != correct:
                reasons.append("distractor_conflicts")
                break
    return reasons


def _option_supported_by_span(option: str, span: str) -> bool:
    if span_in_source(option, span):
        return True
    chunks = [option[i : i + 4] for i in range(0, max(len(option) - 3, 1))]
    return any(len(chunk) >= 2 and span_in_source(chunk, span) for chunk in chunks)
