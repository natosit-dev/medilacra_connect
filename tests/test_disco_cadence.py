import pytest

from experiments.disco_inferno.disco import (
    DEFAULT_RULES,
    inspect_sentence_cadence,
    inspect_text,
    load_judgements,
    record_judgement,
    sentence_word_lengths,
)


def test_sentence_cadence_records_raw_lengths_and_range():
    text = "Short now. This sentence has exactly six words total. Tiny."
    cadence = inspect_sentence_cadence(text)

    assert cadence.sentence_lengths == (2, 7, 1)
    assert cadence.sentence_count == 3
    assert cadence.mean_words == pytest.approx(10 / 3)
    assert cadence.min_words == 1
    assert cadence.max_words == 7
    assert cadence.range_words == 6
    assert cadence.std_dev_words > 0
    assert cadence.coefficient_of_variation > 0


def test_sentence_cadence_protects_common_abbreviations_and_decimals():
    text = "Dr. Smith measured 3.14 units. It worked."
    assert len(sentence_word_lengths(text)) == 2


def test_uniform_sentences_have_zero_variation():
    text = "One two three. Four five six. Seven eight nine."
    cadence = inspect_sentence_cadence(text)

    assert cadence.sentence_lengths == (3, 3, 3)
    assert cadence.std_dev_words == pytest.approx(0.0)
    assert cadence.coefficient_of_variation == pytest.approx(0.0)
    assert cadence.range_words == 0


def test_cadence_is_persisted_without_changing_scores(tmp_path):
    text = "Short now. This sentence has exactly six words total. Tiny."
    profile = inspect_text(text, rules=DEFAULT_RULES)
    path = tmp_path / "judgements.jsonl"

    record_judgement(
        text=text,
        profile=profile,
        ai_generated=False,
        rules=DEFAULT_RULES,
        path=path,
    )

    stored = load_judgements(path=path)[0]
    cadence = stored["sentence_cadence"]

    assert cadence["sentence_lengths"] == [2, 7, 1]
    assert cadence["range_words"] == 6
    assert stored["profile"]["signal_score"] == profile.signal_score
    assert stored["profile"]["ai_signal_score"] == profile.ai_signal_score
