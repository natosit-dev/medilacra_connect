from __future__ import annotations

import pandas as pd
import streamlit as st

from experiments.disco_inferno.disco import DESCRIPTION, inspect_text


st.title("🪩 DiScO")
st.caption(DESCRIPTION)
st.markdown(
    "**Disco Inferno submodel.** DiScO inventories cheap, observable text features "
    "associated with semantic reconstruction cost. Same text + same configuration "
    "produces the same profile."
)
st.info(
    "DiScO does not detect truth, intelligence, private understanding, or AI authorship. "
    "The signal score is a simple weighted summary of deterministic observations, not a calibrated probability."
)

with st.form("disco_judgement"):
    text = st.text_area(
        "Free text",
        height=300,
        placeholder="Paste free text here...",
        help="Paste any text blob for deterministic feature inspection.",
    )
    judge = st.form_submit_button(
        "⚖️ JUDGEMENT",
        type="primary",
        use_container_width=True,
    )

if judge:
    if not text.strip():
        st.warning("Paste some text first.")
    else:
        profile = inspect_text(text)

        m1, m2, m3 = st.columns(3)
        m1.metric("Words", f"{profile.word_count:,}")
        m2.metric("Characters", f"{profile.character_count:,}")
        m3.metric("Signal score", f"{profile.signal_score:.2f}")

        rows = [
            {
                "Feature": feature.label,
                "Count": feature.count,
                "Rate / 100 words": round(feature.rate_per_100_words, 2),
                "Weight": feature.weight,
            }
            for feature in profile.features
        ]
        st.markdown("### DiScO profile")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        with st.expander("Explain matches"):
            for feature in profile.features:
                st.markdown(f"#### {feature.label}")
                if not feature.matches:
                    st.caption("No matches.")
                    continue
                st.code("\n".join(match.text for match in feature.matches), language="text")

        with st.expander("Raw profile JSON"):
            st.json(profile.as_dict())
