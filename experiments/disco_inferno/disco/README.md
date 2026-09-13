# DiScO

**Deterministic Inspection of Semantic Coupling in Outputs**

DiScO is a Disco Inferno submodel for cheap, deterministic inventories of observable text features associated with semantic reconstruction cost and experimental authorship/style signals.

## Working boundary

DiScO does **not** determine truth, intelligence, private understanding, or AI authorship. It inventories observable features and optionally compresses them into bounded signal scores.

The canonical artifact is the inventory. Scores are derived and replaceable.

```text
text / document
  -> deterministic observations
  -> feature inventory
  -> bounded feature strengths
  -> bounded semantic / AI signals
```

## Input modes

`pages/8_DiScO.py` accepts either pasted text or an uploaded `.docx` / `.pdf` file.

For uploaded documents DiScO keeps two layers separate:

1. **Text layer** — plain text is extracted and passed to the existing DiScO text engine.
2. **Artifact layer** — DiScO imports the existing `doc_history` package and stores its complete provenance/metadata dataset with the judgement.

The artifact layer is observational only for now. Document metadata does **not** currently alter semantic or AI scoring.

DiScO intentionally reuses `natosit-dev/doc_history` rather than copying its extraction logic. It first tries a normal `import doc_history`, then looks for a sibling/local checkout. `DOC_HISTORY_PATH` can point to another checkout.

Typical local layout:

```text
~/medilacra_connect_DiScO
~/doc_history
```

The reused `doc_history` dataset includes, when present:

- DOCX core/application/custom properties
- creator and last modifier
- created/modified/printed timestamps
- Word `TotalTime`, application/version, template and document statistics
- Track Changes state and surviving revision markup
- RSIDs, comments/people parts and document IDs
- custom XML / document-management provenance
- PDF Info/XMP metadata, producer/creator software, document/instance IDs
- exact uploaded-file SHA-256

DiScO also stores `doc_history` timeline events and provenance clues as deterministic derived views of the same dataset.

## Active default feature set

The checked-in text defaults currently inventory:

1. Metaphor vocabulary
2. Mechanism placeholders
3. Anthropomorphic mechanism phrases
4. Nominalizations
5. Unintroduced acronyms
6. Ready-made phrases
7. Verbal false limbs
8. Worn / dead metaphors
9. Prestige / intimidating diction
10. Semantically sparse evaluative words
11. Concealment / euphemistic phrases
12. Em dash usage
13. Markdown scaffolding

The later rule families are informed by the current Mao / Orwell provenance work, but they remain candidate signals rather than validated measurements of slop. Em dash usage and Markdown scaffolding are currently treated as AI-oriented style/provenance signals, not semantic-slop signals.

The checked-in rule definitions, priors, phrase dictionaries, and regex patterns live in:

```text
experiments/disco_inferno/disco/rules/defaults.json
```

`config.py` owns the rule schema and loading behavior. The reusable detector/scoring engine lives in `engine.py`. `artifacts.py` is the thin adapter between DiScO and the independent `doc_history` package.

## Bounded scoring model

Raw counts, match locations, and rates per 100 words remain the canonical observations. Each feature is compressed with the same asymptotic curve:

```text
strength = rate / (rate + half_saturation)
contribution = max_contribution × strength
```

Each rule exposes three scoring priors:

- `semantic_max` — semantic evidence budget: maximum contribution to the 0–1 semantic signal
- `ai_max` — AI evidence budget: maximum contribution to the 0–1 AI-oriented signal
- `half_saturation` — rate per 100 words where the feature reaches half of either budget

Both final signals are capped at `1.0`. Neither is a calibrated probability.

The implementation plan and raw prompt provenance for this scoring refactor are preserved in:

```text
experiments/disco_inferno/disco/docs/BOUNDED_SCORING_PROJECT_UPDATE_v0.2_2026-09-12.md
```

## Determinism

Same text + same configuration = same text profile. File-backed judgements additionally preserve the exact artifact dataset obtained from the uploaded bytes.

## Feedback loop

Each submitted judgement can be labelled `AI generated`. The label is metadata only and does not affect either calculated signal.

Judgements are appended locally to:

```text
data/disco/judgements.jsonl
```

Each record preserves:

- the full submitted/extracted text
- AI-generated label
- deterministic DiScO profile
- exact active rule snapshot
- text SHA-256
- rule-configuration SHA-256
- UTC timestamp
- for file uploads: filename plus the complete `doc_history` result, provenance clues, and timeline events

The repository already ignores `data/`, so the local corpus is not committed by ordinary Git workflows.

## Local rule migration

Mutable local rule overrides are stored at:

```text
data/disco/rules.json
```

If an older local override still uses the legacy `weight` / `ai_weight` schema, DiScO preserves its detector dictionaries and regex patterns while inheriting current bounded scoring priors for known rule IDs. Newly added checked-in rules are also merged into older local configurations automatically.

Saving from Disco Fever rewrites the local override in the current schema.

## Disco Fever

`pages/8_Disco_Fever.py` is the calibration page for DiScO. It can:

- change semantic evidence budget
- change AI evidence budget
- change half-saturation rate
- edit lexicon / stem dictionaries
- edit regex patterns
- reset the active configuration to checked-in defaults

Historical judgement records retain the exact rule snapshot used at scoring time, so later calibration does not rewrite provenance.

## Discotorium

`pages/8_Discotorium.py` is the corpus review page. It can:

- show judgement count, AI-labelled count, semantic/AI aggregate signals, mean words, and rule-configuration count
- distinguish bounded profiles from legacy density-multiplier profiles
- aggregate feature raw rates, strengths, semantic contributions, and AI contributions
- compare feature rates for AI-labelled vs not-marked-AI submissions
- filter and select individual judgements
- review the original text, stored profile, individual matches and character offsets
- inspect the exact rule snapshot used for each judgement
- inspect the raw stored JSON record, including file artifact metadata when present
- download the local JSONL corpus

Discotorium reads historical records as stored; it does not silently rescore them with the current rules.

## UI

- `pages/8_DiScO.py` — paste text or upload DOCX/PDF and run JUDGEMENT
- `pages/8_Disco_Fever.py` — calibrate active rules and bounded scoring priors
- `pages/8_Discotorium.py` — review stored judgements and aggregate corpus signals
