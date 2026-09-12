"""DiScO — Deterministic Inspection of Semantic Coupling in Outputs.

A Disco Inferno submodel for cheap, deterministic inventories of observable
text features associated with semantic reconstruction cost.
"""

from .config import DEFAULT_RULES, FeatureRule
from .engine import DiScOProfile, FeatureResult, Match, inspect_text

DESCRIPTION = "Deterministic Inspection of Semantic Coupling in Outputs"

__all__ = [
    "DESCRIPTION",
    "DEFAULT_RULES",
    "DiScOProfile",
    "FeatureResult",
    "FeatureRule",
    "Match",
    "inspect_text",
]
