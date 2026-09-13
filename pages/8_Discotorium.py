from __future__ import annotations

from statistics import mean, median

import pandas as pd
import streamlit as st

from experiments.disco_inferno.disco import load_judgements


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


def _score(record: dict) -> float:
    return float(_profile(record).get("signal_score", 0.0) or 0.0)


def _words(record: dict) -> int:
    return int(_profile(record).get("word_count", 0) or 0)


# Aggregate corpus view -----------------------------------------------------
st.markdown("## Corpus overview")

scores = [_score(record) for record in records]
word_counts = [_words(record) for record in records]
ai_records = [record for record in records if record.get("ai_generated") is True]
not_ai_records = [record for record in records if record.get("ai_generated") is not True]
rule_versions = {str(record.get("rules_sha256", "")) for record in records if record.get("rules_sha256")}

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Judgements", f"{len(records):,}")
m2.metric("AI labelled", f"{len(ai_records):,}")
m3.metric("Mean score", f"{mean(scores):.2f}" if scores else "—")
m4.metric("Median score", f"{median(scores):.2f}" if scores else "—")
m5.metric("Rule configs", f"{len(rule_versions):,}")

s1, s2, s3 = st.columns(3)
s1.metric("Mean words", f"{mean(word_counts):,.0f}" if word_counts else "—")
s2.metric(
    "AI mean score",
    f"{mean(_score(record) for record in ai_records):.2f}" if ai_records else "—",
)
s3.metric(
    "Not marked AI mean",
    f"{mean(_score(record) for record in not_ai_records):.2f}" if not_ai_records else "—",
)

if len(rule_versions) > 1:
    st.info(
        "This corpus contains judgements produced under multiple rule configurations. "
        "Aggregate score comparisons are descriptive only; individual records retain their exact rule snapshot."
    )

feature_rows: dict[str, dict] = {}
for record in records:
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
                "contributions": [],
            },
        )
        rate = float(feature.get("rate_per_100_words", 0.0) or 0.0)
        weight = float(feature.get("weight", 0.0) or 0.0)
        bucket["Records"] += 1
        bucket["Total matches"] += int(feature.get("count", 0) or 0)
        bucket["rates"].append(rate)
        bucket["contributions"].append(rate * weight)

aggregate_feature_rows = []
for bucket in feature_rows.values():
    aggregate_feature_rows.append(
        {
            "Feature": bucket["Feature"],
            "Records": bucket["Records"],
            "Total matches": bucket["Total matches"],
            "Mean rate / 100 words": round(mean(bucket["rates"]), 3),
            "Mean score contribution": round(mean(bucket["contributions"]), 3),
        }
    )

if aggregate_feature_rows:
    st.markdown("### Feature aggregates")
    aggregate_df = pd.DataFrame(aggregate_feature_rows).sort_values(
        "Mean score contribution", ascending=False
    )
    st.dataframe(aggregate_df, use_container_width=True, hide_index=True)


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
    return (
        f"{recorded} · {ai_label} · {int(profile.get('word_count', 0) or 0):,} words · "
        f"score {_score(record):.2f} · {short_id}"
    )

selected_index = st.selectbox(
    "Judgement",
    options=range(len(filtered)),
    format_func=lambda index: _record_label(filtered[index]),
)
selected = filtered[selected_index]
profile = _profile(selected)

r1, r2, r3, r4 = st.columns(4)
r1.metric("Words", f"{int(profile.get('word_count', 0) or 0):,}")
r2.metric("Characters", f"{int(profile.get('character_count', 0) or 0):,}")
r3.metric("Signal score", f"{_score(selected):.2f}")
r4.metric("AI generated", "Yes" if selected.get("ai_generated") is True else "No")

st.caption(
    f"Judgement `{selected.get('judgement_id', '')}` · "
    f"Text SHA `{str(selected.get('text_sha256', ''))[:16]}` · "
    f"Rules SHA `{str(selected.get('rules_sha256', ''))[:16]}`"
)

st.text_area(
    "Original text",
    value=str(selected.get("text", "")),
    height=320,
    disabled=True,
)

feature_detail_rows = []
for feature in profile.get("features", []) or []:
    rate = float(feature.get("rate_per_100_words", 0.0) or 0.0)
    weight = float(feature.get("weight", 0.0) or 0.0)
    feature_detail_rows.append(
        {
            "Feature": feature.get("label", feature.get("id", "")),
            "Count": int(feature.get("count", 0) or 0),
            "Rate / 100 words": round(rate, 3),
            "Weight": weight,
            "Score contribution": round(rate * weight, 3),
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
