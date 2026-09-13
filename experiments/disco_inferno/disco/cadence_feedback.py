from __future__ import annotations

import json
import tempfile
from dataclasses import asdict
from pathlib import Path

from .cadence import inspect_sentence_cadence
from .config import FeatureRule
from .engine import DiScOProfile
from .feedback import FEEDBACK_PATH, record_judgement as _record_judgement


def record_judgement(
    text: str,
    profile: DiScOProfile,
    ai_generated: bool,
    rules: tuple[FeatureRule, ...],
    path: Path = FEEDBACK_PATH,
    artifact: dict | None = None,
) -> dict:
    """Persist a judgement with unscored sentence-cadence observations.

    The underlying judgement builder remains unchanged. It writes once to a
    temporary JSONL file; this wrapper adds cadence observations and appends the
    enriched record to the real corpus path.
    """

    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_path = Path(tmp_dir) / "judgement.jsonl"
        record = _record_judgement(
            text=text,
            profile=profile,
            ai_generated=ai_generated,
            rules=rules,
            path=temp_path,
            artifact=artifact,
        )

    record["sentence_cadence"] = asdict(inspect_sentence_cadence(text))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record
