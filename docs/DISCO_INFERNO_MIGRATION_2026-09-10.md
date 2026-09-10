# Disco Inferno Migration Record

**Repository:** `natosit-dev/medilacra_connect`  
**Migration date:** 2026-09-10  
**Document version:** 1.0  
**Status:** COMPLETE / ACCEPTED  
**Source repository:** `natosit-dev/medilacra`  
**Source branch:** `experiment/disco-inferno`  
**Target repository:** `natosit-dev/medilacra_connect`  
**Target branch:** `main`  
**Purpose:** Preserve Disco Inferno as a distinct MediLacra tool for the HL7 Connectathon platform while protecting shared baseline behavior.

---

# Prompt History

The relevant user prompts are preserved here at the top of the migration record so the implementation can be evaluated against the actual requested grain rather than reconstructed from the resulting code.

## Prompt 1 — Platform consolidation context

> I feel like this is spread across a few chats so let's create a chat here to determine how to fold the valuable Medilacra branches into a single platform for the connectathon. I want to copy the medilacra baseline to this new repo:
> https://github.com/natosit-dev/medilacra_connect
> then merge the important branches into it:
> reality interface
> disco inferno
> structured sparsity
> connectathon/piqi-43
>
> I believe these are all good enough to be separate MediLacra tools. Let's start with copying the baseline. Once I confirm I can pull and run it locally, we'll do the first merge. So, copy Medilacra to medilacra_connect and walk me through pulling it to run locally

## Prompt 2 — Disco Inferno migration

> Ok, looking good. Let's merge the first branch into the new medilacra_connect repo. Start with Disco Inferno. Add as new page in pages, be careful about modifications to shared code

## Prompt 3 — Local validation / defect report

> Looked good except for the API calls are still running. Enabled and disabled it and it ran correctly

## Prompt 4 — Acceptance

> Looks good. I think we can consider this done.

## Prompt 5 — Documentation closeout

> Record the results, all the trimmings, in a migration doc in /docs in medilacra_connect along with what was added and a decision log. Prompt history at the top

---

# Executive Summary

Disco Inferno was successfully migrated from `natosit-dev/medilacra` into `natosit-dev/medilacra_connect` as an independent MediLacra Streamlit tool.

The tool migration is deliberately additive. Relative to the pre-Disco `medilacra_connect` baseline commit `8a6ffe261c1c1e14e421f824dea0224debafbc1b`, the accepted Disco tool state added 17 files and modified or deleted **zero pre-existing baseline files**. This migration record itself is the 18th new repository path relative to that baseline and is documentation, not part of the executable Disco tool surface.

The migration did **not** perform a wholesale Git merge of `experiment/disco-inferno`. Inspection showed that the source branch carried earlier Structured Sparsity history and files. Copying the branch directly would therefore have violated the requested tool boundary and prematurely coupled two experiments.

Instead, only the Disco Inferno page, package, recorded result, and regression tests were brought over. One inherited cross-experiment dependency, `SyntheticCase`, was localized into the Disco package so Disco could stand alone without importing Structured Sparsity.

A local validation pass found one post-migration issue: when SDOH was disabled, the generated output was correct but outbound HTTP attempts could still escape through Requests aliases imported before the Disco offline guard was installed. That was corrected entirely inside Disco's isolated worker boundary. Shared MediLacra code remained unchanged.

Final user acceptance was given after local execution with the SDOH control exercised in both enabled and disabled states.

---

# Migration Objective

The migration had four primary requirements:

1. Add Disco Inferno to `medilacra_connect` as its own Streamlit page.
2. Preserve Disco Inferno as a distinct tool rather than blending it into the MediLacra core.
3. Avoid modifications to shared MediLacra code wherever possible.
4. Keep unrelated experiments, especially Structured Sparsity, out of this migration.

These requirements were met.

---

# Source Analysis

## Source branch state

The original source was:

```text
natosit-dev/medilacra
branch: experiment/disco-inferno
```

Comparison against the source repository's `main` showed the branch was not a clean single-feature branch. It was 22 commits ahead and 1 commit behind the then-current source `main`, and its delta included both:

- Disco Inferno files
- Structured Sparsity files inherited from earlier branch history

The Disco-specific surface itself was cleanly namespaced under:

```text
experiments/disco_inferno/
pages/8_Disco_Inferno.py
tests/test_disco_inferno*.py
```

No existing MediLacra baseline files had been modified by the Disco implementation in the source branch.

## Cross-experiment dependency discovered

Disco Inferno imported a small `SyntheticCase` container from Structured Sparsity. Pulling that dependency as-is would have made Disco depend on an experiment that had not yet been migrated.

The required type was sufficiently small and generic to localize without importing the Structured Sparsity package. A Disco-local implementation was therefore added at:

```text
experiments/disco_inferno/models.py
```

This is the only migration-specific implementation shim added to separate Disco Inferno from inherited source-branch history.

---

# Resulting Tool Boundary

Disco Inferno remains a self-contained controlled-entropy experiment within the larger MediLacra platform.

Its conceptual model remains unchanged:

```text
MediLacra reality
      |
      v
   Beatrice
      |
      +--------------------+
      |                    |
      v                    v
  untouched            Disco Inferno
                           |
                         Minos
                           |
              +------------+------------+
              |            |            |
            Charon        Null        Cerberus
              |            |            |
        drop identifier  null field  duplicate record
```

The existing experiment definition is preserved:

- **Beatrice** is the faithful tabular representation of generated MediLacra reality.
- **Control** proves the comparison harness reports zero damage.
- **Charon** removes an explicit relationship identifier.
- **Null** removes selected generated facts while preserving records.
- **Cerberus** duplicates records, increasing represented cardinality without adding reality entities.

The tool continues to ask the Disco Inferno question: what knowledge survives information degradation when reality and representation structure are held constant?

---

# Files Added

At tool acceptance, comparison from pre-Disco baseline commit `8a6ffe261c1c1e14e421f824dea0224debafbc1b` to the accepted executable Disco state showed 17 added files and no modifications or deletions to pre-existing baseline files. This document is intentionally counted separately as migration documentation.

## Streamlit page

```text
pages/8_Disco_Inferno.py
```

This exposes Disco Inferno as a first-class page in the existing MediLacra Streamlit application.

## Disco Inferno package

```text
experiments/disco_inferno/README.md
experiments/disco_inferno/__init__.py
experiments/disco_inferno/compare.py
experiments/disco_inferno/corruptions.py
experiments/disco_inferno/exports.py
experiments/disco_inferno/materialize.py
experiments/disco_inferno/models.py
experiments/disco_inferno/offline_sdoh.py
experiments/disco_inferno/process_control.py
experiments/disco_inferno/reporting.py
experiments/disco_inferno/run_experiment.py
experiments/disco_inferno/worker.py
```

## Preserved evidence record

```text
experiments/disco_inferno/results/DISCO_INFERNO_MVP_RESULTS_20260831T082301-0400.md
```

The original canonical MVP evidence record was preserved with the tool.

## Regression tests

```text
tests/test_disco_inferno.py
tests/test_disco_inferno_offline_sdoh.py
tests/test_disco_inferno_process_control.py
```

## Migration documentation

```text
docs/DISCO_INFERNO_MIGRATION_2026-09-10.md
```

This record is the documentation closeout artifact and is not counted among the 17 executable/test/evidence files in the tool migration itself.

---

# Shared-Code Impact

## Final result

**No pre-existing MediLacra baseline file was changed.**

The page imports existing canonical MediLacra entities such as `Patient`, `Encounter`, `Observation`, and `Transaction` from `hl7_demo.models`, and the experiment reuses existing generators and message builders rather than cloning or rewriting them.

The SDOH fix was also deliberately kept within:

```text
experiments/disco_inferno/offline_sdoh.py
```

It did not alter:

```text
hl7_demo/messages.py
hl7_demo/sdoh.py
hl7_demo/generators.py
hl7_demo/models.py
```

This preserves the migration rule that a tool may consume shared MediLacra behavior without silently changing the behavior of other pages or tools.

---

# SDOH / Network Boundary Defect and Resolution

## Observed behavior

After the initial migration, local testing showed that the SDOH toggle controlled generated output correctly, but API/network activity could still be observed while the feature was disabled.

Inspection of the uploaded run artifacts confirmed that the disabled runs themselves were recording:

```text
include_sdoh: false
```

and were not materializing AirNow, ACS poverty, PLACES, or unemployment OBXs.

The problem was therefore not stale Streamlit state and not incorrect output semantics. The problem was the strength of the execution boundary.

## Root cause

The initial offline implementation replaced SDOH lookup functions and the `requests` object inside `hl7_demo.sdoh`. That prevented the known SDOH paths from returning external enrichment.

It did not, however, guarantee that another module—or a function alias imported from Requests before the guard was installed—could not still execute an outbound HTTP request.

## Resolution

When Disco Inferno runs with SDOH disabled, its detached worker now blocks Requests at the worker-process level by replacing the Requests session request path. Because each Disco run uses an isolated worker process, this stronger boundary applies only to that run and does not mutate Requests behavior in the Streamlit host or other MediLacra tools.

Regression coverage was added for:

- normal `requests.get`
- a `get` alias imported before offline mode is installed
- existing SDOH public lookup replacements

This preserves the intended invariant:

> SDOH OFF means external enrichment is not merely omitted from the output; the Disco worker cannot make an outbound Requests call through the covered Requests execution path.

---

# Validation

Validation occurred at three levels.

## 1. Repository boundary validation

The tool-state comparison against the pre-Disco baseline contained only the 17 Disco executable/test/evidence files listed above. The later addition of this documentation file does not change that implementation boundary.

Result:

```text
pre-existing files modified: 0
pre-existing files deleted: 0
Structured Sparsity files imported: 0
```

## 2. Automated regression validation

The following suites were run against the `medilacra_connect` dependency set:

```text
tests/test_disco_inferno.py
tests/test_disco_inferno_offline_sdoh.py
tests/test_disco_inferno_process_control.py
```

All three suites passed after the offline-network fix.

The validation run used Python 3.10 and installed the repository's normal `requirements.txt` before executing the Disco tests.

The temporary GitHub Actions workflow used for migration validation was removed before the fix was merged, so CI scaffolding created only for the migration did not become permanent repository infrastructure.

## 3. Local user validation

The migrated page was pulled and run from the normal local MediLacra environment. The user reported that the page looked correct and manually exercised SDOH in enabled and disabled states.

The migration was explicitly accepted as complete after the network-boundary correction.

---

# Local Evidence Runs

Two uploaded local Disco Inferno bundles were inspected during validation. Both manifests recorded `include_sdoh: false`.

## Run `20260910T130920-0400`

Artifact:

```text
DISCO_INFERNO_20260910T130920-0400.zip
```

Settings:

| Setting | Value |
|---|---:|
| Patients | 10 |
| Encounters / patient | 2 |
| Observations / encounter | 2 |
| Transactions / encounter | 2 |
| Labs | enabled |
| SDOH | disabled |
| Null fraction | 10% |
| Cerberus fraction | 10% |

Observed corruption results:

| Arm | Result |
|---|---:|
| Control | 0 affected; zero comparison delta |
| Charon | 40 / 40 observations affected |
| Null | 4 / 40 observations affected |
| Cerberus | 4 duplicate transactions added; 40 → 44 |

HL7 output counts:

| Message | Count |
|---|---:|
| ADT^A01 | 20 |
| ORU^R01 | 20 |
| DFT^P03 | 20 |
| ORM^O01 labs | 20 |
| ORU^R01 labs | 20 |

## Run `20260910T131236-0400`

Artifact:

```text
DISCO_INFERNO_20260910T131236-0400.zip
```

Settings:

| Setting | Value |
|---|---:|
| Patients | 100 |
| Encounters / patient | 2 |
| Observations / encounter | 2 |
| Transactions / encounter | 2 |
| Labs | disabled |
| SDOH | disabled |
| Null fraction | 20% |
| Cerberus fraction | 10% |

Observed corruption results:

| Arm | Result |
|---|---:|
| Control | 0 affected; zero comparison delta |
| Charon | 400 / 400 observations affected |
| Null | 80 / 400 observations affected |
| Cerberus | 40 duplicate transactions added; 400 → 440 |

HL7 output counts:

| Message | Count |
|---|---:|
| ADT^A01 | 200 |
| ORU^R01 | 200 |
| DFT^P03 | 200 |

These runs provide local evidence that the migrated tool retained deterministic corruption behavior across both a small smoke cohort and a normal 100-patient cohort, including exact selected fractions for the tested Null and Cerberus settings and a zero-delta Control.

---

# Git / Migration History

## Initial isolated integration

Integration branch:

```text
integrate/disco-inferno
```

Pull request:

```text
PR #1 — Integrate Disco Inferno as isolated MediLacra tool
```

Squash merge commit:

```text
853376f9a8bfa36d202f29eaadf5e3427cd70253
```

This commit added the isolated Disco tool surface while preserving the MediLacra baseline unchanged.

## Offline-network correction

Fix branch:

```text
fix/disco-offline-network
```

Pull request:

```text
PR #2 — Block outbound HTTP when Disco SDOH is disabled
```

Squash merge commit:

```text
ec3d4caf5dc0fcce81f7f87dc7c43952634f465d
```

This commit strengthened the Disco worker's offline boundary and added regression coverage. It changed no shared MediLacra code.

## Documentation closeout

Migration record:

```text
docs/DISCO_INFERNO_MIGRATION_2026-09-10.md
```

This document was added after user acceptance to preserve prompt provenance, migration mechanics, validation evidence, implementation boundaries, and the decision log.

---

# Decision Log

| ID | Date | Decision | Rationale | Consequence |
|---|---|---|---|---|
| DI-MIG-001 | 2026-09-10 | Treat Disco Inferno as a separate MediLacra tool/page. | The Connectathon platform is intended to contain several independently legible tools rather than collapse experiments into one interface or code path. | Disco is exposed as `pages/8_Disco_Inferno.py` with its own package. |
| DI-MIG-002 | 2026-09-10 | Do not wholesale-merge `experiment/disco-inferno`. | The source branch carried Structured Sparsity history and files in addition to Disco Inferno. | Only the Disco-specific surface was migrated. |
| DI-MIG-003 | 2026-09-10 | Preserve shared MediLacra files unchanged. | The user explicitly requested care around modifications to shared code, and the source implementation did not require such modifications. | Baseline-to-tool-state diff contains no changed/deleted pre-existing files. |
| DI-MIG-004 | 2026-09-10 | Localize `SyntheticCase` inside Disco Inferno. | Disco's inherited import from Structured Sparsity created an unnecessary cross-experiment dependency. | Added `experiments/disco_inferno/models.py`; Structured Sparsity remains independently migratable later. |
| DI-MIG-005 | 2026-09-10 | Reuse MediLacra canonical models/generators/message builders rather than copying them. | Disco is an experiment over MediLacra reality; duplicating core generation would create drift and obscure provenance. | Disco consumes shared core behavior but does not own or fork it. |
| DI-MIG-006 | 2026-09-10 | Keep SDOH opt-in and offline by default. | External enrichment is not part of the core entropy experiment and should not make deterministic local generation depend on API latency/availability. | Normal Disco runs remain locally reproducible without external services. |
| DI-MIG-007 | 2026-09-10 | Fix the discovered API leak at the isolated worker boundary, not in shared `hl7_demo`. | Output semantics were already correct; the defect was execution isolation. Changing shared SDOH code would increase migration blast radius. | Requests are blocked within the Disco worker when SDOH is off; other MediLacra tools are unaffected. |
| DI-MIG-008 | 2026-09-10 | Add a regression test for pre-imported Requests aliases. | The first offline test proved only the known module path and therefore missed the observed escape path. | The defect that escaped the original test is now represented explicitly in the suite. |
| DI-MIG-009 | 2026-09-10 | Use temporary CI only for migration validation and remove it before merge. | A one-time migration test harness should not silently become permanent project infrastructure. | The repository keeps the regression tests but not the temporary workflow. |
| DI-MIG-010 | 2026-09-10 | Squash migration and fix PRs into `main`. | The working branches contained bootstrap/testing mechanics that were useful during integration but not useful as permanent main history. | `main` receives one clean feature commit and one clean corrective commit. |
| DI-MIG-011 | 2026-09-10 | Consider Disco Inferno migration complete after automated regression and local user acceptance. | The tool was present, isolated, generated expected artifacts/corruptions, preserved Control=0, and the reported network issue was corrected. | Disco Inferno becomes the first completed tool migration into `medilacra_connect`. |

---

# Known Boundaries / Non-Goals

This migration intentionally did **not**:

- migrate Structured Sparsity
- migrate Reality Interface
- migrate `connectathon/piqi-43`
- redesign MediLacra core models
- refactor shared SDOH architecture
- introduce a common plugin/tool registry
- renumber or reorganize existing Streamlit pages
- convert temporary migration CI into permanent CI policy

Those decisions keep this migration narrow and make the next tool migration independently reviewable.

---

# Operational Notes

Local launch remains the standard MediLacra launch path:

```bash
cd /home/spooky/code/medilacra_connect
conda activate dev310
python -m streamlit run medi_lacra_app.py
```

Disco Inferno is available from the Streamlit page list.

Relevant regression command:

```bash
python -m pytest -q \
  tests/test_disco_inferno.py \
  tests/test_disco_inferno_offline_sdoh.py \
  tests/test_disco_inferno_process_control.py
```

The tool also retains detached worker process controls, active job/PID state, worker log access, and stop controls. Stale worker locks are cleared when their recorded PID is no longer alive.

---

# Acceptance Criteria — Final State

| Criterion | Status |
|---|---|
| Disco Inferno appears as its own Streamlit page | PASS |
| Disco implementation is namespaced independently | PASS |
| Existing MediLacra baseline files remain unchanged | PASS |
| Structured Sparsity is not migrated accidentally | PASS |
| Inherited `SyntheticCase` dependency is decoupled | PASS |
| Control produces zero delta | PASS |
| Charon / Null / Cerberus execute and materialize expected changes | PASS |
| HL7 artifacts generate | PASS |
| Lab-message path exercised in local evidence run | PASS |
| SDOH disabled state is recorded in artifacts | PASS |
| SDOH-disabled worker blocks covered outbound Requests paths | PASS |
| Automated Disco regression suites pass | PASS |
| Local user validation completed | PASS |
| User accepted migration as complete | PASS |

---

# Final Status

**DISCO INFERNO MIGRATION: COMPLETE**

Disco Inferno is now a distinct, locally runnable MediLacra tool inside `medilacra_connect`, with its original experimental semantics, UI, process controls, evidence record, artifact generation, and regression coverage preserved.

The migration established a useful pattern for subsequent Connectathon tool consolidation:

> Copy the smallest coherent tool surface, reuse the shared MediLacra core, identify inherited branch history before merging, and treat changes to shared code as an explicit architectural decision rather than an incidental side effect of migration.
