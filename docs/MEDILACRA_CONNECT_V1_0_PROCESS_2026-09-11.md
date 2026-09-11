# medilacra_connect v1.0 Consolidation and Build Record

**Repository:** `natosit-dev/medilacra_connect`  
**Closeout date:** 2026-09-11  
**Document version:** 1.0  
**Status:** V1.0 CLOSEOUT  
**Primary integration branch:** `integrate/piqi-43`  
**Primary integration PR:** PR #3 — `Integrate PIQI Connectathon 43 workbench`  
**Purpose:** Record how baseline MediLacra, Disco Inferno, and the PIQI Connectathon 43 workbench were consolidated into the first accepted `medilacra_connect` platform boundary.

---

# Prompt History

The relevant user prompts are preserved verbatim at the top of this record. They define the requested grain and priority of the work more accurately than a retrospective architecture description alone.

## Prompt 1 — Create the consolidated Connectathon platform

> I feel like this is spread across a few chats so let's create a chat here to determine how to fold the valuable Medilacra branches into a single platform for the connectathon. I want to copy the medilacra baseline to this new repo:
> https://github.com/natosit-dev/medilacra_connect
> then merge the important branches into it:
> reality interface
> disco inferno
> structured sparsity
> connectathon/piqi-43
>
> I believe these are all good enough to be separate MediLacra tools. Let's start with copying the baseline. Once I confirm I can pull and run it locally, we'll do the first merge. So, copy Medilacra to medilacra_connect and walk me through pulling it to run locally

## Prompt 2 — Close the first migrated tool cleanly

> Looks good. I think we can consider this done. Record the results, all the trimmings, in a migration doc in /docs in medilacra_connect along with what was added and a decision log. Prompt history at the top

## Prompt 3 — Prioritize the Connectathon module

> I'm thinking the main connectathon piece should be next. It's the most important module. Take a look and see what needs to move to medilacra_connect

## Prompt 4 — Make PIQI-43 the architectural priority

> Sounds like you've got it covered. The order makes sense. Priority should be getting the piqi-43 module working. We can redo Disco Inferno if needed after, then PIQITT

## Prompt 5 — Local quality-gate failure

> Everything worked up to here

This prompt accompanied a local Streamlit screenshot showing:

```text
ValueError: Baseline failed the PIQI control quality gate; refusing to build mutants.
Failed checks: observation.coded_values
```

## Prompt 6 — Successful local evidence handoff

> Here's the output

This prompt accompanied the accepted local artifact:

```text
PIQI_CONNECTATHON_43_20260911T085037-0400.zip
```

## Prompt 7 — v1.0 closeout

> Ok, back to PIQI. Let's finalize this as v1.0 medilacra_connect. Update the readme to reflect what medilacra_connect is now- piqi validation, disco inferno on top of baseline Medilacra. Include simple commands to pull and run locally. Also include definitions in the README. create documentation of the process in docs and include my relevant prompts verbatim. Include baseline results as a separate MD in docs. Take your time

---

# Executive Summary

`medilacra_connect` v1.0 is the first consolidated local platform that treats baseline MediLacra, Disco Inferno, and PIQI validation as separate but composable layers.

The v1.0 repository is not a wholesale merge of every MediLacra experiment branch. That approach was explicitly rejected after branch-history inspection showed that the useful source branches contained inherited experiment history and unrelated files. The repository was instead assembled by preserving the original MediLacra baseline and selectively migrating only the code required for each accepted tool boundary.

The resulting v1.0 structure is:

```text
MediLacra
synthetic reality + ordinary HL7
        |
        +-----------------------------+
        |                             |
        v                             v
Disco Inferno                 PIQI Connectathon 43
controlled corruption        local validation workbench
        |                             |
        +---------- FHIR mutation ----+
                                      |
                                      v
                                PIQITT main
                              HL7 -> FHIR
                                      |
                                      v
                              clean FHIR control
                                      |
                                      v
                              control quality gate
                                      |
                       +--------------+--------------+
                       |              |              |
                    control       one-defect      evidence
                                  mutants          pack
```

PIQITT remains external and authoritative for conversion. Structured Sparsity and Reality Interface are not part of the accepted v1.0 runtime surface. They may be migrated later as independent tools, but they were not allowed to contaminate the PIQI-first closeout.

The local PIQI module was accepted after a real user-run evidence pack demonstrated a clean baseline, zero-delta control, deterministic one-path mutants, common baseline hashing, provenance, and PASS local preflight across all four v1 cases.

Before v1.0 closeout, a final code-review pass found four additional correctness/provenance issues. Those were fixed rather than documented as known v1 defects. The permanent Connectathon smoke workflow then passed against PIQITT `main`.

The accepted v1.0 boundary ends at local PIQI evidence generation. External PIQI endpoint execution remains explicitly `NOT_RUN` and is not claimed by this release state.

---

# 1. Baseline Repository Materialization

## Objective

Create a clean `medilacra_connect` repository from the useful current MediLacra baseline before integrating experiments.

Source:

```text
natosit-dev/medilacra
main
```

Target:

```text
natosit-dev/medilacra_connect
main
```

The baseline was copied as repository content rather than by preserving inherited experiment branch history.

Temporary upload debris under:

```text
.tmp.driveupload/
```

was deliberately excluded.

The first copy initially omitted several tracked-but-gitignored baseline directories. That was corrected before acceptance so the target matched the intended source baseline, including:

```text
data/
dev/
jupyter/
```

Canonical baseline copy commit:

```text
1ff173d48e8031b176b796e6cf9afb548f63cfbd
Restore full MediLacra baseline (excluding upload temp debris)
```

## Runtime dependency stabilization

The copied baseline imported several direct runtime dependencies that were not declared in `requirements.txt`.

The target requirements were corrected to include the dependencies actually imported by the baseline launch path, including:

```text
PyYAML
requests
numpy
joblib
scikit-learn
```

Dependency stabilization commit:

```text
8a6ffe261c1c1e14e421f824dea0224debafbc1b
Fix baseline runtime dependencies for local bootstrap
```

This established the clean platform baseline used for subsequent tool integrations.

---

# 2. Disco Inferno Migration

Disco Inferno was the first experiment migrated into the consolidated platform.

## Source-history finding

Source branch:

```text
natosit-dev/medilacra
experiment/disco-inferno
```

Inspection showed that the branch was not an isolated Disco-only branch. It inherited Structured Sparsity files/history.

A wholesale merge would therefore have imported a second experiment before its requested turn and created an artificial runtime dependency between tools.

## Migration choice

Only the Disco-specific surface was copied:

```text
pages/8_Disco_Inferno.py
experiments/disco_inferno/
tests/test_disco_inferno*.py
```

A small inherited `SyntheticCase` dependency on Structured Sparsity was localized into:

```text
experiments/disco_inferno/models.py
```

instead of importing Structured Sparsity.

Initial Disco integration PR:

```text
PR #1 — Integrate Disco Inferno as isolated MediLacra tool
```

Squash merge:

```text
853376f9a8bfa36d202f29eaadf5e3427cd70253
```

## SDOH-off network defect

Local testing showed that setting SDOH off correctly excluded SDOH values from the output, but Requests-level network activity could still escape through aliases imported before the initial guard was installed.

The fix remained entirely inside Disco's detached worker boundary. With SDOH disabled, the worker now blocks Requests at `Session.request`, preventing covered outbound Requests traffic while leaving the Streamlit host process unchanged.

Fix PR:

```text
PR #2 — Block outbound HTTP when Disco SDOH is disabled
```

Squash merge:

```text
ec3d4caf5dc0fcce81f7f87dc7c43952634f465d
```

The complete Disco migration and evidence record is preserved separately at:

```text
docs/DISCO_INFERNO_MIGRATION_2026-09-10.md
```

---

# 3. PIQI-43 Was Made the Integration Priority

After Disco acceptance, the user explicitly elevated the Connectathon module above the remaining experiments.

That changed the integration rule:

> PIQI-43 is allowed to reshape supporting Disco or PIQITT boundaries if required. Supporting experiments are not allowed to dictate the architecture of the primary Connectathon module.

This mattered because the source `connectathon/piqi-43` branch carried even more inherited history than Disco.

Source branch:

```text
natosit-dev/medilacra
connectathon/piqi-43
```

At inspection time it was approximately 50 commits ahead of source `main` and contained inherited Disco Inferno and Structured Sparsity history.

Therefore the branch itself was not merged.

---

# 4. Selective PIQI Migration

The useful PIQI surface was copied selectively into a clean target branch:

```text
integrate/piqi-43
```

The initial intended integration surface consisted of:

```text
.github/workflows/connectathon-smoke.yml
connectathon/__init__.py
connectathon/fhir_control.py
connectathon/piqitt_bridge.py
connectathon/preflight.py
connectathon/provenance.py
connectathon/run.py
connectathon/scenarios.py
docs/connectathon/IMPLEMENTATION_STATUS_2026-09-02.md
docs/connectathon/PIQI_CONNECTATHON_43_MVP_BUILD_PLAN.md
docs/connectathon/README.md
experiments/disco_inferno/fhir_corruptions.py
hl7_demo/labs.py
pages/9_PIQI_Connectathon_43.py
tests/test_connectathon_control_quality.py
tests/test_connectathon_fhir_corruptions.py
tests/test_connectathon_piqitt_integration.py
tests/test_connectathon_scenarios.py
```

Structured Sparsity was not migrated.

The existing newer Disco implementation in `medilacra_connect` was preserved. Only the missing FHIR corruption primitive required by PIQI was added to its namespace.

---

# 5. Shared Baseline Modification: `hl7_demo/labs.py`

The PIQI migration deliberately allowed one shared MediLacra baseline modification:

```text
hl7_demo/labs.py
```

This was not UI plumbing or experiment-specific convenience. It was necessary to keep the **control** clinically and terminologically coherent enough to function as an experimental baseline.

The shared change included:

- UCUM-safe lab units,
- correction of the WBC unit representation,
- internally plausible lipid relationships so a generated control does not begin with an obvious contradiction such as LDL exceeding total cholesterol.

Decision:

> A validation experiment must not intentionally manufacture mutants from a baseline already known to violate the local control invariants being tested.

The control quality gate therefore refuses to build mutants until the baseline passes.

---

# 6. PIQITT Was Kept External

PIQITT was deliberately not copied into `medilacra_connect`.

The workbench loads:

```text
piqitt/scripts/fhir_convert_backend.py
```

from a local PIQITT checkout.

The accepted default layout is:

```text
workspace/
├── medilacra_connect/
└── piqitt/
```

PIQITT may also be supplied through:

```text
PIQITT_REPO
```

or the workbench path input.

The permanent integration tests use **PIQITT `main`**, not PIQITT's old Connectathon branch. This proves that the consolidated PIQI module depends on the converter itself rather than hidden branch-only scaffolding.

---

# 7. Initial PIQI Workbench Contract

The migrated workbench implemented the local side of the Connectathon experiment:

```text
source HL7
    ↓
PIQITT conversion
    ↓
FHIR control normalization
    ↓
control quality gate
    ↓
selected deterministic mutation
    ↓
baseline + mutant + manifest + preflight
    ↓
run manifest + ZIP
```

The v1 scenario set became:

| Case | Operator | Declared path | Local expected target |
|---|---|---|---|
| `case_000_control` | control | none | no introduced failure |
| `case_001_availability` | remove element | `Patient.identifier` | `ATTR_ISPOPULATED` / `AV_UNPOP` |
| `case_002_code_system` | remove coding component | `Observation.code.coding[0].system` | `CONCEPT_HASCODESYSTEM` / `AV_UNPOP` |
| `case_003_invalid_member` | replace value | `Observation.code.coding[0].code` | `CONCEPT_ISVALIDMEMBER` / `CONF_INCOMP` |

The three non-control SAM/dimension expectations remain provisional until external execution is performed.

---

# 8. Local Failure: `observation.coded_values`

The first substantive local user test reached the scenario-pack boundary and stopped correctly at the control quality gate:

```text
ValueError: Baseline failed the PIQI control quality gate; refusing to build mutants.
Failed checks: observation.coded_values
```

Everything before that point had worked:

- source discovery,
- PIQITT checkout discovery,
- message parsing,
- message selection,
- HL7 -> FHIR conversion,
- FHIR baseline materialization,
- Streamlit state and display.

The failure therefore isolated a semantic control defect rather than an integration failure.

## Root cause

MediLacra legitimately emits coded OBX values with HL7 value types including:

```text
CE
CWE
CNE
```

PIQITT `main` materialized `CE` into FHIR `valueCodeableConcept`, but `CWE`/`CNE` values could fall through to `valueString`.

That left strings such as:

```text
446151000124109^Male^SCT
```

inside FHIR `Observation.valueString`.

The control quality gate correctly rejected this because the source clearly expressed coded data and the FHIR control had not preserved that semantic structure.

## Fix

The PIQITT bridge now uses the original HL7 OBX-2 datatype as provenance.

Only values originating from:

```text
CE
CWE
CNE
```

are eligible for compatibility repair.

Known coding systems are normalized to their known URIs. Unknown source-system tokens are preserved as source identities such as:

```text
urn:hl7v2:99MEDILACRA
```

rather than inventing a canonical terminology mapping.

Arbitrary narrative strings containing carets are not guessed to be coded data.

A regression case using `CWE` plus a local `99MEDILACRA` coding system was added to the real PIQITT integration test.

---

# 9. Accepted Local Evidence Run

After the coded-value compatibility fix, the user successfully generated and supplied:

```text
PIQI_CONNECTATHON_43_20260911T085037-0400.zip
```

The detailed results are preserved separately at:

```text
docs/PIQI_V1_BASELINE_RESULTS_2026-09-11.md
```

The accepted historical evidence demonstrated:

```text
baseline control quality gate: PASS
FHIR resources: 9
Patient: 1
Encounter: 1
Observation: 7
CE-family compatibility repairs: 3
unresolved coded values: 0
case preflight: PASS for all 4 cases
control changed paths: 0
non-control changed paths: exactly 1 each
```

All four cases shared the same historical baseline SHA-256:

```text
ecb65ea668d7e52b38846424357c12ea7a9801cabfdba13d61cdc233d1864a32
```

The control's mutant hash was identical to the baseline hash.

The three non-control cases changed exactly:

```text
entry[0].resource.identifier
entry[5].resource.code.coding[0].system
entry[5].resource.code.coding[0].code
```

The historical `case_003_invalid_member` target was LOINC `39156-5`, so the accepted artifact was already within the terminology boundary later made explicit during final v1 hardening.

---

# 10. Final v1.0 Review and Hardening

Before labeling the repository state v1.0, the open PIQI integration PR received four automated review findings that were sufficiently substantive to fix before closeout.

## V1-HARDEN-001 — Preserve source timezone instead of inventing UTC

### Finding

The initial control normalizer appended `Z` to clock-bearing FHIR dateTimes that lacked an offset.

That made them syntactically zoned but could change the represented clinical instant by asserting UTC for a source local time.

### Resolution

The v1 normalizer now uses this precedence:

1. explicit offset recovered from source HL7 MSH-7,
2. explicitly configured IANA source timezone,
3. conversion-process local timezone.

Already-zoned FHIR values are preserved.

The PIQI page now exposes an optional source-timezone field and supports:

```text
MEDILACRA_SOURCE_TZ
```

The cleanup report records the timezone basis used.

### Evidence implication

The accepted ZIP predates this hardening. Its historical baseline SHA is therefore preserved as evidence of that exact run but is not claimed to be the SHA of a freshly regenerated post-hardening v1 control.

---

## V1-HARDEN-002 — Restrict invalid-member mutation to a bound terminology

### Finding

The initial invalid-member mutation could select any Observation containing a code path, including local SDOH systems such as `urn:hl7v2:L`.

Changing an arbitrary local code to `ZZZ-NOT-A-VALID-CODE` would not necessarily represent a meaningful terminology-membership failure.

### Resolution

`case_003_invalid_member` is now restricted to:

```text
http://loinc.org
```

candidate observations.

The mutation engine supports a declared `candidate_coding_systems` filter and records that constraint in the mutation manifest.

The page's scenario-applicability logic uses the same restriction.

---

## V1-HARDEN-003 — Invalidate stale PIQITT converter cache

### Finding

The PIQITT loader originally cached a converter module only by filesystem path.

If the PIQITT checkout changed while Streamlit remained running, the workbench could continue executing old converter code while provenance reported a newer repository revision.

### Resolution

The cache key now includes:

```text
converter path + converter file SHA-256
```

Changed converter content therefore forces a module reload.

The converter SHA-256 is also included in source metadata.

A regression test writes two different converter files at the same path and verifies that the second load returns a new module.

---

## V1-HARDEN-004 — Separate uploaded names from local file provenance

### Finding

The first provenance implementation treated `source_name` as a potential local path.

A browser-uploaded file named `example.hl7` could therefore accidentally inherit provenance from an unrelated local `example.hl7` in the process working directory.

### Resolution

`source_name` is now descriptive metadata only.

Local file and Disco-run provenance is collected only when the caller supplies an explicit:

```text
source_path
```

The Streamlit page distinguishes uploaded files from selected local files at the source-read boundary.

A regression test creates a same-named local file and proves that an upload does not inherit its path metadata.

---

# 11. v1.0 Validation

The permanent workflow is:

```text
.github/workflows/connectathon-smoke.yml
```

The final hardening regression run used:

```text
Python 3.10
PIQITT main
```

Workflow run:

```text
34618468392
```

Result:

```text
Compile Connectathon modules: PASS
Run Connectathon tests:       PASS
Overall workflow:             SUCCESS
```

The v1 regression surface covers:

- zero-delta control,
- one-path mutation enforcement,
- LOINC-only invalid-member targeting,
- baseline quality gating,
- UCUM normalization,
- coded-value materialization,
- CE/CWE/CNE compatibility against real PIQITT `main`,
- source offset preservation,
- PIQITT converter cache invalidation,
- upload/local-path provenance separation,
- end-to-end PIQITT conversion -> clean control -> scenario pack.

---

# 12. v1.0 Documentation Surface

The v1 closeout adds or updates the following primary documentation:

```text
README.md
```

Reframed from a baseline MediLacra-only README to the consolidated v1 platform identity, including definitions, architecture, output locations, scenarios, non-claims, and simple local pull/run commands.

```text
docs/MEDILACRA_CONNECT_V1_0_PROCESS_2026-09-11.md
```

This document: build/migration history, prompt provenance, review hardening, validation, and decision log.

```text
docs/PIQI_V1_BASELINE_RESULTS_2026-09-11.md
```

Separate accepted local baseline/evidence results from the user-supplied ZIP.

Existing retained documentation includes:

```text
docs/DISCO_INFERNO_MIGRATION_2026-09-10.md
docs/connectathon/README.md
docs/connectathon/PIQI_CONNECTATHON_43_MVP_BUILD_PLAN.md
docs/connectathon/IMPLEMENTATION_STATUS_2026-09-02.md
```

The older Connectathon docs are historical design/build records. The root README and v1 closeout docs describe the accepted consolidated platform boundary.

---

# 13. v1.0 Tool and Code Boundaries

## Baseline MediLacra

Primary UI:

```text
medi_lacra_app.py
```

Ordinary generated HL7:

```text
output/*.hl7
```

Baseline packages remain under:

```text
hl7_demo/
```

## Disco Inferno

UI:

```text
pages/8_Disco_Inferno.py
```

Package:

```text
experiments/disco_inferno/
```

## PIQI Connectathon 43

UI:

```text
pages/9_PIQI_Connectathon_43.py
```

Package:

```text
connectathon/
```

Local evidence output:

```text
connectathon/results/<run-id>/
```

## External PIQITT dependency

Expected converter:

```text
../piqitt/scripts/fhir_convert_backend.py
```

PIQITT remains a separate repository.

---

# 14. Explicit v1.0 Non-Goals

The v1.0 label means the local consolidated experiment platform reached an accepted stable checkpoint. It does **not** mean every planned MediLacra experiment has been migrated or every Connectathon step is complete.

Not part of the v1 accepted runtime boundary:

- Reality Interface migration,
- Structured Sparsity migration,
- external PIQI endpoint submission,
- normalized comparison of multiple external PIQI endpoint responses,
- full US Core conformance,
- production FHIR-server behavior,
- production deployment packaging,
- clinical validation of synthetic values.

These can be layered on after the v1 local control/mutation/provenance machinery is preserved.

---

# 15. Decision Log

| ID | Date | Decision | Rationale | Consequence |
|---|---|---|---|---|
| MC-V1-001 | 2026-09-10 | Materialize a clean MediLacra baseline in a new `medilacra_connect` repository before integrating experiments. | The Connectathon platform needed one stable shared base rather than a branch maze. | Later tools can be compared against one known baseline. |
| MC-V1-002 | 2026-09-10 | Exclude upload-temp debris from the baseline copy. | Temporary transfer artifacts are not repository functionality. | Target baseline remains clean. |
| MC-V1-003 | 2026-09-10 | Fix missing direct runtime dependencies in the target baseline. | Local launch should work from declared requirements. | Baseline bootstrap became reproducible. |
| MC-V1-004 | 2026-09-10 | Migrate Disco selectively rather than merging its branch. | The source branch carried Structured Sparsity history. | Disco remains a distinct tool without prematurely importing another experiment. |
| MC-V1-005 | 2026-09-10 | Localize Disco's inherited `SyntheticCase` dependency. | The type was a small generic container, not a reason to import Structured Sparsity. | Disco became independently runnable. |
| MC-V1-006 | 2026-09-10 | Make SDOH-off a worker execution boundary, not merely an output toggle. | Local testing showed API traffic could continue even when output omitted enrichment. | SDOH-off Disco workers block covered Requests traffic. |
| MC-V1-007 | 2026-09-11 | Prioritize PIQI-43 over preserving existing experiment architecture. | User explicitly identified PIQI as the most important Connectathon module. | Disco/PIQITT boundaries may adapt to serve PIQI rather than the reverse. |
| MC-V1-008 | 2026-09-11 | Do not merge `connectathon/piqi-43` wholesale. | The source branch inherited Disco and Structured Sparsity history. | Only the useful Connectathon surface was migrated. |
| MC-V1-009 | 2026-09-11 | Keep PIQITT external and load its existing converter. | Duplicating conversion code would create two authorities and weaken provenance. | PIQITT remains the source of truth for HL7 -> FHIR. |
| MC-V1-010 | 2026-09-11 | Validate against PIQITT `main`, not its old Connectathon branch. | The consolidated module should depend on the stable converter surface, not branch scaffolding. | CI proves the local integration against PIQITT main. |
| MC-V1-011 | 2026-09-11 | Permit the shared `hl7_demo/labs.py` change. | A dirty or clinically contradictory baseline poisons the mutation experiment. | UCUM and lipid-control coherence became part of baseline generation. |
| MC-V1-012 | 2026-09-11 | Refuse to generate mutants when the baseline quality gate fails. | A controlled mutation only means something relative to a sufficiently clean control. | The first local coded-value defect stopped execution rather than being hidden. |
| MC-V1-013 | 2026-09-11 | Repair PIQITT CE/CWE/CNE fall-through using HL7 datatype provenance. | Coded source values must not survive as packed FHIR strings, but arbitrary caret text must not be guessed into terminology. | The coded-value gate passed without weakening the invariant. |
| MC-V1-014 | 2026-09-11 | Preserve unknown source coding-system tokens rather than invent canonical terminology mappings. | Greater specificity is not greater correctness when the source identity is unknown. | Local source systems remain explicit as `urn:hl7v2:*`. |
| MC-V1-015 | 2026-09-11 | Preserve one baseline hash across all cases in a run. | Regenerating reality between cases would confound mutation effects with source variation. | Each case is a controlled intervention on the same representation. |
| MC-V1-016 | 2026-09-11 | Require exactly one changed JSON path for each non-control v1 mutant. | The initial PIQI cases are intended to isolate one declared information defect. | The manifest acts as a machine-verifiable corruption receipt. |
| MC-V1-017 | 2026-09-11 | Preserve source timezone semantics instead of appending `Z`. | Fabricated UTC changes represented instants and therefore corrupts the control. | Explicit MSH-7 offsets, configured IANA timezone, or process-local timezone are used. |
| MC-V1-018 | 2026-09-11 | Restrict invalid-member mutations to LOINC-coded observations. | Terminology membership is only meaningful against an identifiable code system/value-set context. | Local arbitrary code systems are no longer eligible for `case_003`. |
| MC-V1-019 | 2026-09-11 | Include converter file identity in the PIQITT cache key and provenance. | A long-running UI must not execute stale converter code while claiming a newer checkout. | Changed converter content reloads and the converter SHA is recorded. |
| MC-V1-020 | 2026-09-11 | Treat upload filename and local source path as different provenance fields. | Browser names are not proof of filesystem identity. | Uploaded files cannot accidentally inherit unrelated local/Disco provenance. |
| MC-V1-021 | 2026-09-11 | Call the accepted local consolidated checkpoint `medilacra_connect v1.0`. | Baseline generation, controlled corruption, PIQITT-backed FHIR control construction, local PIQI cases, provenance, and evidence packaging now form a coherent usable platform. | The README and closeout documentation describe this as the first stable platform boundary. |
| MC-V1-022 | 2026-09-11 | Keep external PIQI execution outside v1.0 claims. | No external endpoint result has yet been run/preserved in the accepted evidence. | v1.0 is honest about its boundary; endpoint execution becomes the next major slice. |

---

# 16. v1.0 Acceptance Criteria

The repository is ready for the v1.0 checkpoint when the following are true:

```text
[PASS] baseline MediLacra launches from the consolidated repository
[PASS] ordinary MediLacra output remains available
[PASS] Disco Inferno is available as a distinct page/tool
[PASS] Disco zero-delta and corruption behavior has regression coverage
[PASS] SDOH-off worker boundary is enforced for covered Requests traffic
[PASS] PIQI-43 is available as a distinct workbench
[PASS] PIQITT main can materialize the local FHIR control
[PASS] CE/CWE/CNE coded-value compatibility is tested
[PASS] control quality gate prevents dirty baselines from becoming experiments
[PASS] accepted local evidence pack has a zero-delta control
[PASS] accepted local evidence pack has one changed path per non-control case
[PASS] all accepted local cases pass structural preflight
[PASS] baseline and mutation provenance/hashes are preserved
[PASS] timezone semantics are not fabricated as UTC
[PASS] invalid-member mutation is terminology-bound
[PASS] PIQITT cache/provenance cannot silently diverge after converter changes
[PASS] uploads cannot inherit unrelated local-file provenance
[PASS] permanent Connectathon CI passes against PIQITT main
[PASS] root README describes the consolidated platform and local launch path
[PASS] process and baseline evidence are preserved separately under docs/
```

External PIQI endpoint acceptance is intentionally not included in this list.

---

# Closeout

The v1.0 platform can now be summarized as:

```text
synthetic healthcare reality
        ↓
MediLacra representations
        ↓
controlled damage with explicit receipts
        ↓
PIQITT transformation to FHIR
        ↓
clean invariant control
        ↓
PIQI-shaped controlled failure cases
        ↓
local preflight + provenance + evidence
```

The primary unresolved experimental boundary is no longer local artifact construction. It is external PIQI execution: submit the preserved control and mutants, retain raw responses before normalization, and compare endpoint behavior against both one another and the known ground truth encoded in the mutation manifests.
