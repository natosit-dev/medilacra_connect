from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .config import DATA_DIR, FeatureRule
from .engine import DiScOProfile


FEEDBACK_PATH = DATA_DIR / "judgements.jsonl"


def _rules_fingerprint(rules: tuple[FeatureRule, ...]) -> str:
    payload = json.dumps(
        [asdict(rule) for rule in rules],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def record_judgement(
    text: str,
    profile: DiScOProfile,
    ai_generated: bool,
    rules: tuple[FeatureRule, ...],
    path: Path = FEEDBACK_PATH,
) -> dict:
    """Append one labelled judgement to local JSONL storage.

    The AI-generated label is metadata only. It does not participate in scoring.
    """

    record = {
        "judgement_id": str(uuid4()),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "ai_generated": bool(ai_generated),
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "text": text,
        "rules_sha256": _rules_fingerprint(rules),
        "rules": [asdict(rule) for rule in rules],
        "profile": profile.as_dict(),
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def load_judgements(path: Path = FEEDBACK_PATH) -> list[dict]:
    """Load locally stored judgement records in append order."""

    if not path.exists():
        return []

    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
