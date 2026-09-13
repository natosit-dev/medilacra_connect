from experiments.disco_inferno.disco import (
    DEFAULT_RULES,
    inspect_text,
    load_judgements,
    record_judgement,
)


def test_file_artifact_dataset_round_trip(tmp_path):
    text = "A small document for artifact provenance testing."
    profile = inspect_text(text, rules=DEFAULT_RULES)
    path = tmp_path / "judgements.jsonl"
    artifact = {
        "source_type": "file",
        "filename": "example.docx",
        "doc_history": {
            "type": "docx",
            "sha256": "abc123",
            "embedded_metadata": {"core": {"creator": "Example"}},
        },
        "timeline_events": [],
        "provenance_clues": ["Embedded creator: Example"],
    }

    record_judgement(
        text=text,
        profile=profile,
        ai_generated=False,
        rules=DEFAULT_RULES,
        path=path,
        artifact=artifact,
    )

    records = load_judgements(path=path)
    assert len(records) == 1
    assert records[0]["artifact"] == artifact
    assert records[0]["artifact"]["doc_history"]["sha256"] == "abc123"


def test_pasted_text_record_does_not_gain_empty_artifact_field(tmp_path):
    text = "Plain pasted text."
    profile = inspect_text(text, rules=DEFAULT_RULES)
    path = tmp_path / "judgements.jsonl"

    record_judgement(
        text=text,
        profile=profile,
        ai_generated=False,
        rules=DEFAULT_RULES,
        path=path,
    )

    records = load_judgements(path=path)
    assert "artifact" not in records[0]
