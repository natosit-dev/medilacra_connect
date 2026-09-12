"""DiScO — Deterministic Inspection of Semantic Coupling in Outputs.

A Disco Inferno submodel for cheap, deterministic inventories of observable
text features associated with semantic reconstruction cost.
"""

from .config import (
    DEFAULT_RULES,
    RUNTIME_RULES_PATH,
    FeatureRule,
    load_rules,
    reset_rules,
    save_rules,
)
from .engine import DiScOProfile, FeatureResult, Match, inspect_text
from .feedback import FEEDBACK_PATH, load_judgements, record_judgement

DESCRIPTION = "Deterministic Inspection of Semantic Coupling in Outputs"

__all__ = [
    "DESCRIPTION",
    "DEFAULT_RULES",
    "RUNTIME_RULES_PATH",
    "FEEDBACK_PATH",
    "DiScOProfile",
    "FeatureResult",
    "FeatureRule",
    "Match",
    "inspect_text",
    "load_judgements",
    "load_rules",
    "record_judgement",
    "reset_rules",
    "save_rules",
]
