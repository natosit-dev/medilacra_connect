from experiments.disco_inferno.disco import (
    CADENCE_GUIDANCE,
    DEFAULT_RULES,
    FEATURE_GUIDANCE,
    get_feature_guidance,
)


def test_every_default_rule_has_dedicated_virgil_guidance():
    missing = [rule.id for rule in DEFAULT_RULES if rule.id not in FEATURE_GUIDANCE]
    assert missing == []


def test_unknown_rule_gets_safe_generic_guidance():
    guidance = get_feature_guidance("future_detector")
    assert "observable text pattern" in guidance.summary
    assert "No dedicated Virgil explanation" in guidance.caveat


def test_orwell_is_used_selectively_not_as_default_decoration():
    quoted = [guidance for guidance in FEATURE_GUIDANCE.values() if guidance.orwell_quote]
    assert 0 < len(quoted) < len(FEATURE_GUIDANCE)
    assert all(guidance.orwell_source for guidance in quoted)


def test_sentence_cadence_guidance_explicitly_says_it_is_unscored():
    assert "currently records" in CADENCE_GUIDANCE.why_it_matters
    assert "without scoring" in CADENCE_GUIDANCE.why_it_matters
