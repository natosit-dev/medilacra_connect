from __future__ import annotations

import re
from statistics import mean

import pandas as pd
import streamlit as st

from experiments.disco_inferno.disco import (
    FEEDBACK_PATH,
    RUNTIME_RULES_PATH,
    FeatureRule,
    load_judgements,
    load_rules,
    reset_rules,
    save_rules,
)


st.title("🕺 Disco Fever")
st.caption("DiScO calibration console")
st.markdown(
    "Adjust the active DiScO weights and detector dictionaries without changing the detector engine. "
    "Changes are stored locally and are applied to future judgements."
)
st.info(
    "Disco Fever changes configuration, not historical profiles. Each stored judgement keeps the exact rule snapshot used when it was scored."
)

rules = load_rules()

st.markdown("## Active rules")
with st.form("disco_fever_rules"):
    edited_rules: list[FeatureRule] = []

    for rule in rules:
        with st.expander(f"{rule.label} · `{rule.id}`", expanded=True):
            st.caption(f"Detector type: `{rule.kind}`")
            weight = st.number_input(
                "Weight",
                value=float(rule.weight),
                step=0.1,
                key=f"weight-{rule.id}",
                help="Weights affect only the derived signal score. Raw feature counts remain unchanged.",
            )

            terms = rule.terms
            pattern = rule.pattern

            if rule.kind in {"lexicon", "lexicon_stem"}:
                terms_text = st.text_area(
                    "Term dictionary — one term per line",
                    value="\n".join(rule.terms),
                    height=160,
                    key=f"terms-{rule.id}",
                )
                terms = tuple(
                    line.strip()
                    for line in terms_text.splitlines()
                    if line.strip()
                )
            elif rule.kind == "regex":
                pattern = st.text_area(
                    "Regex pattern",
                    value=rule.pattern or "",
                    height=120,
                    key=f"pattern-{rule.id}",
                ).strip()
            else:
                st.caption(
                    "This is currently a structural detector. Its weight is configurable; "
                    "its underlying parser remains fixed in code."
                )

            edited_rules.append(
                FeatureRule(
                    id=rule.id,
                    label=rule.label,
                    kind=rule.kind,
                    weight=float(weight),
                    terms=terms,
                    pattern=pattern,
                )
            )

    save = st.form_submit_button(
        "🔥 SAVE FEVER SETTINGS",
        type="primary",
        use_container_width=True,
    )

if save:
    errors: list[str] = []
    for rule in edited_rules:
        if rule.kind == "regex":
            if not rule.pattern:
                errors.append(f"{rule.label}: regex pattern cannot be empty.")
                continue
            try:
                re.compile(rule.pattern, re.IGNORECASE)
            except re.error as exc:
                errors.append(f"{rule.label}: {exc}")
        if rule.kind in {"lexicon", "lexicon_stem"} and not rule.terms:
            errors.append(f"{rule.label}: term dictionary cannot be empty.")

    if errors:
        st.error("Configuration was not saved.")
        for error in errors:
            st.code(error, language="text")
    else:
        path = save_rules(tuple(edited_rules))
        st.success(f"Saved active DiScO configuration to `{path}`.")
        st.rerun()

reset_col, path_col = st.columns([1, 3])
with reset_col:
    if st.button("Reset to defaults", use_container_width=True):
        reset_rules()
        st.rerun()
with path_col:
    st.caption(f"Local overrides: `{RUNTIME_RULES_PATH}`")


st.markdown("## Feedback corpus")
records = load_judgements()

if not records:
    st.info("No stored judgements yet. Run text through DiScO to begin the feedback corpus.")
else:
    ai_records = [record for record in records if record.get("ai_generated") is True]
    unmarked_records = [record for record in records if record.get("ai_generated") is not True]

    def _scores(items: list[dict]) -> list[float]:
        return [float(item.get("profile", {}).get("signal_score", 0.0)) for item in items]

    all_scores = _scores(records)
    ai_scores = _scores(ai_records)
    unmarked_scores = _scores(unmarked_records)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Judgements", f"{len(records):,}")
    m2.metric("AI generated", f"{len(ai_records):,}")
    m3.metric("AI mean score", f"{mean(ai_scores):.2f}" if ai_scores else "—")
    m4.metric(
        "Not marked AI mean",
        f"{mean(unmarked_scores):.2f}" if unmarked_scores else "—",
    )

    rows = []
    for record in reversed(records[-100:]):
        profile = record.get("profile", {})
        rows.append(
            {
                "Recorded": record.get("recorded_at", ""),
                "AI generated": bool(record.get("ai_generated", False)),
                "Words": profile.get("word_count", 0),
                "Signal score": round(float(profile.get("signal_score", 0.0)), 2),
                "Text SHA": str(record.get("text_sha256", ""))[:12],
                "Rules SHA": str(record.get("rules_sha256", ""))[:12],
            }
        )

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(
        "The table shows the most recent 100 judgements. Full text, profile, AI label, and rule snapshot "
        "are stored in the local JSONL corpus."
    )

    if FEEDBACK_PATH.exists():
        st.download_button(
            "Download feedback corpus (JSONL)",
            data=FEEDBACK_PATH.read_bytes(),
            file_name="disco_judgements.jsonl",
            mime="application/jsonl",
            use_container_width=True,
        )
        st.caption(f"Local feedback corpus: `{FEEDBACK_PATH}`")
