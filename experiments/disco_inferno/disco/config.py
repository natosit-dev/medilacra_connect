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
    semantic_max: float = 0.0
    ai_max: float = 0.0
    half_saturation: float = 1.0
    terms: tuple[str, ...] = ()
    pattern: str | None = None


def _rule_from_dict(
    raw: dict,
    scoring_defaults: dict[str, FeatureRule] | None = None,
) -> FeatureRule:
    """Build a rule from JSON, with safe migration for legacy local overrides.

    Older runtime rule files used ``weight`` and ``ai_weight`` as density
    multipliers. When a legacy local override matches a checked-in rule ID,
    preserve its detector dictionary/pattern while adopting the new bounded
    scoring priors from the checked-in defaults.
    """

    rule_id = str(raw["id"])
    default = (scoring_defaults or {}).get(rule_id)

    if "semantic_max" in raw:
        semantic_max = float(raw["semantic_max"])
    elif default is not None:
        semantic_max = default.semantic_max
    else:
        semantic_max = float(raw.get("weight", 0.0))

    if "ai_max" in raw:
        ai_max = float(raw["ai_max"])
    elif default is not None:
        ai_max = default.ai_max
    else:
        ai_max = float(raw.get("ai_weight", 0.0))

    if "half_saturation" in raw:
        half_saturation = float(raw["half_saturation"])
    elif default is not None:
        half_saturation = default.half_saturation
    else:
        half_saturation = 1.0

    return FeatureRule(
        id=rule_id,
        label=str(raw["label"]),
        kind=str(raw["kind"]),
        semantic_max=semantic_max,
        ai_max=ai_max,
        half_saturation=half_saturation,
        terms=tuple(str(term) for term in raw.get("terms", ())),
        pattern=raw.get("pattern"),
    )


def _load_rule_file(
    path: Path,
    scoring_defaults: dict[str, FeatureRule] | None = None,
) -> tuple[FeatureRule, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return tuple(_rule_from_dict(item, scoring_defaults=scoring_defaults) for item in raw)


DEFAULT_RULES = _load_rule_file(DEFAULT_RULES_PATH)


def load_rules(path: Path = RUNTIME_RULES_PATH) -> tuple[FeatureRule, ...]:
    """Load mutable local rules, falling back to checked-in JSON defaults.

    Legacy local overrides keep their detector dictionaries and patterns but
    inherit the new bounded scoring priors for matching rule IDs.
    """

    if not path.exists():
        return DEFAULT_RULES

    defaults_by_id = {rule.id: rule for rule in DEFAULT_RULES}
    return _load_rule_file(path, scoring_defaults=defaults_by_id)


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
