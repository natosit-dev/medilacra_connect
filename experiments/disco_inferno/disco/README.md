# DiScO

**Deterministic Inspection of Semantic Coupling in Outputs**

DiScO is a Disco Inferno submodel for cheap, deterministic inventories of observable text features associated with semantic reconstruction cost.

## Working boundary

DiScO does **not** determine truth, intelligence, private understanding, or AI authorship. It inventories surface features in a text blob and optionally compresses them into a simple signal score.

The canonical artifact is the feature inventory. The score is derived and replaceable.

```text
text blob
  -> deterministic observations
  -> feature inventory
  -> optional weighted signal score
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

The later rule families are informed by the current Mao / Orwell provenance work, but they remain candidate signals rather than validated measurements of slop.

The checked-in rule definitions, weights, phrase dictionaries, and regex patterns live in:

```text
experiments/disco_inferno/disco/rules/defaults.json
```

`config.py` only owns the rule schema and loading behavior. The reusable detector engine lives in `engine.py`.

## Determinism

Same text + same configuration = same profile.

## Feedback loop

Each submitted judgement can be labelled `AI generated`. The label is metadata only and does not affect scoring.

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

## Disco Fever

`pages/8_Disco_Fever.py` is the calibration page for DiScO. It can:

- change feature weights
- edit lexicon / stem dictionaries
- edit regex patterns
- reset the active configuration to checked-in defaults

Mutable local rule overrides are stored at:

```text
data/disco/rules.json
```

Historical judgement records retain the exact rule snapshot used at scoring time, so later calibration does not rewrite provenance.

## Discotorium

`pages/8_Discotorium.py` is the corpus review page. It can:

- show judgement count, AI-labelled count, mean and median score, mean words, and rule-configuration count
- compare mean scores for AI-labelled vs not-marked-AI submissions
- aggregate feature match rates and score contributions across the stored corpus
- filter and select individual judgements
- review the original text, stored profile, individual matches and character offsets
- inspect the exact rule snapshot used for each judgement
- inspect the raw stored JSON record
- download the local JSONL corpus

Discotorium reads historical records as stored; it does not silently rescore them with the current rules.

## UI

- `pages/8_DiScO.py` — submit text and run JUDGEMENT
- `pages/8_Disco_Fever.py` — calibrate active rules
- `pages/8_Discotorium.py` — review stored judgements and aggregate corpus signals
