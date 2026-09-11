from __future__ import annotations

import hashlib
import importlib.util
import os
import re
from pathlib import Path
from types import ModuleType
from typing import Any

from connectathon.fhir_control import _coded_value_from_string, prepare_control_bundle


_BACKEND_CACHE: dict[tuple[str, str], ModuleType] = {}
_HL7_UTC_OFFSET = re.compile(r"(?P<sign>[+-])(?P<hours>\d{2})(?P<minutes>\d{2})$")


def default_piqitt_repo() -> Path:
    """Return the most likely local PIQITT checkout without requiring it to be installed."""
    configured = os.getenv("PIQITT_REPO")
    if configured:
        return Path(configured).expanduser().resolve()

    medilacra_root = Path(__file__).resolve().parents[1]
    return (medilacra_root.parent / "piqitt").resolve()


def backend_path(piqitt_repo: str | Path | None = None) -> Path:
    repo = Path(piqitt_repo).expanduser().resolve() if piqitt_repo else default_piqitt_repo()
    return repo / "scripts" / "fhir_convert_backend.py"


def backend_sha256(piqitt_repo: str | Path | None = None) -> str:
    path = backend_path(piqitt_repo)
    if not path.exists():
        raise FileNotFoundError(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_backend(piqitt_repo: str | Path | None = None) -> ModuleType:
    """Load PIQITT's existing converter directly from its checkout.

    This deliberately avoids copying PIQITT mapping code into MediLacra. The local PIQITT
    repository remains the source of truth for HL7 -> FHIR conversion.

    The cache key includes the converter file hash. Updating or switching the PIQITT
    checkout therefore reloads changed converter code instead of leaving a long-running
    Streamlit session attached to a stale module.
    """
    path = backend_path(piqitt_repo)
    if not path.exists():
        raise FileNotFoundError(
            f"PIQITT converter not found at {path}. Set PIQITT_REPO or select the local PIQITT checkout."
        )

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    cache_key = (str(path), digest)
    if cache_key in _BACKEND_CACHE:
        return _BACKEND_CACHE[cache_key]

    # Drop stale versions of the same checkout path so a long-running UI cannot
    # accidentally retain converter code from an earlier revision.
    for key in list(_BACKEND_CACHE):
        if key[0] == str(path) and key != cache_key:
            _BACKEND_CACHE.pop(key, None)

    module_name = f"piqitt_fhir_convert_backend_{abs(hash(cache_key))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load PIQITT converter from {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _BACKEND_CACHE[cache_key] = module
    return module


def inspect_hl7_text(hl7_text: str, piqitt_repo: str | Path | None = None) -> list[dict[str, Any]]:
    """Return message index/type information using PIQITT's parser without materializing FHIR."""
    backend = load_backend(piqitt_repo)
    messages = backend.split_messages(hl7_text)
    summary: list[dict[str, Any]] = []
    for index, message in enumerate(messages, start=1):
        parsed = backend.parse_hl7(message)
        summary.append(
            {
                "message_index": index,
                "message_type": backend.detect_message_type(parsed),
                "segment_count": len(backend.split_segments(message)),
            }
        )
    return summary


def _repair_piqitt_coded_obx_values(
    raw_bundle: dict[str, Any],
    parsed: dict[str, Any],
    backend: ModuleType,
) -> dict[str, Any]:
    """Repair PIQITT CE-family OBX values that fell through to valueString.

    PIQITT main currently materializes OBX-2=CE as CodeableConcept but treats
    CWE/CNE as generic strings. The original HL7 datatype is used as provenance,
    so arbitrary narrative strings containing carets are never guessed to be coded.
    """
    observations = [
        entry.get("resource")
        for entry in raw_bundle.get("entry", [])
        if isinstance(entry, dict)
        and isinstance(entry.get("resource"), dict)
        and entry["resource"].get("resourceType") == "Observation"
    ]
    obx_entries = parsed.get("OBX") or []
    report: dict[str, Any] = {
        "obx_count": len(obx_entries),
        "observation_count": len(observations),
        "repaired": 0,
        "unresolved": [],
    }

    for index, (obx_entry, observation) in enumerate(zip(obx_entries, observations), start=1):
        fields = obx_entry.get("_fields", []) if isinstance(obx_entry, dict) else []
        value_type = str(backend.get_field(fields, 2) or "").upper()
        if value_type not in {"CE", "CWE", "CNE"}:
            continue
        if "valueCodeableConcept" in observation:
            continue

        raw_value = backend.get_field(fields, 5)
        if not raw_value or not isinstance(observation.get("valueString"), str):
            continue

        concept = _coded_value_from_string(raw_value, preserve_unknown_system=True)
        if concept is None:
            report["unresolved"].append(
                {"obx_index": index, "value_type": value_type, "value": raw_value}
            )
            continue

        observation.pop("valueString", None)
        observation["valueCodeableConcept"] = concept
        report["repaired"] += 1

    return report


def _source_utc_offset(parsed: dict[str, Any], backend: ModuleType) -> str | None:
    """Recover an explicit UTC offset from MSH-7 when the source HL7 supplies one."""
    msh_entries = parsed.get("MSH") or []
    if not msh_entries:
        return None
    first = msh_entries[0]
    fields = first.get("_fields", []) if isinstance(first, dict) else []
    raw = str(backend.get_msh_field(fields, 7) or "").strip()
    match = _HL7_UTC_OFFSET.search(raw)
    if not match:
        return None
    return f"{match.group('sign')}{match.group('hours')}:{match.group('minutes')}"


def convert_hl7_text(
    hl7_text: str,
    message_index: int = 1,
    piqitt_repo: str | Path | None = None,
    source_timezone: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Convert one 1-based HL7 message to the PIQI Connectathon FHIR control representation.

    PIQITT performs the actual HL7 -> FHIR mapping. The Connectathon layer then removes
    message-transport semantics and normalizes the resulting Bundle into a self-contained
    collection suitable for baseline/mutation experiments.

    When MSH-7 contains an explicit UTC offset, that offset is preserved when PIQITT has
    emitted naive FHIR dateTimes. Otherwise ``source_timezone`` may supply the sender's
    IANA timezone. If neither is available, the conversion process's local timezone is
    used rather than asserting UTC.
    """
    backend = load_backend(piqitt_repo)
    messages = backend.split_messages(hl7_text)
    if not messages:
        raise ValueError("No HL7 messages beginning with MSH| were found.")
    if message_index < 1 or message_index > len(messages):
        raise IndexError(f"message_index {message_index} is outside 1..{len(messages)}")

    selected_message = messages[message_index - 1]
    parsed = backend.parse_hl7(selected_message)
    source_offset = _source_utc_offset(parsed, backend)
    raw_bundle, message_type = backend.convert_message_to_bundle(selected_message)
    coded_value_compatibility = _repair_piqitt_coded_obx_values(raw_bundle, parsed, backend)
    bundle, cleanup = prepare_control_bundle(
        raw_bundle,
        source_timezone=source_timezone,
        source_utc_offset=source_offset,
    )
    metadata = {
        "message_index": message_index,
        "message_count": len(messages),
        "message_type": message_type,
        "piqitt_backend": str(backend_path(piqitt_repo)),
        "piqitt_backend_sha256": backend_sha256(piqitt_repo),
        "piqitt_raw_bundle_type": raw_bundle.get("type"),
        "piqitt_coded_obx_compatibility": coded_value_compatibility,
        "source_timezone_configured": source_timezone,
        "source_utc_offset_from_msh7": source_offset,
        "connectathon_bundle_type": bundle.get("type"),
        "connectathon_cleanup": cleanup,
    }
    return bundle, metadata


def convert_hl7_file(
    input_path: str | Path,
    message_index: int = 1,
    piqitt_repo: str | Path | None = None,
    source_timezone: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    path = Path(input_path)
    raw = path.read_text(encoding="utf-8", errors="ignore")
    bundle, metadata = convert_hl7_text(
        raw,
        message_index=message_index,
        piqitt_repo=piqitt_repo,
        source_timezone=source_timezone,
    )
    metadata["source_file"] = str(path.resolve())
    return bundle, metadata
