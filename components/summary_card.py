import streamlit as st

def render_summary_card(title, value, subtitle):
    """Render a summary card with a value and subtitle"""
    st.markdown(
        f"""
        <div class="summary-card">
            <h3 class="summary-title">{title}</h3>
            <div class="summary-value">{value}</div>
            <div class="summary-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )