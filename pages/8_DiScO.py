from __future__ import annotations

import pandas as pd
import streamlit as st

from experiments.disco_inferno.disco import DESCRIPTION, inspect_text, load_rules, record_judgement


st.title("🪩 DiScO")
st.caption(DESCRIPTION)
st.markdown(
    "**Disco Inferno submodel.** DiScO inventories cheap, observable text features "
    "associated with semantic reconstruction cost. Same text + same configuration produces the same profile."
)
st.info(
    "Semantic signal and AI signal are bounded 0–1 summaries of deterministic observations, not calibrated probabilities. "
    "The raw feature inventory remains the canonical artifact."
)

with st.form("disco_judgement"):
    text = st.text_area(
        "Free text",
        height=300,
        placeholder="Paste free text here...",
        help="Paste any text blob for deterministic feature inspection.",
    )
    ai_generated = st.checkbox(
        "AI generated",
        value=False,
        help="Feedback metadata only. The label is stored for later analysis and does not affect scoring.",
    )
    judge = st.form_submit_button("⚖️ JUDGEMENT", type="primary", use_container_width=True)

if judge:
    if not text.strip():
        st.warning("Paste some text first.")
    else:
        rules = load_rules()
        profile = inspect_text(text, rules=rules)
        record = record_judgement(
            text=text,
            profile=profile,
            ai_generated=ai_generated,
            rules=rules,
        )

        st.caption(
            f"Judgement saved locally: `{record['judgement_id']}` • "
            f"AI generated = `{record['ai_generated']}`. The label did not affect scoring."
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Words", f"{profile.word_count:,}")
        m2.metric("Characters", f"{profile.character_count:,}")
        m3.metric("Semantic signal", f"{profile.signal_score:.3f}")
        m4.metric("AI signal", f"{profile.ai_signal_score:.3f}")

        rows = [
            {
                "Feature": feature.label,
                "Count": feature.count,
                "Rate / 100": round(feature.rate_per_100_words, 3),
                "Strength": round(feature.strength, 3),
                "Semantic contribution": round(feature.semantic_contribution, 3),
                "AI contribution": round(feature.ai_contribution, 3),
            }
            for feature in profile.features
        ]
        st.markdown("### DiScO profile")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        with st.expander("Explain matches"):
            for feature in profile.features:
                st.markdown(f"#### {feature.label}")
                st.caption(
                    f"rate={feature.rate_per_100_words:.3f}/100 · "
                    f"half-saturation={feature.half_saturation:.3f} · "
                    f"strength={feature.strength:.3f} · "
                    f"semantic max={feature.semantic_max:.3f} · "
                    f"AI max={feature.ai_max:.3f}"
                )
                if not feature.matches:
                    st.caption("No matches.")
                    continue
                st.code("\n".join(match.text for match in feature.matches), language="text")

        with st.expander("Raw profile JSON"):
            st.json(profile.as_dict())
