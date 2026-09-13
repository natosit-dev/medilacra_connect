from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "disco"
RUNTIME_RULES_PATH = DATA_DIR / "rules.json"
DEFAULT_RULES_PATH = Path(__file__).resolve().parent / "rules" / "defaults.json"


@dataclass(frozen=True)
class FeatureRule:
    """Configuration for one deterministic text feature."""

    id: str
    label: str
    kind: str
    weight: float = 1.0
    ai_weight: float = 0.0
    terms: tuple[str, ...] = ()
    pattern: str | None = None


def _rule_from_dict(raw: dict) -> FeatureRule:
    return FeatureRule(
        id=str(raw["id"]),
        label=str(raw["label"]),
        kind=str(raw["kind"]),
        weight=float(raw.get("weight", 1.0)),
        ai_weight=float(raw.get("ai_weight", 0.0)),
        terms=tuple(str(term) for term in raw.get("terms", ())),
        pattern=raw.get("pattern"),
    )


def _load_rule_file(path: Path) -> tuple[FeatureRule, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return tuple(_rule_from_dict(item) for item in raw)


DEFAULT_RULES = _load_rule_file(DEFAULT_RULES_PATH)


def load_rules(path: Path = RUNTIME_RULES_PATH) -> tuple[FeatureRule, ...]:
    """Load mutable local rules, falling back to checked-in JSON defaults."""

    if not path.exists():
        return DEFAULT_RULES
    return _load_rule_file(path)


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
