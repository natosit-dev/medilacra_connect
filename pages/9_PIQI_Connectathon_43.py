from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from connectathon.piqi_execution import EndpointConfig, execute_run
from connectathon.piqitt_bridge import (
    backend_path,
    convert_hl7_text,
    default_piqitt_repo,
    inspect_hl7_text,
)
from connectathon.preflight import preflight_bundle
from connectathon.provenance import build_source_provenance
from connectathon.scenarios import (
    DEFAULT_SCENARIOS,
    build_scenario_pack,
    load_case,
    zip_run_directory,
)
from experiments.disco_inferno.fhir_corruptions import path_exists


RESULT_ROOT = Path("connectathon/results")
MEDILACRA_ROOT = Path(__file__).resolve().parents[1]


def _discover_hl7_files() -> list[Path]:
    candidates: list[Path] = []
    patterns = (
        "output/*.hl7",
        "experiments/disco_inferno/output/*/hl7/*.hl7",
    )
    for pattern in patterns:
        candidates.extend(path for path in Path(".").glob(pattern) if path.is_file())
    unique = {str(path.resolve()): path for path in candidates}
    return sorted(unique.values(), key=lambda path: path.stat().st_mtime, reverse=True)


def _bundle_resource_counts(bundle: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {}) if isinstance(entry, dict) else {}
        resource_type = resource.get("resourceType")
        if resource_type:
            counts[resource_type] = counts.get(resource_type, 0) + 1
    return counts


def _scenario_applicable(bundle: dict, scenario: dict) -> bool:
    if scenario["operator"] == "control":
        return True
    allowed_systems = set(scenario.get("candidate_coding_systems") or [])
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {}) if isinstance(entry, dict) else {}
        if resource.get("resourceType") != scenario.get("resource"):
            continue
        if not path_exists(resource, scenario.get("path") or ""):
            continue
        if allowed_systems:
            codings = ((resource.get("code") or {}).get("coding") or [])
            first = codings[0] if codings else None
            system = first.get("system") if isinstance(first, dict) else None
            if system not in allowed_systems:
                continue
        return True
    return False


def _json_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _read_selected_source(
    mode: str,
    uploaded_file,
    local_file: str | None,
) -> tuple[str | None, str | None, str | None]:
    """Return text, display name, and an explicit local path when one exists."""
    if mode == "Upload HL7":
        if uploaded_file is None:
            return None, None, None
        return (
            uploaded_file.getvalue().decode("utf-8", errors="ignore"),
            uploaded_file.name,
            None,
        )

    if not local_file:
        return None, None, None
    path = Path(local_file)
    return (
        path.read_text(encoding="utf-8", errors="ignore"),
        str(path),
        str(path.resolve()),
    )


st.title("🧪 PIQI Connectathon 43")
st.caption(
    "MediLacra → PIQITT → FHIR baseline → controlled PIQI-shaped mutants. "
    "This page is the local Connectathon workbench."
)

nav1, nav2 = st.columns(2)
with nav1:
    st.page_link("pages/8_Disco_Inferno.py", label="Generate source data in Disco Inferno", icon="🔥")
with nav2:
    st.page_link("medi_lacra_app.py", label="Generate ordinary MediLacra HL7", icon="🧬")

st.success(
    "The local evidence pack can now be executed against external endpoints. "
    "Exact request/response bytes are preserved before normalization or comparison."
)

with st.expander("Experiment contract", expanded=False):
    st.markdown(
        """
- **MediLacra** creates the synthetic source reality and HL7.
- **PIQITT** remains the source of truth for HL7 → FHIR conversion; this branch loads its existing converter rather than copying it.
- **Disco Inferno** introduces exactly one declared FHIR mutation per mutant case.
- The untouched FHIR baseline is preserved alongside each mutant and its machine-readable manifest.
- Local preflight is deliberately weaker than PIQI/US Core conformance: it only proves the artifacts are shaped well enough for the next ingestion step.
        """
    )

st.markdown("## 1. Select source and materialize FHIR")

piqitt_default = str(default_piqitt_repo())
piqitt_repo = st.text_input(
    "Local PIQITT repository",
    value=os.getenv("PIQITT_REPO", piqitt_default),
    help="Expected to contain scripts/fhir_convert_backend.py. Default assumes medilacra_connect and piqitt are sibling folders.",
)

source_timezone = st.text_input(
    "Source timezone for HL7 timestamps without an offset (optional)",
    value=os.getenv("MEDILACRA_SOURCE_TZ", ""),
    placeholder="America/New_York",
    help=(
        "Use an IANA timezone when the source system emits local clock times without an offset. "
        "If MSH-7 already includes an offset, that source offset wins. If this is blank and no "
        "offset exists, the conversion process's local timezone is used."
    ),
)

backend = backend_path(piqitt_repo)
if backend.exists():
    st.success(f"PIQITT converter found: {backend}")
else:
    st.error(f"PIQITT converter not found: {backend}")

source_mode = st.radio("HL7 source", ["Existing MediLacra / Disco output", "Upload HL7"], horizontal=True)
local_files = _discover_hl7_files()
selected_local: str | None = None
uploaded = None

if source_mode == "Existing MediLacra / Disco output":
    if local_files:
        selected_path = st.selectbox(
            "Existing HL7 file",
            local_files,
            format_func=lambda path: f"{path.name} — {path.parent}",
        )
        selected_local = str(selected_path)
    else:
        st.warning("No local HL7 files found under output/ or Disco Inferno output directories.")
else:
    uploaded = st.file_uploader("Drop one MediLacra HL7/.txt file", type=["hl7", "txt"])

source_text, source_name, source_path = _read_selected_source(source_mode, uploaded, selected_local)
message_summary: list[dict] = []
message_index = 1

if source_text and backend.exists():
    try:
        message_summary = inspect_hl7_text(source_text, piqitt_repo=piqitt_repo)
    except Exception as exc:
        st.exception(exc)

if message_summary:
    st.caption(f"{len(message_summary)} HL7 message(s) found in {source_name}")
    st.dataframe(pd.DataFrame(message_summary), use_container_width=True, hide_index=True)
    options = [row["message_index"] for row in message_summary]
    message_index = st.selectbox(
        "Message to materialize",
        options,
        format_func=lambda index: (
            f"#{index} — "
            + next(row["message_type"] for row in message_summary if row["message_index"] == index)
        ),
    )

materialize_disabled = not source_text or not backend.exists() or not message_summary
if st.button(
    "Materialize FHIR baseline with PIQITT",
    type="primary",
    use_container_width=True,
    disabled=materialize_disabled,
):
    try:
        bundle, metadata = convert_hl7_text(
            source_text,
            message_index=int(message_index),
            piqitt_repo=piqitt_repo,
            source_timezone=source_timezone.strip() or None,
        )
        metadata.update(
            build_source_provenance(
                source_text,
                source_name=source_name,
                source_path=source_path,
                medilacra_root=MEDILACRA_ROOT,
                piqitt_repo=piqitt_repo,
            )
        )
        st.session_state["piqi43_baseline"] = bundle
        st.session_state["piqi43_source_metadata"] = metadata
        st.session_state.pop("piqi43_run", None)
        st.success("FHIR baseline materialized from PIQITT's existing converter.")
    except Exception as exc:
        st.exception(exc)

baseline = st.session_state.get("piqi43_baseline")
source_metadata = st.session_state.get("piqi43_source_metadata", {})

if baseline:
    counts = _bundle_resource_counts(baseline)
    preflight = preflight_bundle(baseline)
    metric_cols = st.columns(4)
    metric_cols[0].metric("FHIR entries", len(baseline.get("entry", [])))
    metric_cols[1].metric("Patients", counts.get("Patient", 0))
    metric_cols[2].metric("Observations", counts.get("Observation", 0))
    metric_cols[3].metric("Local preflight", preflight["status"])

    st.dataframe(
        pd.DataFrame([{"Resource": key, "Count": value} for key, value in sorted(counts.items())]),
        use_container_width=True,
        hide_index=True,
    )

    if not counts.get("Observation"):
        st.warning(
            "This FHIR baseline has no Observation resource. Observation-targeting Connectathon cases will be hidden; "
            "an ORU or ADT with OBX content is a better source for the initial PIQI pack."
        )

    with st.expander("Source provenance"):
        st.json(source_metadata)
    with st.expander("Baseline FHIR JSON"):
        st.json(baseline)
    st.download_button(
        "Download baseline FHIR JSON",
        data=_json_bytes(baseline),
        file_name="baseline.fhir.json",
        mime="application/fhir+json",
        use_container_width=True,
    )

st.markdown("## 2. Build controlled Connectathon cases")
scenario_labels = {scenario["case_id"]: scenario["label"] for scenario in DEFAULT_SCENARIOS}
if baseline:
    applicable_scenarios = [scenario for scenario in DEFAULT_SCENARIOS if _scenario_applicable(baseline, scenario)]
    unavailable_scenarios = [scenario for scenario in DEFAULT_SCENARIOS if scenario not in applicable_scenarios]
else:
    applicable_scenarios = list(DEFAULT_SCENARIOS)
    unavailable_scenarios = []

if unavailable_scenarios:
    st.caption(
        "Not applicable to this baseline: "
        + "; ".join(scenario["label"] for scenario in unavailable_scenarios)
    )

available_case_ids = [scenario["case_id"] for scenario in applicable_scenarios]
selected_case_ids = st.multiselect(
    "Cases",
    options=available_case_ids,
    default=available_case_ids,
    format_func=lambda case_id: scenario_labels[case_id],
    help="The three non-control SAM targets remain provisional until the track confirms the rubric targets.",
)
mutation_seed = int(st.number_input("Mutation seed", value=666, step=1))

if st.button(
    "Build local PIQI scenario pack",
    type="primary",
    use_container_width=True,
    disabled=not baseline or not selected_case_ids,
):
    try:
        run = build_scenario_pack(
            baseline,
            output_root=RESULT_ROOT,
            case_ids=selected_case_ids,
            mutation_seed=mutation_seed,
            source_metadata=source_metadata,
        )
        st.session_state["piqi43_run"] = run
        st.success(f"Scenario pack created: {run['run_id']}")
    except Exception as exc:
        st.exception(exc)

run = st.session_state.get("piqi43_run")
if run:
    st.markdown("### Local evidence pack")
    case_frame = pd.DataFrame(run["cases"])
    display_columns = [
        "case_id",
        "operator",
        "resource",
        "path",
        "expected_sam",
        "expected_status",
        "preflight",
        "changed_paths",
    ]
    st.dataframe(case_frame[display_columns], use_container_width=True, hide_index=True)

    run_dir = Path(run["run_dir"])
    st.download_button(
        "Download complete local Connectathon pack",
        data=zip_run_directory(run_dir),
        file_name=f"PIQI_CONNECTATHON_43_{run['run_id']}.zip",
        mime="application/zip",
        use_container_width=True,
    )
    st.caption(f"Local artifact directory: {run_dir}")

    selected_case = st.selectbox(
        "Inspect case",
        [case["case_id"] for case in run["cases"]],
        format_func=lambda case_id: scenario_labels.get(case_id, case_id),
    )
    case = load_case(run_dir, selected_case)
    manifest = case["manifest"]

    mutation = manifest["mutation"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Operator", mutation["operator"])
    c2.metric("Expected SAM", manifest.get("expected", {}).get("sam") or "Control")
    c3.metric("Changed JSON paths", len(manifest.get("changed_paths", [])))

    baseline_tab, mutant_tab, manifest_tab, preflight_tab = st.tabs(
        ["Baseline", "Mutant", "Manifest", "Preflight"]
    )
    with baseline_tab:
        st.json(case["baseline"])
        st.download_button(
            "Download case baseline",
            data=_json_bytes(case["baseline"]),
            file_name=f"{selected_case}_baseline.fhir.json",
            mime="application/fhir+json",
            key=f"baseline-{run['run_id']}-{selected_case}",
        )
    with mutant_tab:
        st.json(case["mutant"])
        st.download_button(
            "Download case mutant",
            data=_json_bytes(case["mutant"]),
            file_name=f"{selected_case}_mutant.fhir.json",
            mime="application/fhir+json",
            key=f"mutant-{run['run_id']}-{selected_case}",
        )
    with manifest_tab:
        st.json(manifest)
        st.caption(
            "The manifest is the corruption receipt. For non-control cases, exactly one JSON path must differ from baseline."
        )
    with preflight_tab:
        st.json(case["preflight"])
        st.warning(
            "LOCAL_ONLY preflight is not an HL7/US Core/PIQI conformance claim and is not evidence that the track endpoint accepted the payload."
        )

st.markdown("## 3. Endpoint execution and comparison")
st.caption(
    "Execute the same controlled cases against one or more endpoints. Raw request and response bytes, "
    "hashes, HTTP metadata, normalized JSON, and pairwise disagreement paths are written back into the evidence pack."
)

with st.expander("Endpoint contract", expanded=False):
    st.markdown(
        """
**FHIR Bundle JSON** posts each case's FHIR Bundle directly. Use this only for endpoints that explicitly accept FHIR JSON
(for example a FHIR repository, proxy, or Connectathon test client). A successful POST here is transport evidence, not PIQI scoring.

**PIQI reference service** wraps already-converted PIQI `MessageData` in the current open-source `PIQIRequest` envelope.
The reference service currently exposes `/PIQI/ScoreMessage` and `/PIQI/ScoreAuditMessage`. MediLacra deliberately does **not**
treat raw FHIR JSON as PIQI `MessageData`; provide a directory containing `<case_id>.piqi.json` files produced by a real
FHIR → PIQI conversion step.
        """
    )

def _endpoint_editor(prefix: str, default_name: str):
    enabled = st.checkbox("Enable endpoint", value=(prefix == "a"), key=f"piqi43-{prefix}-enabled")
    if not enabled:
        return None, None

    name = st.text_input("Endpoint name", value=default_name, key=f"piqi43-{prefix}-name")
    url = st.text_input(
        "Full POST URL",
        value="",
        placeholder="http://localhost:52773/csp/piqitt/fhir/Bundle",
        key=f"piqi43-{prefix}-url",
    )
    mode_label = st.selectbox(
        "Payload contract",
        ["FHIR Bundle JSON", "PIQI reference service (PIQIRequest)"],
        key=f"piqi43-{prefix}-mode",
    )
    payload_mode = "fhir_bundle" if mode_label == "FHIR Bundle JSON" else "piqi_request"

    auth_label = st.selectbox(
        "Authentication",
        ["None", "Basic auth", "Header / API key"],
        key=f"piqi43-{prefix}-auth",
    )
    auth_mode = {"None": "none", "Basic auth": "basic", "Header / API key": "header"}[auth_label]
    username = ""
    password = ""
    header_name = ""
    header_value = ""
    if auth_mode == "basic":
        username = st.text_input("Username", key=f"piqi43-{prefix}-username")
        password = st.text_input("Password", type="password", key=f"piqi43-{prefix}-password")
    elif auth_mode == "header":
        header_name = st.text_input(
            "Header name",
            value="X-API-Key",
            key=f"piqi43-{prefix}-header-name",
        )
        header_value = st.text_input(
            "Header value",
            type="password",
            key=f"piqi43-{prefix}-header-value",
        )

    verify_tls = st.checkbox("Verify TLS certificate", value=True, key=f"piqi43-{prefix}-verify-tls")
    timeout_seconds = float(
        st.number_input(
            "Timeout (seconds)",
            min_value=1,
            max_value=300,
            value=30,
            key=f"piqi43-{prefix}-timeout",
        )
    )

    message_dir = None
    model_mnemonic = "PAT_CLINICAL_V1"
    rubric_mnemonic = "USCDI_V3"
    contributor_id = "MediLacra"
    data_source_id = "MediLacra Connectathon 43"
    if payload_mode == "piqi_request":
        st.warning(
            "This mode requires PIQI-format MessageData. Raw FHIR is intentionally not substituted for the conversion step."
        )
        message_dir = st.text_input(
            "PIQI MessageData directory",
            placeholder="connectathon/piqi_messages/<run_id>",
            help="Expected files: <case_id>.piqi.json",
            key=f"piqi43-{prefix}-message-dir",
        )
        model_mnemonic = st.text_input(
            "PIQI model mnemonic",
            value="PAT_CLINICAL_V1",
            key=f"piqi43-{prefix}-model",
        )
        rubric_mnemonic = st.text_input(
            "Evaluation rubric mnemonic",
            value="USCDI_V3",
            key=f"piqi43-{prefix}-rubric",
        )
        contributor_id = st.text_input(
            "Contributor ID",
            value="MediLacra",
            key=f"piqi43-{prefix}-contributor",
        )
        data_source_id = st.text_input(
            "Data source ID",
            value="MediLacra Connectathon 43",
            key=f"piqi43-{prefix}-data-source",
        )

    if not name.strip() or not url.strip():
        return None, message_dir

    return (
        EndpointConfig(
            name=name.strip(),
            url=url.strip(),
            payload_mode=payload_mode,
            timeout_seconds=timeout_seconds,
            verify_tls=verify_tls,
            auth_mode=auth_mode,
            username=username,
            password=password,
            header_name=header_name,
            header_value=header_value,
            model_mnemonic=model_mnemonic,
            rubric_mnemonic=rubric_mnemonic,
            contributor_id=contributor_id,
            data_source_id=data_source_id,
        ),
        message_dir,
    )

ep_col_a, ep_col_b = st.columns(2)
with ep_col_a:
    st.markdown("### Endpoint A")
    endpoint_a, message_dir_a = _endpoint_editor("a", "IRIS FHIR")
with ep_col_b:
    st.markdown("### Endpoint B")
    endpoint_b, message_dir_b = _endpoint_editor("b", "PIQI endpoint")

endpoint_configs = [endpoint for endpoint in (endpoint_a, endpoint_b) if endpoint is not None]
piqi_message_dirs = {}
if endpoint_a is not None and endpoint_a.payload_mode == "piqi_request" and message_dir_a:
    piqi_message_dirs[endpoint_a.name] = message_dir_a
if endpoint_b is not None and endpoint_b.payload_mode == "piqi_request" and message_dir_b:
    piqi_message_dirs[endpoint_b.name] = message_dir_b

if run:
    run_dir = Path(run["run_dir"])
    if st.button(
        "Execute current pack against enabled endpoints",
        type="primary",
        use_container_width=True,
        disabled=not endpoint_configs,
    ):
        try:
            execution = execute_run(
                run_dir,
                endpoints=endpoint_configs,
                piqi_message_dirs=piqi_message_dirs,
            )
            st.session_state["piqi43_endpoint_execution"] = execution
            st.success(
                f"Endpoint execution complete: {execution['execution_kind']} / {execution['status']}"
            )
        except Exception as exc:
            st.exception(exc)
else:
    st.info("Build a local PIQI scenario pack before endpoint execution.")

execution = st.session_state.get("piqi43_endpoint_execution")
if execution and run:
    st.markdown("### Endpoint evidence")
    m1, m2, m3 = st.columns(3)
    m1.metric("Execution kind", execution.get("execution_kind", ""))
    m2.metric("Endpoints", execution.get("endpoint_count", 0))
    m3.metric("Status", execution.get("status", ""))

    execution_rows = []
    comparison_rows = []
    for case_result in execution.get("cases", []):
        case_id = case_result.get("case_id")
        for endpoint_result in case_result.get("endpoints", []):
            endpoint_meta = endpoint_result.get("endpoint", {})
            execution_rows.append(
                {
                    "case_id": case_id,
                    "endpoint": endpoint_meta.get("name"),
                    "mode": endpoint_meta.get("payload_mode"),
                    "status": endpoint_result.get("status_code"),
                    "HTTP ok": endpoint_result.get("ok"),
                    "transport ok": endpoint_result.get("transport_ok"),
                    "PIQI response": endpoint_result.get("piqi_response_recognized"),
                    "elapsed ms": endpoint_result.get("elapsed_ms"),
                    "request sha256": endpoint_result.get("request_sha256"),
                    "response sha256": endpoint_result.get("response_sha256"),
                }
            )
        for pair in case_result.get("comparison", {}).get("pairwise", []):
            comparison_rows.append({"case_id": case_id, **pair})

    if execution_rows:
        st.dataframe(pd.DataFrame(execution_rows), use_container_width=True, hide_index=True)
    if comparison_rows:
        st.markdown("### Pairwise normalized comparison")
        st.dataframe(pd.DataFrame(comparison_rows), use_container_width=True, hide_index=True)
        selected_comparison = st.selectbox(
            "Inspect disagreement paths",
            range(len(comparison_rows)),
            format_func=lambda index: (
                f"{comparison_rows[index]['case_id']} — "
                f"{comparison_rows[index]['left']} vs {comparison_rows[index]['right']}"
            ),
        )
        st.json(comparison_rows[selected_comparison])
    elif execution.get("endpoint_count", 0) < 2:
        st.caption("Configure two endpoints to produce a pairwise agreement comparison.")

    st.download_button(
        "Download evidence pack including endpoint results",
        data=zip_run_directory(Path(run["run_dir"])),
        file_name=f"PIQI_CONNECTATHON_43_{run['run_id']}_EXECUTED.zip",
        mime="application/zip",
        use_container_width=True,
    )
