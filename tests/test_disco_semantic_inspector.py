import json

import pytest

from experiments.disco_inferno.disco import (
    DEFAULT_RULES,
    FeatureRule,
    inspect_text,
    load_judgements,
    load_rules,
    record_judgement,
    save_rules,
)


def _feature(profile, feature_id):
    return next(feature for feature in profile.features if feature.id == feature_id)


def test_metaphor_vocabulary_count():
    profile = inspect_text("The semantic substrate forms a shared vessel in a cognitive field.")
    assert _feature(profile, "metaphor_vocabulary").count == 3


def test_mechanism_placeholder_count():
    profile = inspect_text("The process steers attention, shapes context, and emerges as agreement.")
    assert _feature(profile, "mechanism_placeholders").count == 3


def test_anthropomorphic_mechanism_phrase():
    profile = inspect_text("The model wants to remember what the user meant.")
    feature = _feature(profile, "anthropomorphic_mechanism")
    assert feature.count == 1
    assert feature.matches[0].text.lower() == "model wants"


def test_nominalizations_are_counted():
    profile = inspect_text("The stabilization and representation of coordination changes interpretation.")
    assert _feature(profile, "nominalizations").count >= 4


def test_introduced_acronym_is_not_flagged():
    profile = inspect_text("Large Language Model (LLM) output is inspected.")
    assert _feature(profile, "unintroduced_acronyms").count == 0


def test_unintroduced_acronym_is_flagged():
    profile = inspect_text("The system moves through JSPACE before output.")
    feature = _feature(profile, "unintroduced_acronyms")
    assert feature.count == 1
    assert feature.matches[0].text == "JSPACE"


def test_plain_mechanical_sentence_is_negative_control():
    profile = inspect_text("The model stores the previous message in its current context.")
    assert _feature(profile, "anthropomorphic_mechanism").count == 0


def test_ready_made_phrase_is_counted():
    profile = inspect_text("At the end of the day, it is important to note that the system changed.")
    assert _feature(profile, "ready_made_phrases").count == 2


def test_verbal_false_limb_is_counted():
    profile = inspect_text("The change has the effect of reducing latency and gives rise to a new state.")
    assert _feature(profile, "verbal_false_limbs").count == 2


def test_dead_metaphor_is_counted():
    profile = inspect_text("We need to move the needle without boiling the ocean.")
    assert _feature(profile, "dead_metaphors").count == 2


def test_prestige_diction_is_counted():
    profile = inspect_text("The robust epistemic paradigm is multidimensional.")
    assert _feature(profile, "prestige_diction").count == 3


def test_semantically_sparse_words_are_counted():
    profile = inspect_text("Our strategic vision creates meaningful impact and authentic engagement.")
    assert _feature(profile, "semantically_sparse_words").count == 6


def test_concealment_euphemism_is_counted():
    profile = inspect_text("The company announced a workforce reduction and strategic realignment.")
    assert _feature(profile, "concealment_euphemisms").count == 2


def test_markdown_scaffolding_is_counted():
    text = "**What to do now**\n1. **Check your temperature.**\n2. **Hydrate** and rest."
    feature = _feature(inspect_text(text), "markdown_scaffolding")
    assert feature.count >= 5


def test_zero_matches_produce_zero_contribution():
    rules = (
        FeatureRule(
            id="example",
            label="Example",
            kind="lexicon",
            semantic_max=0.2,
            ai_max=0.1,
            half_saturation=1.0,
            terms=("signal",),
        ),
    )
    feature = _feature(inspect_text("nothing here", rules=rules), "example")
    assert feature.strength == 0.0
    assert feature.semantic_contribution == 0.0
    assert feature.ai_contribution == 0.0


def test_half_saturation_gives_half_maximum_contribution():
    rules = (
        FeatureRule(
            id="example",
            label="Example",
            kind="lexicon",
            semantic_max=0.2,
            ai_max=0.1,
            half_saturation=1.0,
            terms=("signal",),
        ),
    )
    text = "signal " + " ".join(["word"] * 99)
    feature = _feature(inspect_text(text, rules=rules), "example")
    assert feature.rate_per_100_words == pytest.approx(1.0)
    assert feature.strength == pytest.approx(0.5)
    assert feature.semantic_contribution == pytest.approx(0.1)
    assert feature.ai_contribution == pytest.approx(0.05)


def test_strength_is_monotonic_with_rate():
    rules = (
        FeatureRule(
            id="example",
            label="Example",
            kind="lexicon",
            semantic_max=0.2,
            half_saturation=1.0,
            terms=("signal",),
        ),
    )
    low = _feature(inspect_text("signal " + " ".join(["word"] * 99), rules=rules), "example")
    high = _feature(inspect_text(" ".join(["signal"] * 10 + ["word"] * 90), rules=rules), "example")
    assert high.rate_per_100_words > low.rate_per_100_words
    assert high.strength > low.strength
    assert high.semantic_contribution > low.semantic_contribution


def test_feature_contribution_never_exceeds_maximum():
    rules = (
        FeatureRule(
            id="example",
            label="Example",
            kind="lexicon",
            semantic_max=0.2,
            ai_max=0.1,
            half_saturation=0.01,
            terms=("signal",),
        ),
    )
    feature = _feature(inspect_text(" ".join(["signal"] * 1000), rules=rules), "example")
    assert feature.semantic_contribution < 0.2
    assert feature.ai_contribution < 0.1


def test_total_signals_are_capped_at_one():
    rules = (
        FeatureRule(
            id="foo",
            label="Foo",
            kind="lexicon",
            semantic_max=0.8,
            ai_max=0.8,
            half_saturation=0.01,
            terms=("foo",),
        ),
        FeatureRule(
            id="bar",
            label="Bar",
            kind="lexicon",
            semantic_max=0.8,
            ai_max=0.8,
            half_saturation=0.01,
            terms=("bar",),
        ),
    )
    profile = inspect_text(" ".join(["foo"] * 100 + ["bar"] * 100), rules=rules)
    assert profile.signal_score == 1.0
    assert profile.ai_signal_score == 1.0


def test_markdown_regression_is_small_bounded_ai_nudge():
    text = " ".join(["**x**"] * 38 + ["word"] * 315)
    profile = inspect_text(text)
    feature = _feature(profile, "markdown_scaffolding")
    assert profile.word_count == 353
    assert feature.count == 38
    assert feature.rate_per_100_words == pytest.approx(10.7649, rel=1e-4)
    assert feature.strength == pytest.approx(0.5184, rel=1e-3)
    assert feature.ai_max == pytest.approx(0.10)
    assert feature.ai_contribution == pytest.approx(0.05184, rel=1e-3)
    assert feature.semantic_contribution == 0.0


def test_nominalization_semantic_contribution_is_capped_at_one_percent():
    profile = inspect_text(" ".join(["transformation"] * 500))
    feature = _feature(profile, "nominalizations")
    assert feature.semantic_max == pytest.approx(0.01)
    assert 0.0 < feature.semantic_contribution < 0.01


def test_same_text_same_profile():
    text = "The model wants a semantic substrate."
    assert inspect_text(text).as_dict() == inspect_text(text).as_dict()


def test_runtime_rule_round_trip(tmp_path):
    path = tmp_path / "rules.json"
    rules = (
        FeatureRule(
            id="example",
            label="Example",
            kind="lexicon",
            semantic_max=0.25,
            ai_max=0.05,
            half_saturation=2.0,
            terms=("foo", "bar"),
        ),
    )
    save_rules(rules, path=path)
    loaded = load_rules(path=path)
    example = next(rule for rule in loaded if rule.id == "example")
    assert example == rules[0]


def test_legacy_local_override_inherits_bounded_scoring_and_new_defaults(tmp_path):
    path = tmp_path / "rules.json"
    legacy = [
        {
            "id": "nominalizations",
            "label": "Nominalizations",
            "kind": "regex",
            "weight": 99.0,
            "pattern": r"\bfoo\b",
        }
    ]
    path.write_text(json.dumps(legacy), encoding="utf-8")
    loaded = load_rules(path=path)
    nominalizations = next(rule for rule in loaded if rule.id == "nominalizations")
    markdown = next(rule for rule in loaded if rule.id == "markdown_scaffolding")
    assert nominalizations.semantic_max == pytest.approx(0.01)
    assert nominalizations.pattern == r"\bfoo\b"
    assert markdown.ai_max == pytest.approx(0.10)


def test_ai_generated_feedback_is_metadata_only(tmp_path):
    text = "The semantic substrate shapes the field."
    profile = inspect_text(text, rules=DEFAULT_RULES)
    path = tmp_path / "judgements.jsonl"

    record_judgement(
        text=text,
        profile=profile,
        ai_generated=True,
        rules=DEFAULT_RULES,
        path=path,
    )

    records = load_judgements(path=path)
    assert len(records) == 1
    assert records[0]["ai_generated"] is True
    assert records[0]["text"] == text
    assert records[0]["profile"]["signal_score"] == profile.signal_score
    assert records[0]["profile"]["ai_signal_score"] == profile.ai_signal_score
