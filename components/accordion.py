import streamlit as st
from components.summary_card import render_summary_card
import pandas as pd

def render_accordion_item(title, content_func, *args, **kwargs):
    """Render a custom accordion item with Stripe-like styling"""
    with st.expander(title):
        content_func(*args, **kwargs)

import re

def format_hour(hour_24):
    # Accepts int, float, or strings like '6:00', '18:00', '6am', '8pm', etc.
    if isinstance(hour_24, (int, float)) and not pd.isnull(hour_24):
        hour = int(hour_24)
    elif isinstance(hour_24, str):
        s = hour_24.strip().lower()
        if 'am' in s or 'pm' in s:
            return s
        match = re.match(r'^(\d{1,2}):', s)
        if match:
            hour = int(match.group(1))
        else:
            try:
                hour = int(s)
            except Exception:
                return hour_24
    else:
        return hour_24
    if hour == 0 or hour == 24:
        return "12am"
    elif hour == 12:
        return "12pm"
    elif hour < 12:
        return f"{hour}am"
    else:
        return f"{hour-12}pm"

def render_market_accordion(markets_data):
    """Render the market accordion list with data"""
    for market_name, market_data in markets_data.items():
        with st.expander(market_name):
            st.markdown('<div class="accordion-content">', unsafe_allow_html=True)
            
            # Prepare hourly data sorted by Total Plays descending
            df = pd.DataFrame(market_data["hourly_data"])
            if 'Hour' in df.columns and 'Total Plays' in df.columns:
                df = df.copy()
                df['Hour'] = df['Hour'].apply(lambda h: h if ("am" in str(h) or "pm" in str(h)) else format_hour(int(h) if isinstance(h, (int, float)) else h))
                df['Total Plays'] = df['Total Plays'].apply(lambda x: int(float(x)) if pd.notnull(x) else x)
                df = df.sort_values('Total Plays', ascending=False)
            # Top 3 hours
            top3 = df.head(3)
            card_titles = ["Top Hour", "2nd Hour", "3rd Hour"]
            st.markdown('<div class="accordion-summary-cards">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            for idx, col in enumerate([col1, col2, col3]):
                if idx < len(top3):
                    row = top3.iloc[idx]
                    hour = row['Hour']
                    total_plays = f"{int(row['Total Plays']):,}"
                    with col:
                        render_summary_card(card_titles[idx], hour, f"{total_plays} Total Plays")
            st.markdown('</div>', unsafe_allow_html=True)
            # Market data table
            st.dataframe(
                df[['Hour', 'Total Plays']],
                use_container_width=True,
                height=200,
                hide_index=True
            )
            st.markdown('</div>', unsafe_allow_html=True)