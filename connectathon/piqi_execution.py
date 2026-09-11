from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import requests
from requests.auth import HTTPBasicAuth


def _canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _pretty_json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return slug or "endpoint"


@dataclass
class EndpointConfig:
    name: str
    url: str
    payload_mode: str = "fhir_bundle"
    timeout_seconds: float = 30.0
    verify_tls: bool = True
    auth_mode: str = "none"
    username: str = ""
    password: str = field(default="", repr=False)
    header_name: str = ""
    header_value: str = field(default="", repr=False)
    model_mnemonic: str = "PAT_CLINICAL_V1"
    rubric_mnemonic: str = "USCDI_V3"
    contributor_id: str = "MediLacra"
    data_source_id: str = "MediLacra Connectathon 43"

    def public_metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "url": self.url,
            "payload_mode": self.payload_mode,
            "timeout_seconds": self.timeout_seconds,
            "verify_tls": self.verify_tls,
            "auth_mode": self.auth_mode,
            "username_present": bool(self.username) if self.auth_mode == "basic" else False,
            "header_name": self.header_name if self.auth_mode == "header" else "",
            "header_value_present": bool(self.header_value) if self.auth_mode == "header" else False,
            "model_mnemonic": self.model_mnemonic if self.payload_mode == "piqi_request" else None,
            "rubric_mnemonic": self.rubric_mnemonic if self.payload_mode == "piqi_request" else None,
            "contributor_id": self.contributor_id if self.payload_mode == "piqi_request" else None,
            "data_source_id": self.data_source_id if self.payload_mode == "piqi_request" else None,
        }


def build_piqi_request(
    message_data: str,
    *,
    message_id: str,
    model_mnemonic: str = "PAT_CLINICAL_V1",
    rubric_mnemonic: str = "USCDI_V3",
    contributor_id: str = "MediLacra",
    data_source_id: str = "MediLacra Connectathon 43",
) -> dict[str, Any]:
    if not message_data.strip():
        raise ValueError("PIQI MessageData must not be empty")
    return {
        "ContributorID": contributor_id,
        "DataSourceID": data_source_id,
        "MessageID": message_id,
        "PIQIModelMnemonic": model_mnemonic,
        "EvaluationRubricMnemonic": rubric_mnemonic,
        "MessageData": message_data,
    }


def _request_payload(
    config: EndpointConfig,
    *,
    bundle: dict[str, Any],
    case_id: str,
    piqi_message_data: str | None,
) -> dict[str, Any]:
    if config.payload_mode == "fhir_bundle":
        return bundle
    if config.payload_mode == "piqi_request":
        if piqi_message_data is None:
            raise ValueError(
                "PIQI reference-service mode requires PIQI-format MessageData. "
                "FHIR JSON is not silently treated as a PIQI message."
            )
        return build_piqi_request(
            piqi_message_data,
            message_id=case_id,
            model_mnemonic=config.model_mnemonic,
            rubric_mnemonic=config.rubric_mnemonic,
            contributor_id=config.contributor_id,
            data_source_id=config.data_source_id,
        )
    raise ValueError(f"Unsupported endpoint payload mode: {config.payload_mode}")


def _casefold_get(mapping: dict[str, Any] | None, key: str, default: Any = None) -> Any:
    if not isinstance(mapping, dict):
        return default
    wanted = key.casefold()
    for actual, value in mapping.items():
        if str(actual).casefold() == wanted:
            return value
    return default


_STABLE_SCORE_KEYS = (
    "Denominator",
    "Numerator",
    "PIQIScore",
    "CriticalFailureCount",
    "WeightedDenominator",
    "WeightedNumerator",
    "WeightedPIQIScore",
)


def _stable_score(score: dict[str, Any] | None) -> dict[str, Any]:
    return {key: _casefold_get(score, key) for key in _STABLE_SCORE_KEYS}


def normalize_piqi_response(payload: Any) -> dict[str, Any] | None:
    """Extract stable PIQI result semantics from the current reference-service response.

    Raw response bytes are preserved separately. This intentionally drops transport/process
    metadata such as ProcessDate, MessageID and ElapsedTimeInMS from the comparison view.
    """
    if not isinstance(payload, dict):
        return None
    scoring = _casefold_get(payload, "ScoringData")
    if not isinstance(scoring, dict):
        return None

    message_results = _casefold_get(scoring, "MessageResults", {})
    data_class_results = _casefold_get(scoring, "DataClassResults", []) or []
    normalized_classes: list[dict[str, Any]] = []
    for row in data_class_results:
        if not isinstance(row, dict):
            continue
        normalized = {
            "DataClassName": _casefold_get(row, "DataClassName"),
            "InstanceCount": _casefold_get(row, "InstanceCount"),
            **_stable_score(row),
        }
        normalized_classes.append(normalized)
    normalized_classes.sort(key=lambda row: str(row.get("DataClassName") or ""))

    informational_results = _casefold_get(scoring, "InformationalResults", []) or []
    normalized_info: list[dict[str, Any]] = []
    for group in informational_results:
        if not isinstance(group, dict):
            continue
        evaluations = _casefold_get(group, "EvaluationList", []) or []
        normalized_evaluations = []
        for item in evaluations:
            if not isinstance(item, dict):
                continue
            normalized_evaluations.append(
                {
                    "EntityName": _casefold_get(item, "EntityName"),
                    "EvaluationName": _casefold_get(item, "EvaluationName"),
                    "InstanceCount": _casefold_get(item, "InstanceCount"),
                    "Denominator": _casefold_get(item, "Denominator"),
                    "Numerator": _casefold_get(item, "Numerator"),
                }
            )
        normalized_evaluations.sort(
            key=lambda item: (
                str(item.get("EntityName") or ""),
                str(item.get("EvaluationName") or ""),
            )
        )
        normalized_info.append(
            {
                "DataClassName": _casefold_get(group, "DataClassName"),
                "EvaluationList": normalized_evaluations,
            }
        )
    normalized_info.sort(key=lambda row: str(row.get("DataClassName") or ""))

    plausibility = _casefold_get(scoring, "PlausibilityResults", []) or []

    return {
        "Succeeded": _casefold_get(payload, "Succeeded"),
        "ErrorMessage": _casefold_get(payload, "ErrorMessage"),
        "EvaluationRubric": _casefold_get(scoring, "EvaluationRubric"),
        "MessageResults": _stable_score(message_results if isinstance(message_results, dict) else {}),
        "DataClassResults": normalized_classes,
        "InformationalResults": normalized_info,
        "PlausibilityResults": plausibility,
        "AuditedMessage": _casefold_get(payload, "AuditedMessage"),
    }


def _flatten_json(value: Any, path: str = "$") -> dict[str, Any]:
    leaves: dict[str, Any] = {}
    if isinstance(value, dict):
        if not value:
            leaves[path] = {}
        for key in sorted(value):
            leaves.update(_flatten_json(value[key], f"{path}.{key}"))
        return leaves
    if isinstance(value, list):
        if not value:
            leaves[path] = []
        for index, item in enumerate(value):
            leaves.update(_flatten_json(item, f"{path}[{index}]"))
        return leaves
    leaves[path] = value
    return leaves


def compare_normalized_results(left: Any, right: Any) -> dict[str, Any]:
    left_map = _flatten_json(left)
    right_map = _flatten_json(right)
    all_paths = sorted(set(left_map) | set(right_map))
    differing = [
        path
        for path in all_paths
        if path not in left_map or path not in right_map or left_map[path] != right_map[path]
    ]
    return {
        "equal": not differing,
        "left_leaf_count": len(left_map),
        "right_leaf_count": len(right_map),
        "differing_leaf_count": len(differing),
        "differing_paths": differing,
    }


def submit_payload(
    config: EndpointConfig,
    payload: dict[str, Any],
    *,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    request_bytes = _canonical_json_bytes(payload)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    auth = None

    if config.auth_mode == "basic":
        auth = HTTPBasicAuth(config.username, config.password)
    elif config.auth_mode == "header":
        if not config.header_name:
            raise ValueError("Header auth requires a header name")
        headers[config.header_name] = config.header_value
    elif config.auth_mode != "none":
        raise ValueError(f"Unsupported auth mode: {config.auth_mode}")

    client = session or requests.Session()
    started = time.perf_counter()
    try:
        response = client.post(
            config.url,
            data=request_bytes,
            headers=headers,
            auth=auth,
            timeout=config.timeout_seconds,
            verify=config.verify_tls,
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        response_bytes = response.content
        try:
            response_json = response.json()
        except ValueError:
            response_json = None

        normalized = normalize_piqi_response(response_json)
        if normalized is None and response_json is not None:
            normalized = response_json

        return {
            "transport_ok": True,
            "ok": bool(response.ok),
            "status_code": response.status_code,
            "reason": response.reason,
            "elapsed_ms": elapsed_ms,
            "request_bytes": request_bytes,
            "request_sha256": sha256_bytes(request_bytes),
            "response_bytes": response_bytes,
            "response_sha256": sha256_bytes(response_bytes),
            "response_headers": dict(response.headers),
            "response_json": response_json,
            "normalized": normalized,
            "error": None,
        }
    except requests.RequestException as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        return {
            "transport_ok": False,
            "ok": False,
            "status_code": None,
            "reason": None,
            "elapsed_ms": elapsed_ms,
            "request_bytes": request_bytes,
            "request_sha256": sha256_bytes(request_bytes),
            "response_bytes": b"",
            "response_sha256": None,
            "response_headers": {},
            "response_json": None,
            "normalized": None,
            "error": str(exc),
        }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_pretty_json_bytes(payload))


def persist_endpoint_result(
    run_dir: str | Path,
    *,
    case_id: str,
    config: EndpointConfig,
    result: dict[str, Any],
) -> dict[str, Any]:
    endpoint_dir = Path(run_dir) / "cases" / case_id / "endpoint_results" / _slug(config.name)
    endpoint_dir.mkdir(parents=True, exist_ok=True)

    (endpoint_dir / "request.body.json").write_bytes(result["request_bytes"])
    (endpoint_dir / "response.raw").write_bytes(result["response_bytes"])

    if result.get("response_json") is not None:
        _write_json(endpoint_dir / "response.json", result["response_json"])
    if result.get("normalized") is not None:
        _write_json(endpoint_dir / "normalized.json", result["normalized"])

    metadata = {
        "endpoint": config.public_metadata(),
        "transport_ok": result["transport_ok"],
        "ok": result["ok"],
        "status_code": result["status_code"],
        "reason": result["reason"],
        "elapsed_ms": result["elapsed_ms"],
        "request_sha256": result["request_sha256"],
        "response_sha256": result["response_sha256"],
        "response_headers": result["response_headers"],
        "response_is_json": result.get("response_json") is not None,
        "piqi_response_recognized": normalize_piqi_response(result.get("response_json")) is not None,
        "error": result["error"],
    }
    _write_json(endpoint_dir / "execution.json", metadata)
    return {**metadata, "endpoint_dir": str(endpoint_dir), "case_id": case_id}


def execute_case(
    run_dir: str | Path,
    *,
    case_id: str,
    bundle: dict[str, Any],
    endpoints: Iterable[EndpointConfig],
    piqi_message_data_by_endpoint: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    message_data_lookup = piqi_message_data_by_endpoint or {}
    for config in endpoints:
        payload = _request_payload(
            config,
            bundle=bundle,
            case_id=case_id,
            piqi_message_data=message_data_lookup.get(config.name),
        )
        result = submit_payload(config, payload)
        summaries.append(
            persist_endpoint_result(
                run_dir,
                case_id=case_id,
                config=config,
                result=result,
            )
        )
    return summaries


def compare_endpoint_artifacts(
    run_dir: str | Path,
    *,
    case_id: str,
    endpoint_names: Iterable[str],
) -> dict[str, Any]:
    endpoint_names = list(endpoint_names)
    normalized_by_endpoint: dict[str, Any] = {}
    for endpoint_name in endpoint_names:
        path = (
            Path(run_dir)
            / "cases"
            / case_id
            / "endpoint_results"
            / _slug(endpoint_name)
            / "normalized.json"
        )
        if path.exists():
            normalized_by_endpoint[endpoint_name] = json.loads(path.read_text(encoding="utf-8"))

    pairwise: list[dict[str, Any]] = []
    names = list(normalized_by_endpoint)
    for i, left_name in enumerate(names):
        for right_name in names[i + 1 :]:
            comparison = compare_normalized_results(
                normalized_by_endpoint[left_name],
                normalized_by_endpoint[right_name],
            )
            pairwise.append(
                {
                    "left": left_name,
                    "right": right_name,
                    **comparison,
                }
            )

    return {
        "case_id": case_id,
        "endpoint_count": len(endpoint_names),
        "normalized_response_count": len(normalized_by_endpoint),
        "pairwise": pairwise,
    }


def execute_run(
    run_dir: str | Path,
    *,
    endpoints: Iterable[EndpointConfig],
    piqi_message_dirs: dict[str, str | Path] | None = None,
) -> dict[str, Any]:
    """Execute every materialized case against the configured endpoints.

    Each case submits its mutant artifact; the control case's mutant is byte-semantically
    identical to its baseline by construction. PIQI reference-service endpoints require
    pre-converted PIQI MessageData files named <case_id>.piqi.json.
    """
    run_path = Path(run_dir)
    cases_root = run_path / "cases"
    if not cases_root.is_dir():
        raise FileNotFoundError(f"Connectathon cases directory not found: {cases_root}")

    endpoint_list = list(endpoints)
    if not endpoint_list:
        raise ValueError("At least one endpoint is required")

    message_dirs = {key: Path(value) for key, value in (piqi_message_dirs or {}).items()}
    case_summaries: list[dict[str, Any]] = []
    all_transport_ok = True
    any_piqi_service = any(config.payload_mode == "piqi_request" for config in endpoint_list)

    for case_dir in sorted(path for path in cases_root.iterdir() if path.is_dir()):
        case_id = case_dir.name
        mutant_path = case_dir / "mutant.fhir.json"
        if not mutant_path.exists():
            continue
        bundle = json.loads(mutant_path.read_text(encoding="utf-8"))

        message_data_lookup: dict[str, str] = {}
        for config in endpoint_list:
            if config.payload_mode != "piqi_request":
                continue
            root = message_dirs.get(config.name)
            if root is None:
                raise ValueError(
                    f"PIQI MessageData directory is required for endpoint {config.name!r}"
                )
            message_path = root / f"{case_id}.piqi.json"
            if not message_path.exists():
                raise FileNotFoundError(
                    f"Missing PIQI MessageData for {case_id} / {config.name}: {message_path}"
                )
            message_data_lookup[config.name] = message_path.read_text(encoding="utf-8")

        endpoint_results = execute_case(
            run_path,
            case_id=case_id,
            bundle=bundle,
            endpoints=endpoint_list,
            piqi_message_data_by_endpoint=message_data_lookup,
        )
        all_transport_ok = all_transport_ok and all(row["transport_ok"] for row in endpoint_results)
        comparison = compare_endpoint_artifacts(
            run_path,
            case_id=case_id,
            endpoint_names=[config.name for config in endpoint_list],
        )
        _write_json(case_dir / "endpoint_comparison.json", comparison)
        case_summaries.append(
            {
                "case_id": case_id,
                "endpoints": endpoint_results,
                "comparison": comparison,
            }
        )

    status = "COMPLETE" if all_transport_ok else "COMPLETE_WITH_TRANSPORT_ERRORS"
    execution_kind = "PIQI_EVALUATION" if any_piqi_service else "FHIR_TRANSPORT_ONLY"
    summary = {
        "status": status,
        "execution_kind": execution_kind,
        "endpoint_count": len(endpoint_list),
        "endpoints": [config.public_metadata() for config in endpoint_list],
        "cases": case_summaries,
    }
    _write_json(run_path / "endpoint_execution_summary.json", summary)

    manifest_path = run_path / "run_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["external_piqi_execution"] = (
            status if any_piqi_service else "NOT_RUN_FHIR_TRANSPORT_EXERCISED"
        )
        manifest["endpoint_execution"] = {
            "status": status,
            "execution_kind": execution_kind,
            "summary_file": "endpoint_execution_summary.json",
        }
        _write_json(manifest_path, manifest)

    return summary
