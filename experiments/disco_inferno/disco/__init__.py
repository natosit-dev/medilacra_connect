"""DiScO — Deterministic Inspection of Semantic Coupling in Outputs.

A Disco Inferno submodel for cheap, deterministic inventories of observable
text features associated with semantic reconstruction cost.
"""

from .artifacts import (
    DocHistoryUnavailable,
    extract_document_text,
    inspect_document_artifact,
)
from .cadence import SentenceCadenceObservation, inspect_sentence_cadence, sentence_word_lengths
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
from .guidance import (
    CADENCE_GUIDANCE,
    FEATURE_GUIDANCE,
    METRIC_GUIDANCE,
    VIRGIL_OVERVIEW,
    FeatureGuidance,
    get_feature_guidance,
)

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
    "SentenceCadenceObservation",
    "DocHistoryUnavailable",
    "FeatureGuidance",
    "FEATURE_GUIDANCE",
    "CADENCE_GUIDANCE",
    "METRIC_GUIDANCE",
    "VIRGIL_OVERVIEW",
    "extract_document_text",
    "get_feature_guidance",
    "inspect_document_artifact",
    "inspect_sentence_cadence",
    "inspect_text",
    "load_judgements",
    "load_rules",
    "record_judgement",
    "reset_rules",
    "save_rules",
    "sentence_word_lengths",
]
