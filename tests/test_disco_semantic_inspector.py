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
            weight=2.5,
            terms=("foo", "bar"),
        ),
    )
    save_rules(rules, path=path)
    assert load_rules(path=path) == rules


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
