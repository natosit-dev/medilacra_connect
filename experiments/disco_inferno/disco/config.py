from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureRule:
    """Configuration for one deterministic text feature."""

    id: str
    label: str
    kind: str
    weight: float = 1.0
    terms: tuple[str, ...] = ()
    pattern: str | None = None


DEFAULT_RULES: tuple[FeatureRule, ...] = (
    FeatureRule(
        id="metaphor_vocabulary",
        label="Metaphor vocabulary",
        kind="lexicon",
        terms=(
            "substrate",
            "fabric",
            "vessel",
            "basin",
            "field",
            "landscape",
            "manifold",
            "resonance",
        ),
    ),
    FeatureRule(
        id="mechanism_placeholders",
        label="Mechanism placeholders",
        kind="lexicon_stem",
        terms=(
            "shape",
            "steer",
            "align",
            "mediate",
            "emerge",
            "resonate",
            "transform",
        ),
    ),
    FeatureRule(
        id="anthropomorphic_mechanism",
        label="Anthropomorphic mechanism phrases",
        kind="regex",
        pattern=(
            r"\b(?:AI|LLM|model|system|algorithm)\s+"
            r"(?:wants?|remembers?|believes?|understands?|chooses?|refuses?|tries?)\b"
        ),
    ),
    FeatureRule(
        id="nominalizations",
        label="Nominalizations",
        kind="regex",
        pattern=r"\b\w+(?:tion|sion|ment|ness|ity|ance|ence|ism|ization)\b",
        weight=0.5,
    ),
    FeatureRule(
        id="unintroduced_acronyms",
        label="Unintroduced acronyms",
        kind="unintroduced_acronym",
    ),
)
