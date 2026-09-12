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

## Initial feature set

1. Metaphor vocabulary density
2. Mechanism-placeholder density
3. Anthropomorphic mechanism phrases
4. Nominalization density
5. Unintroduced acronym count

The feature definitions live in `config.py`; the reusable detector engine lives in `engine.py`.

## Determinism

Same text + same configuration = same profile.

## UI

`pages/8_DiScO.py` exposes the submodel as a Streamlit page adjacent to Disco Inferno.
