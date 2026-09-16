from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from connectathon.piqi_execution import (
    EndpointConfig,
    build_piqi_request,
    compare_normalized_results,
    execute_run,
    normalize_piqi_response,
    submit_payload,
)


class _Handler(BaseHTTPRequestHandler):
    response_payload = {
        "Succeeded": True,
        "ElapsedTimeInMS": 99,
        "ScoringData": {
            "ContributorID": "X",
            "DataSourceID": "Y",
            "MessageID": "volatile",
            "EvaluationRubric": "USCDI v3",
            "ProcessDate": "2026-09-11T12:00:00",
            "MessageResults": {
                "Denominator": 10,
                "Numerator": 9,
                "PIQIScore": 90,
                "CriticalFailureCount": 0,
                "WeightedDenominator": 10,
                "WeightedNumerator": 9,
                "WeightedPIQIScore": 90,
            },
            "DataClassResults": [],
            "InformationalResults": [],
            "PlausibilityResults": [],
        },
        "AuditedMessage": {"patient": {"id": "p1"}},
    }

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        self.server.last_body = self.rfile.read(length)
        self.server.last_headers = dict(self.headers)
        data = json.dumps(self.response_payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        return


@pytest.fixture()
def endpoint_server():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_reference_request_does_not_silently_convert_fhir():
    request = build_piqi_request(
        '{"FormatID":"FHIR JSON"}',
        message_id="case_001",
    )
    assert request["PIQIModelMnemonic"] == "PAT_CLINICAL_V1"
    assert request["EvaluationRubricMnemonic"] == "USCDI_V3"
    assert request["MessageData"] == '{"FormatID":"FHIR JSON"}'


def test_normalize_piqi_response_drops_process_metadata():
    normalized = normalize_piqi_response(_Handler.response_payload)
    assert normalized["Succeeded"] is True
    assert normalized["MessageResults"]["PIQIScore"] == 90
    assert "ProcessDate" not in normalized
    assert "MessageID" not in normalized


def test_submit_raw_fhir_preserves_request_bytes(endpoint_server):
    config = EndpointConfig(
        name="IRIS FHIR",
        url=f"http://127.0.0.1:{endpoint_server.server_port}/Bundle",
        payload_mode="fhir_bundle",
    )
    bundle = {"resourceType": "Bundle", "entry": []}
    result = submit_payload(config, bundle)
    assert result["ok"] is True
    assert json.loads(endpoint_server.last_body) == bundle
    assert result["response_sha256"]
    assert result["normalized"]["MessageResults"]["PIQIScore"] == 90


def test_compare_normalized_results_reports_exact_paths():
    comparison = compare_normalized_results(
        {"x": {"a": 1, "b": 2}},
        {"x": {"a": 1, "b": 3}},
    )
    assert comparison["equal"] is False
    assert comparison["differing_paths"] == ["$.x.b"]


def test_execute_run_persists_raw_endpoint_evidence(tmp_path, endpoint_server):
    run_dir = tmp_path / "run"
    case_dir = run_dir / "cases" / "case_000_control"
    case_dir.mkdir(parents=True)
    (case_dir / "mutant.fhir.json").write_text(
        json.dumps({"resourceType": "Bundle", "entry": []}),
        encoding="utf-8",
    )
    (run_dir / "run_manifest.json").write_text(
        json.dumps({"external_piqi_execution": "NOT_RUN"}),
        encoding="utf-8",
    )

    endpoint = EndpointConfig(
        name="IRIS FHIR",
        url=f"http://127.0.0.1:{endpoint_server.server_port}/Bundle",
        payload_mode="fhir_bundle",
    )
    summary = execute_run(run_dir, endpoints=[endpoint])

    assert summary["execution_kind"] == "FHIR_TRANSPORT_ONLY"
    evidence = case_dir / "endpoint_results" / "IRIS-FHIR"
    assert (evidence / "request.body.json").exists()
    assert (evidence / "response.raw").exists()
    assert (evidence / "normalized.json").exists()
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["external_piqi_execution"] == "NOT_RUN_FHIR_TRANSPORT_EXERCISED"


def test_piqi_request_mode_refuses_missing_converted_message(tmp_path, endpoint_server):
    run_dir = tmp_path / "run"
    case_dir = run_dir / "cases" / "case_000_control"
    case_dir.mkdir(parents=True)
    (case_dir / "mutant.fhir.json").write_text(
        json.dumps({"resourceType": "Bundle", "entry": []}),
        encoding="utf-8",
    )
    endpoint = EndpointConfig(
        name="PIQI Reference",
        url=f"http://127.0.0.1:{endpoint_server.server_port}/PIQI/ScoreAuditMessage",
        payload_mode="piqi_request",
    )
    with pytest.raises(ValueError, match="MessageData directory"):
        execute_run(run_dir, endpoints=[endpoint])
