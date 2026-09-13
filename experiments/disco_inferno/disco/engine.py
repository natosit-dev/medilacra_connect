from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Iterable

from .config import DEFAULT_RULES, FeatureRule


WORD_RE = re.compile(r"\b\w+(?:[-']\w+)*\b")
ACRONYM_RE = re.compile(r"\b[A-Z][A-Z0-9-]{1,7}\b")
INTRODUCED_ACRONYM_RE = re.compile(
    r"\b[A-Z][A-Za-z]+(?:\s+[A-Z]?[A-Za-z]+){0,6}\s*\(([A-Z][A-Z0-9-]{1,7})\)"
)


@dataclass(frozen=True)
class Match:
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class FeatureResult:
    id: str
    label: str
    count: int
    rate_per_100_words: float
    weight: float
    ai_weight: float
    matches: tuple[Match, ...]


@dataclass(frozen=True)
class DiScOProfile:
    word_count: int
    character_count: int
    features: tuple[FeatureResult, ...]
    signal_score: float
    ai_signal_score: float

    def as_dict(self) -> dict:
        return asdict(self)


def _lexicon_matches(text: str, terms: Iterable[str], stems: bool = False) -> list[Match]:
    suffix = r"\w*" if stems else ""
    pattern = re.compile(
        r"\b(?:" + "|".join(re.escape(term) for term in terms) + r")" + suffix + r"\b",
        re.IGNORECASE,
    )
    return [Match(m.group(0), m.start(), m.end()) for m in pattern.finditer(text)]


def _regex_matches(text: str, pattern: str) -> list[Match]:
    compiled = re.compile(pattern, re.IGNORECASE)
    return [Match(m.group(0), m.start(), m.end()) for m in compiled.finditer(text)]


def _unintroduced_acronym_matches(text: str) -> list[Match]:
    introduced = {m.group(1) for m in INTRODUCED_ACRONYM_RE.finditer(text)}
    return [
        Match(m.group(0), m.start(), m.end())
        for m in ACRONYM_RE.finditer(text)
        if m.group(0) not in introduced
    ]


def _matches_for_rule(text: str, rule: FeatureRule) -> list[Match]:
    if rule.kind == "lexicon":
        return _lexicon_matches(text, rule.terms)
    if rule.kind == "lexicon_stem":
        return _lexicon_matches(text, rule.terms, stems=True)
    if rule.kind == "regex" and rule.pattern:
        return _regex_matches(text, rule.pattern)
    if rule.kind == "unintroduced_acronym":
        return _unintroduced_acronym_matches(text)
    raise ValueError(f"Unsupported DiScO feature kind: {rule.kind}")


def inspect_text(
    text: str,
    rules: tuple[FeatureRule, ...] = DEFAULT_RULES,
) -> DiScOProfile:
    """Create a deterministic feature inventory for one text blob.

    ``signal_score`` summarizes semantic reconstruction signals.
    ``ai_signal_score`` separately summarizes style/provenance signals associated
    with AI generation. Neither score is a calibrated probability.
    """

    word_count = len(WORD_RE.findall(text))
    denominator = max(word_count, 1)
    features: list[FeatureResult] = []

    for rule in rules:
        matches = tuple(_matches_for_rule(text, rule))
        rate = (len(matches) / denominator) * 100.0
        features.append(
            FeatureResult(
                id=rule.id,
                label=rule.label,
                count=len(matches),
                rate_per_100_words=rate,
                weight=rule.weight,
                ai_weight=rule.ai_weight,
                matches=matches,
            )
        )

    score = sum(feature.rate_per_100_words * feature.weight for feature in features)
    ai_score = sum(feature.rate_per_100_words * feature.ai_weight for feature in features)

    return DiScOProfile(
        word_count=word_count,
        character_count=len(text),
        features=tuple(features),
        signal_score=score,
        ai_signal_score=ai_score,
    )
