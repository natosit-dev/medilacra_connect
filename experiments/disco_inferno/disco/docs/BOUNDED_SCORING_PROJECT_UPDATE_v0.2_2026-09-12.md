# DiScO Bounded Scoring Model — Project Update Plan

**Version:** v0.2  
**Date:** 2026-09-12  
**Status:** Working implementation plan  
**Scope:** Replace arbitrary density multipliers with bounded 0–1 signal contributions while preserving the raw feature inventory as the canonical artifact.

## Raw prompt provenance

> “Yeah, it's just a probabilistic inventory of a text blob”

> “Cool, let's put together a project plan for what you have outlined. Reusable/configurable modules, not a suite of bespoke functions. Let's see it here”

> “There should be a checkbox that indicates the text blob is AI generated. Doesn't effect score, but it should be stored for later.”

> “I think we should also make a new page after DiScO called Disco Fever- it will be where we adjust weights, regex term dictionaries, etc.”

> “Same essay results, new stuff found!. Are we saving the full analysis somewhere for each text blob judged?”

> “Let's create a new page, call it Discotorium. Where we can review the analysis for individual blobs and see some basic aggregate stats”

> “Looking good. Just noticed something from deepseek. Maybe we should add MD notation as a something to look for?”

> “Let's add scaffolding inventory, weight it at 0.1 towards AI. UPdate and I'll retry”

> “I think we've gotta talk about weights. I'm probably confused XD”

> “I was thinking scale of 1,  0.1 max change in swoopy line up that's near impossible to reach”

> “And if the final AI score itself is intended to live on **0–1**, we should design the feature maxima deliberately rather than just letting them sum arbitrarily. Markdown gets at most `.10`; maybe a much stronger signal eventually gets `.30`, a weak one `.03`, etc. Then the score becomes legible: **the number expresses accumulated bounded evidence, not arbitrary units.**
>
> Ok, let's do this for all of them. Keep it stupid simple, let me review what you think it could look like and I'll confirm or request changes”

> “Ah, I meant 0.01 for nominalization, it's extremely noisy. Rest looks good.”

## Problem statement

The current scoring model multiplies feature density directly by a configured weight:

```text
current contribution = matches_per_100_words × weight
```

That makes the apparent meaning of a weight depend on the natural frequency of the feature. A common feature can dominate the score even when its configured weight is small.

Markdown scaffolding exposed the problem. A rate of 10.76 markers per 100 words at an AI weight of 0.1 produced an AI contribution of 1.076. The arithmetic was correct, but the semantics were wrong: `0.1` had been intended as a weak maximum nudge, not as a density multiplier.

## New scoring contract

Keep the raw inventory exactly as it is. Change only the compression step from raw feature density to bounded contribution.

```text
raw_rate = matches_per_100_words

strength = raw_rate / (raw_rate + half_saturation)

feature_contribution = max_contribution × strength

final_score = min(sum(feature_contributions), 1.0)
```

The curve rises quickly at first and then flattens. It approaches the configured maximum but cannot exceed it.

| Parameter | Meaning | Interpretation |
| --- | --- | --- |
| Raw rate | Observed matches per 100 words | Canonical inventory measurement |
| Half-saturation | Rate where the feature reaches 50% of its maximum | How much of the feature counts as substantial |
| Semantic max | Largest possible contribution to semantic signal | How much the feature is allowed to matter semantically |
| AI max | Largest possible contribution to AI signal | How much the feature is allowed to matter as authorship/style evidence |

## Proposed starting priors

These values are initial priors only. They should be revised through labeled testing in Discotorium.

| Feature | Semantic max | AI max | Half-sat /100 words |
| --- | ---: | ---: | ---: |
| Metaphor vocabulary | .05 | .02 | 2.0 |
| Mechanism placeholders | .10 | .04 | 2.0 |
| Anthropomorphic mechanism | .08 | .02 | 0.5 |
| **Nominalizations** | **.01** | .03 | 5.0 |
| Unintroduced acronyms | .05 | 0 | 2.0 |
| Ready-made phrases | .08 | .08 | 1.0 |
| Verbal false limbs | .12 | .03 | 1.0 |
| Worn / dead metaphors | .05 | .02 | 1.0 |
| Prestige / intimidating diction | .08 | .05 | 1.5 |
| Semantically sparse evaluative words | .18 | .08 | 3.0 |
| Concealment / euphemistic phrases | .16 | 0 | 1.0 |
| Markdown scaffolding | 0 | **.10** | 10.0 |

The semantic maxima do not need to sum to exactly 1.0 because the final signal itself is capped at 1.0. The AI maxima intentionally occupy only part of the available 0–1 range; the current evidence is too weak to justify a high-confidence AI authorship score.

## Rule schema update

Replace:

```text
weight
ai_weight
```

with:

```text
semantic_max
ai_max
half_saturation
```

Example:

```json
{
  "id": "markdown_scaffolding",
  "label": "Markdown scaffolding",
  "kind": "regex",
  "semantic_max": 0.0,
  "ai_max": 0.1,
  "half_saturation": 10.0,
  "pattern": "..."
}
```

## Engine update

The detector engine remains generic. No feature-specific scoring code should be introduced.

```text
rate = matches_per_100_words
strength = rate / (rate + rule.half_saturation)

semantic_contribution = strength × rule.semantic_max
ai_contribution = strength × rule.ai_max

semantic_score = min(sum(semantic_contributions), 1.0)
ai_score = min(sum(ai_contributions), 1.0)
```

## Stored profile update

Every stored feature result should preserve enough information to reconstruct the score without rerunning the detector.

```json
{
  "count": 38,
  "rate_per_100_words": 10.76,
  "half_saturation": 10.0,
  "strength": 0.518,
  "semantic_max": 0.0,
  "semantic_contribution": 0.0,
  "ai_max": 0.1,
  "ai_contribution": 0.052
}
```

## Historical provenance

Do not rewrite old JSONL judgements. Historical records remain valid statements of what DiScO produced under the rules that existed at the time. Their stored rule snapshots and rule hashes provide the necessary provenance.

Future rescoring, if added, must be explicitly represented as a separate result: original stored score versus rescore under a named current configuration.

## DiScO page

Top-level metrics become:

```text
Words
Characters
Semantic signal   0.000–1.000
AI signal         0.000–1.000
```

Primary feature table:

| Feature | Count | Rate /100 | Strength | Semantic contribution | AI contribution |
| --- | ---: | ---: | ---: | ---: | ---: |

The human `AI generated` checkbox remains visually and causally separate from the calculated AI signal. The checkbox is a label; the AI signal is model output.

## Disco Fever

Replace the current scoring controls with three generic fields per rule:

- **Semantic max** — maximum semantic contribution.
- **AI max** — maximum AI contribution.
- **Half-saturation** — matches per 100 words required to reach half of either maximum.

Dictionary and regex editing remain unchanged. `rules/defaults.json` remains the checked-in model definition; `data/disco/rules.json` remains the local override.

## Discotorium

Discotorium becomes the calibration surface for learning better priors from the stored corpus.

Add or preserve:

- mean and median raw rate by feature
- mean strength by feature
- mean semantic contribution by feature
- mean AI contribution by feature
- split feature statistics by the human `AI generated` label
- visible rule-configuration boundaries so incompatible historical scores are not silently treated as one model

## Tests

The scoring contract should be tested as properties:

- zero matches → zero contribution
- rate = half-saturation → contribution = max / 2
- higher rate → higher strength
- feature contribution never exceeds configured max
- semantic and AI signals never exceed 1.0
- same text + same rules → same profile
- human `AI generated` label cannot alter calculated scores
- Markdown regression: `10.76/100`, half-sat `10`, AI max `.10` → about `.052` contribution
- nominalization semantic contribution can never exceed `.01`

## Acceptance criterion

The refactor is accepted when existing detectors produce the same raw counts and rates while score compression follows the new bounded model.

Example:

```text
Markdown scaffolding

Count                     38
Rate / 100             10.76
Half-saturation         10.00
Strength                 .518
AI max                    .10
AI contribution           .052
```

A dense feature must no longer dominate merely because its base rate is high. The final numbers should be interpretable as bounded accumulated signal, not arbitrary units.

## Decision summary

- Raw inventory stays canonical: no change to counts, rates, matches, or offsets.
- Scoring becomes bounded using an asymptotic strength curve per feature.
- `weight` becomes explicit maximum contribution: `semantic_max` and `ai_max`.
- `half_saturation` controls how quickly each feature approaches its maximum.
- Nominalization is heavily down-weighted: **semantic max = 0.01**.
- Markdown remains authorship/style only: **semantic max = 0; AI max = 0.10**.
- Historical records remain immutable; no migration or silent rescoring.
- Priors will be learned empirically using the labeled corpus and Discotorium.
