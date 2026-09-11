# PIQI v1 Local Baseline Results

**Repository:** `natosit-dev/medilacra_connect`  
**Evidence date:** 2026-09-11  
**Document version:** 1.0  
**Evidence run:** `20260911T085037-0400`  
**Artifact:** `PIQI_CONNECTATHON_43_20260911T085037-0400.zip`  
**Status:** LOCAL ACCEPTANCE PASS  
**External PIQI execution:** NOT RUN  

---

# Purpose

This document records the local acceptance evidence supplied for the PIQI Connectathon 43 module before the repository was closed as `medilacra_connect` v1.0.

The evidence pack proves the local experiment machinery can:

1. take MediLacra / Disco HL7,
2. materialize FHIR using PIQITT,
3. normalize a clean control representation,
4. pass the local baseline quality gate,
5. preserve one invariant baseline across all cases,
6. create deterministic one-defect mutants,
7. produce zero delta for the control,
8. preserve per-case manifests, hashes, provenance, and preflight results.

This is deliberately **not** evidence that an external PIQI endpoint accepted or scored the artifacts.

---

# Important v1.0 provenance note

The uploaded acceptance ZIP was generated from repository revision:

```text
6c551d97e9bbe422f2c1575ec13482a86d98941d
```

During the final v1.0 review, the code was hardened in four additional areas:

- naive FHIR clock timestamps no longer receive a fabricated `Z`; an explicit HL7 offset is preserved when available, with configured/source-local timezone fallback otherwise,
- invalid-member mutations are restricted to LOINC-coded observations,
- PIQITT converter caching is invalidated when converter file content changes and the converter SHA is recorded,
- uploaded filenames are no longer eligible for local-file provenance unless an explicit local source path was supplied.

Therefore the baseline SHA recorded below is the exact hash of the **accepted uploaded evidence run**, not a promise that a newly regenerated post-hardening v1.0 control will have the same SHA.

The hardening does not invalidate the core experimental observations from this evidence pack. In particular, the observed `case_003_invalid_member` mutation already targeted a LOINC observation (`39156-5`), so it was already inside the stricter v1.0 terminology boundary. The timestamp representation itself will differ when the same source is regenerated under the corrected timezone behavior.

---

# Run Summary

The run manifest reported:

```text
run_id:                 20260911T085037-0400
mutation_seed:          666
baseline_control_gate:  PASS
external_piqi_execution: NOT_RUN
```

Invariant baseline SHA-256:

```text
ecb65ea668d7e52b38846424357c12ea7a9801cabfdba13d61cdc233d1864a32
```

Every case in the evidence pack records this same baseline SHA.

---

# Source Provenance

The accepted run was generated from a Disco Inferno HL7 artifact:

```text
Disco run ID: 20260910T130920-0400
Source message type: ADT^A01
Selected message index: 1
Messages in source file: 20
Labs: enabled
SDOH output: disabled
```

Source HL7 SHA-256:

```text
036cf09a0f0e4bfd063c7095a70c0e3a089705349d4c195ab95e7e63e0bc8b2c
```

Disco manifest SHA-256:

```text
61860cda9f33244fe83828b09c11064fc25bf096b80f024919d269b76736569c
```

PIQITT revision recorded in the run:

```text
a40300e4950d73ed192a2112cf516b4ec46a184b
```

The PIQITT backend used was:

```text
scripts/fhir_convert_backend.py
```

The local Connectathon compatibility boundary reported:

```text
OBX resources observed:       7
FHIR Observations observed:   7
CE-family values repaired:    3
Unresolved coded values:      0
```

This is the regression path that caught and then repaired PIQITT's `CWE` fall-through to caret-packed `valueString` before this evidence run was produced.

---

# Baseline FHIR Shape

The accepted control Bundle contained 9 retained resources:

| Resource type | Count |
|---|---:|
| Patient | 1 |
| Encounter | 1 |
| Observation | 7 |
| **Total** | **9** |

PIQITT originally produced a FHIR `message` Bundle. The local Connectathon normalization converted it to a self-contained `collection` and reported:

| Cleanup operation | Count / result |
|---|---:|
| MessageHeader removed | 1 |
| Stable `fullUrl` values added | 9 |
| Internal references rewritten | 15 |
| Encounter classes mapped | 1 |
| Quantities UCUM-normalized | 4 |
| Coded values materialized by general control cleanup | 0 |
| CE/CWE/CNE compatibility repairs before control cleanup | 3 |
| Clock dateTimes zoned in this historical run | 3 |
| Empty nested extension values removed | 3 |

The accepted observations included:

| Observation | Coding | Value representation |
|---|---|---|
| Systolic BP | LOINC `8480-6` | UCUM quantity `mm[Hg]` |
| Heart rate | LOINC `8867-4` | UCUM quantity `/min` |
| Oxygen saturation | LOINC `59408-5` | UCUM quantity `%` |
| Body mass index | LOINC `39156-5` | UCUM quantity `kg/m2` |
| Gender identity | LOINC `76691-5` | SNOMED CT coded value `446151000124109` / Male |
| Personal pronouns | LOINC `90778-2` | LOINC answer `LA29518-0` / he/him/his/his/himself |
| Sex parameter for clinical use | local/HL7 `SPCU` | coded value `M-T` / Apply male-typical settings |

The important semantic result was that the Gender Harmony coded values were no longer stored as caret-packed strings such as:

```text
446151000124109^Male^SCT
```

They were represented as proper FHIR `valueCodeableConcept` codings before the control gate ran.

---

# Control Quality Gate

Overall result:

```text
PASS
```

All recorded control checks passed:

| Check | Result | Recorded detail |
|---|---|---|
| `structural_preflight` | PASS | Self-contained FHIR collection shape; external PIQI ingest not yet exercised |
| `encounter.class.coded` | PASS | all Encounter.class values are system-qualified |
| `observation.quantity.ucum` | PASS | all coded quantities use UCUM |
| `observation.coded_values` | PASS | no caret-packed coded values remain in valueString |
| `datetime.timezone` | PASS | all dateTimes with clock time include timezone |
| `extensions.empty_values` | PASS | no empty valueString elements remain |
| `lipid.plausibility` | PASS | lipid relationship not present in this baseline |

The quality gate is intentionally applied to the unmutated control **before** any mutants are created. A dirty control is rejected rather than promoted into an experiment.

---

# Case Results

## `case_000_control`

Label:

```text
Control — untouched FHIR
```

Result:

```text
preflight: PASS
changed paths: 0
baseline SHA == mutant SHA
```

Mutant SHA-256:

```text
ecb65ea668d7e52b38846424357c12ea7a9801cabfdba13d61cdc233d1864a32
```

This is the required zero-delta control.

---

## `case_001_availability`

Label:

```text
Availability — remove Patient.identifier
```

Expected local target recorded in the evidence pack:

```text
SAM: ATTR_ISPOPULATED
Dimension: AV_UNPOP
Expected status: FAIL
```

Mutation:

```text
resource: Patient
operator: remove_element
path: identifier
changed JSON path: entry[0].resource.identifier
```

Before value:

```json
[
  {
    "system": "urn:mrn",
    "value": "RAD1819600"
  }
]
```

After value:

```text
absent
```

Mutant SHA-256:

```text
cbf37bb8c64aaa29e94dbb358778685ca98afb03f39f4b387762c665bba3dd7b
```

Preflight:

```text
PASS
```

Exactly one JSON path changed.

---

## `case_002_code_system`

Label:

```text
Availability — remove Observation coding system
```

Expected local target recorded in the evidence pack:

```text
SAM: CONCEPT_HASCODESYSTEM
Dimension: AV_UNPOP
Expected status: FAIL
```

Mutation:

```text
resource: Observation
operator: remove_coding_component
path: code.coding[0].system
changed JSON path: entry[5].resource.code.coding[0].system
```

Before value:

```text
http://loinc.org
```

After value:

```text
absent
```

Mutant SHA-256:

```text
eedb3d6b3016bd3085f3dbc4e52ea128dccd3d84b1d905f1bdbcfcb4f01086f7
```

Preflight:

```text
PASS
```

Exactly one JSON path changed.

---

## `case_003_invalid_member`

Historical evidence-run label:

```text
Conformity — replace Observation code with known non-member
```

The v1.0 implementation subsequently makes the LOINC boundary explicit in the scenario definition.

Expected local target recorded in the evidence pack:

```text
SAM: CONCEPT_ISVALIDMEMBER
Dimension: CONF_INCOMP
Expected status: FAIL
```

Mutation:

```text
resource: Observation
operator: replace_value
path: code.coding[0].code
changed JSON path: entry[5].resource.code.coding[0].code
```

The selected source Observation was LOINC-coded.

Before value:

```text
39156-5
```

After value:

```text
ZZZ-NOT-A-VALID-CODE
```

Mutant SHA-256:

```text
8b1e350206a1b46bc679a9596532194e44c57b52cc0b18631d62ed5002185e4a
```

Preflight:

```text
PASS
```

Exactly one JSON path changed.

---

# Experimental Invariants Demonstrated

The evidence pack establishes the following local invariants:

1. **The baseline is held constant across all cases.** Every case records the same baseline SHA-256.
2. **The control is truly zero-delta.** Its baseline and mutant hashes are identical and `changed_paths` is empty.
3. **Each non-control case changes exactly one declared JSON path.**
4. **The baseline must pass its quality gate before mutation.**
5. **Mutants remain structurally self-contained enough to pass local preflight.**
6. **Mutation receipts contain the target resource, entry index, resource ID, path, before value, after value, and hashes.**
7. **The conversion lineage is recorded.** The evidence includes MediLacra/Disco and PIQITT provenance.

These properties are more important than the specific random synthetic patient selected for this run. They establish the experimental harness itself.

---

# What This Evidence Does Not Establish

The run manifest explicitly records:

```text
external_piqi_execution: NOT_RUN
```

Therefore this evidence does **not** establish:

- external PIQI endpoint acceptance,
- the exact external SAM/dimension score for each mutant,
- full FHIR or US Core conformance,
- production endpoint interoperability,
- clinical validity of the synthetic values.

The non-control SAM/dimension targets are preserved as provisional experiment expectations until external execution is performed.

---

# Acceptance Conclusion

For the v1.0 local boundary, the run is accepted as successful evidence that the consolidated platform can execute:

```text
MediLacra / Disco source
        ↓
HL7
        ↓
PIQITT
        ↓
FHIR control normalization
        ↓
control quality gate — PASS
        ↓
zero-delta control + deterministic one-defect mutants
        ↓
local preflight — PASS
        ↓
provenance + manifests + hashes + evidence ZIP
```

The next major boundary is external PIQI execution and preservation/comparison of raw endpoint responses.
