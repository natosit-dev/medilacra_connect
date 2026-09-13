# DiScO Sentence Cadence Observations

Date: 2026-09-13
Status: observational only; no scoring prior assigned

## Decision

DiScO now records sentence cadence as a deterministic observation block on each newly stored judgement. The purpose is to preserve enough raw structure to study two concepts later without prematurely deciding that either one is evidence of AI authorship.

### Uniformity

Uniformity asks: how tightly do sentence lengths cluster around their average?

Recorded observations:

- sentence count
- raw sentence-length sequence in words
- mean sentence length
- population standard deviation of sentence length
- coefficient of variation (`std_dev / mean`)

### Range

Range asks: how far apart are the shortest and longest sentences?

Recorded observations:

- shortest sentence length
- longest sentence length
- range (`max - min`)

## Canonical data

The raw sentence-length sequence is the canonical cadence observation. Derived summaries are deliberately replaceable.

Example:

```json
{
  "sentence_cadence": {
    "sentence_count": 7,
    "sentence_lengths": [3, 18, 21, 6, 43, 17, 5],
    "mean_words": 16.14,
    "std_dev_words": 12.83,
    "coefficient_of_variation": 0.79,
    "min_words": 3,
    "max_words": 43,
    "range_words": 40
  }
}
```

## Scoring boundary

Sentence cadence currently contributes **zero** to both semantic and AI signals. No threshold, prior, preferred range, minimum sentence count, or AI association has been encoded yet. The corpus should establish whether the observations carry useful signal before DiScO assigns them a scoring budget.

## Segmentation

The first implementation intentionally uses a small deterministic sentence splitter with no external NLP dependency. It protects common abbreviations, initials/initialisms, and decimal points before treating `.`, `?`, and `!` as sentence boundaries. This is cheap and reproducible, but the raw text remains available if sentence segmentation is refined later.

## Persistence

New judgements store `sentence_cadence` alongside the existing text, rule snapshot, hashes, labels, and DiScO profile. Because individual judgement downloads serialize the complete stored record, cadence observations are automatically included in both the main DiScO download and Discotorium individual downloads.
