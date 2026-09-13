# DiScO

**Deterministic Inspection of Semantic Coupling in Outputs**

DiScO is a Disco Inferno submodel for cheap, deterministic inventories of observable text features associated with semantic reconstruction cost and experimental authorship/style signals.

## Working boundary

DiScO does **not** determine truth, intelligence, private understanding, or AI authorship. It inventories surface features in a text blob and optionally compresses them into bounded signal scores.

The canonical artifact is the feature inventory. Scores are derived and replaceable.

```text
text blob
  -> deterministic observations
  -> feature inventory
  -> bounded feature strengths
  -> bounded semantic / AI signals
```

## Active default feature set

The checked-in defaults currently inventory:

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
12. Markdown scaffolding

The later rule families are informed by the current Mao / Orwell provenance work, but they remain candidate signals rather than validated measurements of slop. Markdown scaffolding is currently treated as an AI-oriented style/provenance signal, not a semantic-slop signal.

The checked-in rule definitions, priors, phrase dictionaries, and regex patterns live in:

```text
experiments/disco_inferno/disco/rules/defaults.json
```

`config.py` owns the rule schema and loading behavior. The reusable detector/scoring engine lives in `engine.py`.

## Bounded scoring model

Raw counts, match locations, and rates per 100 words remain the canonical observations. Each feature is compressed with the same asymptotic curve:

```text
strength = rate / (rate + half_saturation)
contribution = max_contribution × strength
```

Each rule exposes three scoring priors:

- `semantic_max` — maximum contribution to the 0–1 semantic signal
- `ai_max` — maximum contribution to the 0–1 AI-oriented signal
- `half_saturation` — rate per 100 words where the feature reaches half of either maximum

Both final signals are capped at `1.0`. Neither is a calibrated probability.

The implementation plan and raw prompt provenance for this scoring refactor are preserved in:

```text
experiments/disco_inferno/disco/docs/BOUNDED_SCORING_PROJECT_UPDATE_v0.2_2026-09-12.md
```

## Determinism

Same text + same configuration = same profile.

## Feedback loop

Each submitted judgement can be labelled `AI generated`. The label is metadata only and does not affect either calculated signal.

Judgements are appended locally to:

```text
data/disco/judgements.jsonl
```

Each record preserves:

- the full submitted text
- AI-generated label
- deterministic DiScO profile
- exact active rule snapshot
- text SHA-256
- rule-configuration SHA-256
- UTC timestamp

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

- change semantic maximum contribution
- change AI maximum contribution
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
- inspect the raw stored JSON record
- download the local JSONL corpus

Discotorium reads historical records as stored; it does not silently rescore them with the current rules.

## UI

- `pages/8_DiScO.py` — submit text and run JUDGEMENT
- `pages/8_Disco_Fever.py` — calibrate active rules and bounded scoring priors
- `pages/8_Discotorium.py` — review stored judgements and aggregate corpus signals
