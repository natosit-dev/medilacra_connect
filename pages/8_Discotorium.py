from __future__ import annotations

from statistics import mean, median

import pandas as pd
import streamlit as st

from experiments.disco_inferno.disco import FEEDBACK_PATH, load_judgements


st.title("🏛️ Discotorium")
st.caption("Review stored DiScO judgements and corpus-level signals")
st.markdown(
    "Discotorium reads the local DiScO judgement corpus. It does not rescore text: "
    "individual records are shown exactly as they were saved, with their original rule snapshot."
)

records = load_judgements()

if not records:
    st.info("No stored judgements yet. Run text through DiScO to populate the Discotorium.")
    st.stop()


def _profile(record: dict) -> dict:
    return record.get("profile", {}) or {}


def _semantic_score(record: dict) -> float:
    return float(_profile(record).get("signal_score", 0.0) or 0.0)


def _ai_signal(record: dict) -> float | None:
    value = _profile(record).get("ai_signal_score")
    return None if value is None else float(value or 0.0)


def _words(record: dict) -> int:
    return int(_profile(record).get("word_count", 0) or 0)


def _rate(feature: dict) -> float:
    return float(feature.get("rate_per_100_words", 0.0) or 0.0)


def _strength(feature: dict) -> float | None:
    value = feature.get("strength")
    return None if value is None else float(value or 0.0)


def _semantic_contribution(feature: dict) -> float:
    if "semantic_contribution" in feature:
        return float(feature.get("semantic_contribution", 0.0) or 0.0)
    return _rate(feature) * float(feature.get("weight", 0.0) or 0.0)


def _ai_contribution(feature: dict) -> float:
    if "ai_contribution" in feature:
        return float(feature.get("ai_contribution", 0.0) or 0.0)
    return _rate(feature) * float(feature.get("ai_weight", 0.0) or 0.0)


def _is_bounded_profile(record: dict) -> bool:
    features = _profile(record).get("features", []) or []
    return bool(features) and all("strength" in feature for feature in features)


# Aggregate corpus view -----------------------------------------------------
st.markdown("## Corpus overview")

semantic_scores = [_semantic_score(record) for record in records]
ai_signals = [value for record in records if (value := _ai_signal(record)) is not None]
word_counts = [_words(record) for record in records]
ai_records = [record for record in records if record.get("ai_generated") is True]
not_ai_records = [record for record in records if record.get("ai_generated") is not True]
rule_versions = {str(record.get("rules_sha256", "")) for record in records if record.get("rules_sha256")}
bounded_records = [record for record in records if _is_bounded_profile(record)]
legacy_records = [record for record in records if not _is_bounded_profile(record)]

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Judgements", f"{len(records):,}")
m2.metric("AI labelled", f"{len(ai_records):,}")
m3.metric("Mean semantic", f"{mean(semantic_scores):.3f}" if semantic_scores else "—")
m4.metric("Mean AI signal", f"{mean(ai_signals):.3f}" if ai_signals else "—")
m5.metric("Rule configs", f"{len(rule_versions):,}")

s1, s2, s3, s4 = st.columns(4)
s1.metric("Median semantic", f"{median(semantic_scores):.3f}" if semantic_scores else "—")
s2.metric("Median AI signal", f"{median(ai_signals):.3f}" if ai_signals else "—")
s3.metric("Mean words", f"{mean(word_counts):,.0f}" if word_counts else "—")
s4.metric("Bounded / legacy", f"{len(bounded_records)} / {len(legacy_records)}")

if len(rule_versions) > 1 or legacy_records:
    st.info(
        "This corpus contains historical judgements produced under different scoring configurations. "
        "Legacy density-multiplier scores and new bounded scores are preserved as originally stored and are not silently normalized together. "
        "Aggregate values are descriptive only."
    )

feature_rows: dict[str, dict] = {}
for record in records:
    labelled_ai = record.get("ai_generated") is True
    for feature in _profile(record).get("features", []) or []:
        feature_id = str(feature.get("id", ""))
        if not feature_id:
            continue
        bucket = feature_rows.setdefault(
            feature_id,
            {
                "Feature": feature.get("label", feature_id),
                "Records": 0,
                "Total matches": 0,
                "rates": [],
                "strengths": [],
                "semantic_contributions": [],
                "ai_contributions": [],
                "ai_label_rates": [],
                "not_ai_label_rates": [],
            },
        )
        rate = _rate(feature)
        strength = _strength(feature)
        bucket["Records"] += 1
        bucket["Total matches"] += int(feature.get("count", 0) or 0)
        bucket["rates"].append(rate)
        if strength is not None:
            bucket["strengths"].append(strength)
        bucket["semantic_contributions"].append(_semantic_contribution(feature))
        bucket["ai_contributions"].append(_ai_contribution(feature))
        if labelled_ai:
            bucket["ai_label_rates"].append(rate)
        else:
            bucket["not_ai_label_rates"].append(rate)

aggregate_feature_rows = []
for bucket in feature_rows.values():
    aggregate_feature_rows.append(
        {
            "Feature": bucket["Feature"],
            "Records": bucket["Records"],
            "Total matches": bucket["Total matches"],
            "Mean rate / 100": round(mean(bucket["rates"]), 3),
            "Median rate / 100": round(median(bucket["rates"]), 3),
            "Mean strength": round(mean(bucket["strengths"]), 3) if bucket["strengths"] else None,
            "Mean semantic contribution": round(mean(bucket["semantic_contributions"]), 3),
            "Mean AI contribution": round(mean(bucket["ai_contributions"]), 3),
            "AI-labelled mean rate": round(mean(bucket["ai_label_rates"]), 3) if bucket["ai_label_rates"] else None,
            "Not-AI mean rate": round(mean(bucket["not_ai_label_rates"]), 3) if bucket["not_ai_label_rates"] else None,
        }
    )

if aggregate_feature_rows:
    st.markdown("### Feature aggregates")
    aggregate_df = pd.DataFrame(aggregate_feature_rows).sort_values(
        "Mean semantic contribution", ascending=False
    )
    st.dataframe(aggregate_df, use_container_width=True, hide_index=True)

if FEEDBACK_PATH.exists():
    st.download_button(
        "Download feedback corpus (JSONL)",
        data=FEEDBACK_PATH.read_bytes(),
        file_name="disco_judgements.jsonl",
        mime="application/jsonl",
        use_container_width=True,
    )
    st.caption(f"Local feedback corpus: `{FEEDBACK_PATH}`")


# Individual judgement review ----------------------------------------------
st.markdown("## Individual judgements")

filter_choice = st.radio(
    "Show",
    options=("All", "AI generated", "Not marked AI"),
    horizontal=True,
)

if filter_choice == "AI generated":
    filtered = ai_records
elif filter_choice == "Not marked AI":
    filtered = not_ai_records
else:
    filtered = records

filtered = list(reversed(filtered))

if not filtered:
    st.info("No judgements match this filter.")
    st.stop()


def _record_label(record: dict) -> str:
    recorded = str(record.get("recorded_at", ""))
    ai_label = "AI" if record.get("ai_generated") is True else "not marked AI"
    profile = _profile(record)
    short_id = str(record.get("judgement_id", ""))[:8]
    ai_signal = _ai_signal(record)
    ai_part = f" · AI signal {ai_signal:.3f}" if ai_signal is not None else ""
    return (
        f"{recorded} · {ai_label} · {int(profile.get('word_count', 0) or 0):,} words · "
        f"semantic {_semantic_score(record):.3f}{ai_part} · {short_id}"
    )

selected_index = st.selectbox(
    "Judgement",
    options=range(len(filtered)),
    format_func=lambda index: _record_label(filtered[index]),
)
selected = filtered[selected_index]
profile = _profile(selected)
selected_ai_signal = _ai_signal(selected)

r1, r2, r3, r4, r5 = st.columns(5)
r1.metric("Words", f"{int(profile.get('word_count', 0) or 0):,}")
r2.metric("Characters", f"{int(profile.get('character_count', 0) or 0):,}")
r3.metric("Semantic signal", f"{_semantic_score(selected):.3f}")
r4.metric("AI signal", f"{selected_ai_signal:.3f}" if selected_ai_signal is not None else "—")
r5.metric("AI generated", "Yes" if selected.get("ai_generated") is True else "No")

st.caption(
    f"Judgement `{selected.get('judgement_id', '')}` · "
    f"Text SHA `{str(selected.get('text_sha256', ''))[:16]}` · "
    f"Rules SHA `{str(selected.get('rules_sha256', ''))[:16]}` · "
    f"Scoring model = `{'bounded' if _is_bounded_profile(selected) else 'legacy'}`"
)

st.text_area(
    "Original text",
    value=str(selected.get("text", "")),
    height=320,
    disabled=True,
)

feature_detail_rows = []
for feature in profile.get("features", []) or []:
    strength = _strength(feature)
    feature_detail_rows.append(
        {
            "Feature": feature.get("label", feature.get("id", "")),
            "Count": int(feature.get("count", 0) or 0),
            "Rate / 100": round(_rate(feature), 3),
            "Strength": round(strength, 3) if strength is not None else None,
            "Semantic contribution": round(_semantic_contribution(feature), 3),
            "AI contribution": round(_ai_contribution(feature), 3),
        }
    )

st.markdown("### Stored DiScO profile")
if feature_detail_rows:
    st.dataframe(pd.DataFrame(feature_detail_rows), use_container_width=True, hide_index=True)
else:
    st.caption("No stored feature profile.")

with st.expander("Explain stored matches", expanded=True):
    for feature in profile.get("features", []) or []:
        st.markdown(f"#### {feature.get('label', feature.get('id', 'Feature'))}")
        matches = feature.get("matches", []) or []
        if not matches:
            st.caption("No matches.")
            continue
        match_rows = [
            {
                "Match": match.get("text", ""),
                "Start": match.get("start", ""),
                "End": match.get("end", ""),
            }
            for match in matches
        ]
        st.dataframe(pd.DataFrame(match_rows), use_container_width=True, hide_index=True)

with st.expander("Rule snapshot used for this judgement"):
    st.json(selected.get("rules", []))

with st.expander("Raw stored judgement JSON"):
    st.json(selected)
