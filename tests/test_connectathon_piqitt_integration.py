from __future__ import annotations

import os
from pathlib import Path

from connectathon.piqitt_bridge import convert_hl7_text, load_backend
from connectathon.provenance import build_source_provenance
from connectathon.scenarios import build_scenario_pack, load_case


def _oru_message() -> str:
    return "\r".join(
        [
            r"MSH|^~\&|MEDILACRA|FAC|PIQITT|TEST|20260902100000-0400||ORU^R01|MSG1|P|2.5",
            "PID|1||MRN1^^^FAC||Doe^Jane||19800101|F|||1 Main St^^Lowell^MA^01854",
            "PV1|1|I|WARD^101^A^FAC",
            "OBR|1|||4548-4^Hemoglobin A1c^LN",
            "OBX|1|NM|4548-4^Hemoglobin A1c^LN||6.1|%|||||F|||20260901100000",
            "OBX|2|CWE|76691-5^Gender identity^LN||X-LOCAL^Synthetic coded value^99MEDILACRA|||||F|||20260901100000",
        ]
    )


def test_real_piqitt_converter_can_feed_local_connectathon_pack(tmp_path: Path):
    piqitt_repo = os.environ.get("PIQITT_REPO")
    assert piqitt_repo, "PIQITT_REPO must point to the checked-out PIQITT converter repository"

    bundle, metadata = convert_hl7_text(
        _oru_message(),
        message_index=1,
        piqitt_repo=piqitt_repo,
    )

    assert metadata["message_type"] == "ORU^R01"
    assert metadata["source_utc_offset_from_msh7"] == "-04:00"
    assert metadata["connectathon_cleanup"]["datetime_timezone_basis"] == "HL7_OFFSET:-04:00"
    assert len(metadata["piqitt_backend_sha256"]) == 64

    resource_types = [entry["resource"]["resourceType"] for entry in bundle["entry"]]
    assert "Patient" in resource_types
    assert "Observation" in resource_types

    observations = [
        entry["resource"]
        for entry in bundle["entry"]
        if entry["resource"].get("resourceType") == "Observation"
    ]
    assert all(
        observation.get("effectiveDateTime", "").endswith("-04:00")
        for observation in observations
        if observation.get("effectiveDateTime")
    )

    coded_observation = next(
        observation
        for observation in observations
        if ((observation.get("code") or {}).get("coding") or [{}])[0].get("code") == "76691-5"
    )
    assert "valueString" not in coded_observation
    coded_value = coded_observation["valueCodeableConcept"]["coding"][0]
    assert coded_value["code"] == "X-LOCAL"
    assert coded_value["system"] == "urn:hl7v2:99MEDILACRA"
    assert metadata["piqitt_coded_obx_compatibility"]["repaired"] == 1

    run = build_scenario_pack(
        bundle,
        output_root=tmp_path,
        case_ids=[
            "case_000_control",
            "case_001_availability",
            "case_002_code_system",
            "case_003_invalid_member",
        ],
        mutation_seed=666,
        run_id="integration-run",
        source_metadata=metadata,
    )

    assert all(case["preflight"] == "PASS" for case in run["cases"])
    assert len(run["cases"]) == 4

    code_system_case = load_case(run["run_dir"], "case_002_code_system")
    manifest = code_system_case["manifest"]
    assert manifest["changed_paths"]
    target_index = manifest["mutation"]["entry_index"]
    observation = code_system_case["mutant"]["entry"][target_index]["resource"]
    assert observation["resourceType"] == "Observation"
    assert "system" not in observation["code"]["coding"][0]

    invalid_member_case = load_case(run["run_dir"], "case_003_invalid_member")
    invalid_manifest = invalid_member_case["manifest"]
    invalid_index = invalid_manifest["mutation"]["entry_index"]
    baseline_target = invalid_member_case["baseline"]["entry"][invalid_index]["resource"]
    assert baseline_target["code"]["coding"][0]["system"] == "http://loinc.org"
    assert invalid_manifest["mutation"]["candidate_coding_systems"] == ["http://loinc.org"]


def test_backend_cache_reloads_when_converter_file_changes(tmp_path: Path):
    repo = tmp_path / "piqitt"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    backend_file = scripts / "fhir_convert_backend.py"

    backend_file.write_text("VALUE = 'first'\n", encoding="utf-8")
    first = load_backend(repo)
    assert first.VALUE == "first"

    backend_file.write_text("VALUE = 'second-version'\n", encoding="utf-8")
    second = load_backend(repo)
    assert second is not first
    assert second.VALUE == "second-version"


def test_uploaded_filename_is_not_treated_as_local_source_path(tmp_path: Path, monkeypatch):
    piqitt_repo = os.environ.get("PIQITT_REPO")
    assert piqitt_repo

    monkeypatch.chdir(tmp_path)
    same_named_local = tmp_path / "uploaded.hl7"
    same_named_local.write_text("UNRELATED LOCAL FILE", encoding="utf-8")

    uploaded = build_source_provenance(
        "MSH|uploaded-content",
        source_name="uploaded.hl7",
        source_path=None,
        medilacra_root=tmp_path,
        piqitt_repo=piqitt_repo,
    )
    assert uploaded["source_name"] == "uploaded.hl7"
    assert "source_file" not in uploaded

    local = build_source_provenance(
        "UNRELATED LOCAL FILE",
        source_name="uploaded.hl7",
        source_path=same_named_local,
        medilacra_root=tmp_path,
        piqitt_repo=piqitt_repo,
    )
    assert local["source_file"] == str(same_named_local.resolve())
