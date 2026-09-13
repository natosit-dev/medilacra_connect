from __future__ import annotations

import re

import streamlit as st

from experiments.disco_inferno.disco import (
    RUNTIME_RULES_PATH,
    FeatureRule,
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
            weight_col, ai_weight_col = st.columns(2)
            with weight_col:
                weight = st.number_input(
                    "Semantic weight",
                    value=float(rule.weight),
                    step=0.1,
                    key=f"weight-{rule.id}",
                    help="Contribution to the semantic signal score.",
                )
            with ai_weight_col:
                ai_weight = st.number_input(
                    "AI weight",
                    value=float(rule.ai_weight),
                    step=0.1,
                    key=f"ai-weight-{rule.id}",
                    help="Contribution to the separate AI-oriented signal score.",
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
                    "This is currently a structural detector. Its weights are configurable; "
                    "its underlying parser remains fixed in code."
                )

            edited_rules.append(
                FeatureRule(
                    id=rule.id,
                    label=rule.label,
                    kind=rule.kind,
                    weight=float(weight),
                    ai_weight=float(ai_weight),
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

st.caption("Use Discotorium to review stored judgements and corpus-level statistics.")
