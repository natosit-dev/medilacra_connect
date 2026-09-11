# PIQI Connectathon 43 — Endpoint Execution Boundary

**Status:** implementation slice in progress  
**Date:** 2026-09-11  
**Branch:** `feature/piqi-endpoint-execution`

## Purpose

Extend the local PIQI-43 evidence-pack workflow from artifact generation into endpoint execution without collapsing distinct interfaces into one another.

The Connectathon Scenario 2 target is endpoint agreement: the same controlled patient payload should be evaluated by independent PIQI-enabled endpoints using the same model/rubric, with raw Evaluation/Audit reports preserved before comparison.

## Explicit boundaries

MediLacra currently produces controlled FHIR Bundle artifacts. The official open-source PIQI reference service does **not** accept a FHIR Bundle directly at its scoring controller. Its current `PIQIRequest` requires:

- `ContributorID`
- `DataSourceID`
- `MessageID`
- `PIQIModelMnemonic`
- `EvaluationRubricMnemonic`
- `MessageData`

`MessageData` is PIQI-format message content. FHIR-to-PIQI conversion is a separate transformation concern and is not silently invented in this module.

The current reference implementation exposes:

- `POST /PIQI/ScoreMessage`
- `POST /PIQI/ScoreAuditMessage`

The reference data currently includes the clinical model mnemonic `PAT_CLINICAL_V1` and evaluation rubrics including `USCDI_V3`.

## Endpoint modes

### `fhir_bundle`

Posts the materialized case Bundle directly as JSON. This is appropriate for:

- FHIR-shaped transport/persistence endpoints
- Connectathon clients/proxies that explicitly accept FHIR Bundle JSON
- local IRIS transport experiments

This mode exercises transport only. It does **not** claim PIQI evaluation occurred.

### `piqi_request`

Posts a current-reference-service `PIQIRequest` envelope. This mode requires pre-converted PIQI `MessageData` for every case. The expected file convention is:

```text
<message-data-directory>/<case_id>.piqi.json
```

MediLacra refuses to substitute raw FHIR JSON for PIQI MessageData.

## Evidence preservation

For every case and endpoint, execution writes under:

```text
cases/<case_id>/endpoint_results/<endpoint>/
```

Artifacts include:

- exact request bytes sent
- SHA-256 of request bytes
- exact raw response bytes
- SHA-256 of response bytes
- parsed JSON response when possible
- normalized response when possible
- HTTP status/reason/headers
- elapsed client time
- redacted endpoint metadata
- execution error text, if transport failed

Credentials are never written to the evidence pack. Persisted endpoint metadata records only whether a credential was present and, for custom-header auth, the header name.

## PIQI response normalization

When a response matches the current open-source `PIQIResponse` shape, comparison removes only known process/identity metadata that should not determine endpoint agreement, including processing time/date and message identifiers.

The normalized comparison retains:

- success/failure state
- error message
- evaluation rubric
- message-level score counts and PIQI scores
- class-level score counts and PIQI scores
- informational evaluation results
- plausibility results
- audited message

Raw responses remain authoritative evidence.

If a response is JSON but is not recognized as `PIQIResponse`, its complete canonical JSON is used as the normalized comparison artifact rather than guessing a schema.

## Pairwise comparison

For each case, endpoint normalized artifacts are flattened to JSON leaf paths and compared pairwise. The comparison records exact differing paths rather than reducing disagreement to a single boolean.

This is deliberately a structural/semantic JSON comparison layer, not a claim that PIQI report prototypes are final. The Connectathon page itself notes that standardized PIQI Evaluation Report structures are still being developed during the track.

## Run-level state

A scenario pack now distinguishes:

- `FHIR_TRANSPORT_ONLY` — external FHIR transport was exercised, but no PIQI service evaluation occurred
- `PIQI_EVALUATION` — at least one configured endpoint used the `PIQIRequest` interface

This prevents a successful POST to a FHIR repository from being mislabeled as a successful PIQI evaluation.

## Source alignment

The implementation boundary is based on the current PIQI Alliance reference application and Connectathon material available on 2026-09-11:

- `piqiframework/reference_application/PIQI_Engine.Server/Controllers/PIQIController.cs`
- `piqiframework/reference_application/PIQI.Components/ProcessingClasses/PIQIRequest.cs`
- `piqiframework/reference_application/PIQI.Components/ProcessingClasses/PIQIResponse.cs`
- `piqiframework/reference_application/PIQI.Components/ProcessingClasses/PIQIStatResponse.cs`
- `piqiframework/reference_application/PIQI_Engine.Server/ReferenceData/Models/ModelLibrary.json`
- `piqiframework/reference_application/PIQI_Engine.Server/ReferenceData/Evaluations/EvaluationProfileLibrary.json`
- `piqiframework/transformationTemplates` for the separate FHIR R4 → PIQI Liquid-template transformation layer

## Next integration seam

Once a repeatable FHIR → PIQI transformation runner is available, the same scenario pack can generate `<case_id>.piqi.json` files and drive the official reference service without changing endpoint execution, evidence storage, or comparison logic.
