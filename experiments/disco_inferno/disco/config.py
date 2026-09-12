from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "disco"
RUNTIME_RULES_PATH = DATA_DIR / "rules.json"


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


def _rule_from_dict(raw: dict) -> FeatureRule:
    return FeatureRule(
        id=str(raw["id"]),
        label=str(raw["label"]),
        kind=str(raw["kind"]),
        weight=float(raw.get("weight", 1.0)),
        terms=tuple(str(term) for term in raw.get("terms", ())),
        pattern=raw.get("pattern"),
    )


def load_rules(path: Path = RUNTIME_RULES_PATH) -> tuple[FeatureRule, ...]:
    """Load mutable local rules, falling back to checked-in defaults."""

    if not path.exists():
        return DEFAULT_RULES
    raw = json.loads(path.read_text(encoding="utf-8"))
    return tuple(_rule_from_dict(item) for item in raw)


def save_rules(
    rules: tuple[FeatureRule, ...],
    path: Path = RUNTIME_RULES_PATH,
) -> Path:
    """Persist the active local rule configuration."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(rule) for rule in rules]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def reset_rules(path: Path = RUNTIME_RULES_PATH) -> None:
    """Remove local overrides so checked-in defaults become active again."""

    if path.exists():
        path.unlink()
