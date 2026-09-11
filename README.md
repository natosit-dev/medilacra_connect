# medilacra_connect v1.0

**A local healthcare-data experiment platform for generating synthetic HL7, introducing controlled information damage, and building reproducible PIQI validation artifacts.**

`medilacra_connect` is the consolidated Connectathon-facing form of MediLacra. It keeps the original MediLacra synthetic-data generator as the baseline, adds Disco Inferno as the controlled-corruption layer, and adds the PIQI Connectathon 43 workbench as the validation/evidence layer.

The central question remains:

> **What relationships survive transformation?**

This repository is intentionally local-first, inspectable, and synthetic-data-only. It is a working experiment platform, not a clinical system and not a production interoperability server.

---

## What v1.0 contains

```text
MediLacra synthetic reality
        |
        +--> ordinary HL7 v2 output
        |
        +--> Disco Inferno
        |      |
        |      +--> controlled representational damage
        |      +--> zero-delta control
        |      +--> deterministic manifests / comparison artifacts
        |      +--> FHIR mutation primitives used by PIQI cases
        |
        +--> PIQI Connectathon 43 workbench
               |
               +--> select MediLacra or Disco HL7
               +--> convert HL7 -> FHIR through PIQITT
               +--> normalize a self-contained FHIR control
               +--> run a baseline quality gate
               +--> materialize controlled one-defect mutants
               +--> preserve baseline, mutant, manifest, hashes, provenance
               +--> run local structural preflight
               +--> export a complete evidence ZIP
```

The v1.0 boundary stops at **local PIQI evidence generation**. External PIQI endpoint submission is deliberately not claimed as complete and remains visibly disabled in the workbench.

---

## Definitions

These definitions describe how the terms are used **in this repository**.

### MediLacra

The baseline synthetic healthcare-data generator. MediLacra creates fake patients, encounters, observations, transactions, vitals, labs, and HL7 v2 messages. It can persist generated entities/messages to DuckDB and can optionally enrich synthetic data with public SDOH signals.

### medilacra_connect

The consolidated platform in this repository. It contains baseline MediLacra plus distinct experiment/validation tools layered on top of it rather than replacing the baseline generator.

### Disco Inferno

The controlled-corruption experiment. Disco Inferno starts from a generated MediLacra reality, preserves an untouched control, and applies declared deterministic damage to copies so the effect of the damage can be measured directly.

For PIQI work, Disco also supplies FHIR-level mutation primitives that enforce a one-declared-change experiment boundary.

### PIQI

The Patient Information Quality Improvement validation context targeted by the Connectathon workbench. In v1.0, `medilacra_connect` prepares clean control artifacts plus controlled PIQI-shaped failure cases and records the expected quality target for each case. External PIQI execution is not yet part of the accepted v1.0 boundary.

### PIQITT

A separate repository used as the authoritative local HL7 -> FHIR converter for this workflow.

`medilacra_connect` does **not** copy PIQITT's converter into this repository. The PIQI workbench loads the converter from a local PIQITT checkout so conversion provenance remains explicit.

Expected sibling layout:

```text
workspace/
├── medilacra_connect/
└── piqitt/
```

If PIQITT lives elsewhere, set `PIQITT_REPO` or enter the path in the PIQI page.

### Baseline / control

The unmutated FHIR representation used as the experimental reference. The baseline must pass the local control quality gate before mutant cases can be created.

### Mutant

A deep-copied baseline with exactly one declared information-quality mutation. Each mutant carries a manifest describing the operator, target resource/path, before/after value, hashes, and changed JSON path.

### Control quality gate

A set of checks applied **only to the unmutated baseline** before mutants are allowed. v1.0 checks include structural shape, coded Encounter class, UCUM quantities, elimination of caret-packed coded values, timezone-bearing clock datetimes, empty-extension cleanup, and a basic lipid plausibility check when the relevant values exist.

### Local preflight

A structural ingest-shape check for the baseline and mutants. A PASS means the Bundle is self-contained enough for the next step of the experiment. It is **not** a claim of full FHIR, US Core, HL7, or PIQI conformance and it is not evidence of external endpoint acceptance.

### Provenance

Machine-readable information describing where an artifact came from: HL7 hash, MediLacra revision, PIQITT revision and converter hash, source-file path when explicitly local, and Disco run metadata when applicable.

### Evidence pack

The generated run directory / ZIP containing the control gate, per-case baseline and mutant FHIR, mutation manifest, preflight results, and run manifest.

### HL7 v2

The pipe-delimited healthcare messaging representation generated by MediLacra and consumed by PIQITT in this workflow.

### FHIR

The resource-based representation produced by PIQITT and then normalized by the Connectathon layer into a self-contained collection for controlled validation experiments.

### UCUM

The unit coding system used to make numeric FHIR quantities explicit and machine-comparable. The control-normalization layer repairs known MediLacra/PIQITT unit representation issues before the baseline is accepted.

### SAM target

The named PIQI quality assertion recorded as the expected target for a scenario. In v1.0, the non-control SAM/dimension expectations remain **provisional** until they are exercised against the external track implementation.

---

## Quick local start

### Existing checkout

```bash
git switch main
git pull --ff-only origin main
python -m pip install -r requirements.txt
python -m streamlit run medi_lacra_app.py
```

Open the URL Streamlit prints, normally:

```text
http://localhost:8501
```

### First-time checkout

Clone both repositories next to one another:

```bash
git clone https://github.com/natosit-dev/medilacra_connect.git
git clone https://github.com/natosit-dev/piqitt.git
cd medilacra_connect
python -m pip install -r requirements.txt
python -m streamlit run medi_lacra_app.py
```

A virtual environment or Conda environment is recommended but not required by the repository layout.

If PIQITT is not a sibling folder:

```bash
export PIQITT_REPO=/path/to/piqitt
```

If source HL7 timestamps contain local clock times without an offset and your process timezone is not the sender timezone, you can make the source timezone explicit:

```bash
export MEDILACRA_SOURCE_TZ=America/New_York
```

The PIQI page also exposes this as an optional field. If MSH-7 already contains an explicit offset, the source offset takes precedence.

---

## The three v1.0 layers

### 1. Baseline MediLacra

Primary entry point:

```text
medi_lacra_app.py
```

MediLacra can generate:

- synthetic patients,
- encounters,
- observations,
- transactions,
- providers and order identifiers,
- ADT / ORU / DFT messages,
- synthetic lab ORM / ORU messages,
- vitals,
- Gender Harmony-style observations,
- optional public SDOH enrichments,
- local DuckDB persistence.

Default ordinary HL7 output:

```text
./output/*.hl7
```

The baseline generator remains useful independently of the Connectathon tools.

### 2. Disco Inferno

Streamlit page:

```text
pages/8_Disco_Inferno.py
```

Core experiment package:

```text
experiments/disco_inferno/
```

Disco Inferno produces an untouched representation plus controlled corruptions such as:

- dropping relationship identifiers,
- nulling selected facts,
- duplicating records,
- and FHIR-level remove/replace mutations used by the PIQI workbench.

The control must remain zero-delta. Mutation receipts and hashes make the experiment inspectable rather than relying on visual comparison.

When SDOH is disabled, the detached Disco worker blocks Requests-level outbound HTTP so "off" means both no enrichment in the artifact and no covered Requests traffic from that worker.

### 3. PIQI Connectathon 43

Streamlit page:

```text
pages/9_PIQI_Connectathon_43.py
```

Core package:

```text
connectathon/
```

The page performs this local workflow:

```text
MediLacra / Disco HL7
        |
        v
PIQITT conversion
        |
        v
raw FHIR message Bundle
        |
        v
Connectathon control normalization
        |
        v
control quality gate
        |
        +--> untouched control
        +--> Patient.identifier removed
        +--> Observation coding system removed
        +--> LOINC code replaced with a known non-member
        |
        v
local preflight + manifests + hashes + provenance
        |
        v
PIQI_CONNECTATHON_43_<run-id>.zip
```

The invalid-member case is restricted to LOINC-coded observations so the mutation actually represents a terminology-membership failure rather than changing an arbitrary local code.

---

## Current PIQI v1.0 scenarios

| Case | Mutation | Intended local experiment |
|---|---|---|
| `case_000_control` | none | Prove zero introduced change |
| `case_001_availability` | remove `Patient.identifier` | Missing populated attribute |
| `case_002_code_system` | remove `Observation.code.coding[0].system` | Coding-system availability |
| `case_003_invalid_member` | replace a LOINC code with `ZZZ-NOT-A-VALID-CODE` | Known terminology non-member |

Every non-control case is expected to change exactly one JSON path. All cases preserve the same baseline hash within a run.

---

## Control normalization performed by the PIQI layer

PIQITT remains responsible for HL7 -> FHIR conversion. `medilacra_connect` then performs a narrow Connectathon control cleanup so the experiment does not begin with known representation defects.

Current cleanup includes:

- convert the PIQITT message Bundle to a FHIR `collection`,
- remove `MessageHeader` transport semantics from the PIQI artifact,
- add stable `urn:uuid:` `fullUrl` values,
- rewrite internal references to those stable URLs,
- map known Encounter classes to system-qualified FHIR coding,
- normalize known quantity units to UCUM,
- materialize known coded values from PIQITT `valueString` fall-throughs,
- repair CE/CWE/CNE compatibility using original HL7 datatype provenance,
- preserve explicit source timestamp offsets and use an explicit/source-local timezone for otherwise-naive clock times,
- remove empty nested extension values.

This cleanup is intentionally narrow. It is not a general-purpose FHIR repair engine.

---

## Output locations

Ordinary MediLacra HL7:

```text
./output/
```

Disco Inferno runs:

```text
./experiments/disco_inferno/output/<run-id>/
```

PIQI local evidence packs:

```text
./connectathon/results/<run-id>/
```

Typical PIQI run layout:

```text
connectathon/results/<run-id>/
├── control_quality_gate.json
├── run_manifest.json
└── cases/
    ├── case_000_control/
    │   ├── baseline.fhir.json
    │   ├── mutant.fhir.json
    │   ├── manifest.json
    │   └── preflight.json
    └── ...
```

Generated output is generally ignored by Git. The human-readable acceptance records live under `docs/`.

---

## v1.0 acceptance evidence

The accepted local PIQI run is documented separately at:

```text
docs/PIQI_V1_BASELINE_RESULTS_2026-09-11.md
```

The consolidation/build/migration process, prompt provenance, review fixes, and decision log are recorded at:

```text
docs/MEDILACRA_CONNECT_V1_0_PROCESS_2026-09-11.md
```

The earlier Disco migration record remains at:

```text
docs/DISCO_INFERNO_MIGRATION_2026-09-10.md
```

The original Connectathon planning/build notes remain under:

```text
docs/connectathon/
```

---

## Testing

The permanent Connectathon smoke workflow checks the consolidated PIQI surface against **PIQITT `main`**.

The v1.0 regression surface includes tests for:

- zero-delta controls,
- exactly-one-path FHIR mutations,
- terminology-bound invalid-member mutation,
- baseline quality gating,
- control normalization,
- PIQITT CE/CWE/CNE compatibility,
- explicit source timezone preservation,
- PIQITT backend cache invalidation when converter code changes,
- uploaded-file versus local-path provenance separation,
- end-to-end PIQITT -> control -> scenario-pack generation.

---

## Current v1.0 boundary / non-claims

v1.0 **does** provide:

- a usable synthetic HL7 baseline,
- deterministic controlled corruption,
- PIQITT-backed FHIR materialization,
- baseline quality gating,
- controlled PIQI-shaped mutants,
- machine-readable mutation receipts,
- local structural preflight,
- reproducible evidence-pack generation.

v1.0 **does not claim**:

- external PIQI endpoint acceptance,
- full US Core conformance,
- production FHIR-server behavior,
- clinical validity of synthetic values,
- complete terminology validation,
- production-grade security or deployment packaging.

External PIQI execution is the next major boundary after v1.0.

---

## Repository map

```text
medilacra_connect/
├── medi_lacra_app.py                 # baseline MediLacra UI
├── hl7_demo/                         # synthetic entities + HL7 generation
├── pages/
│   ├── 8_Disco_Inferno.py
│   └── 9_PIQI_Connectathon_43.py
├── experiments/
│   └── disco_inferno/                # controlled corruption
├── connectathon/                     # PIQI control/mutation/evidence layer
├── tests/                            # baseline + experiment regressions
├── docs/                             # build records and acceptance evidence
├── output/                           # ordinary generated HL7 (local/generated)
└── connectathon/results/             # PIQI evidence runs (local/generated)
```

---

## Safety and privacy

This repository is for **synthetic and public data only**.

Do not commit or load:

- PHI,
- production patient data,
- client extracts,
- proprietary schemas you do not have permission to publish,
- credentials,
- API keys,
- local `.env` files,
- sensitive forensic or employment material.

MediLacra's fake patients are fake. The data-quality problems are intentionally real.

---

## Name

**MediLacra** suggests medical simulacra: representations that are synthetic but structured enough to expose how healthcare-data systems preserve, transform, or destroy meaning.

`medilacra_connect` is the place where those representations are deliberately moved, damaged, converted, and checked.
