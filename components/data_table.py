import streamlit as st
import pandas as pd

def render_data_table(data_frame=None):
    """Render a data table wrapped in a card"""
    # If no data is provided, create a sample dataframe
    if data_frame is None:
        data_frame = pd.DataFrame({
            'Hour': [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
            'Play Rate': [0.12, 0.15, 0.21, 0.28, 0.32, 0.35, 0.30, 0.25, 0.18, 0.14],
            'Total Plays': [120, 150, 210, 280, 320, 350, 300, 250, 180, 140],
        })
    
    # Format hour column if present
    if 'Hour' in data_frame.columns:
        def format_hour(hour):
            try:
                h = int(hour) if isinstance(hour, (int, float)) else hour
                if h == 0 or h == 24:
                    return "12am"
                elif h == 12:
                    return "12pm"
                elif h < 12:
                    return f"{h}am"
                elif isinstance(h, str) and ("am" in h or "pm" in h):
                    return h
                else:
                    return f"{h-12}pm"
            except:
                return hour
        data_frame['Hour'] = data_frame['Hour'].apply(format_hour)
    # Format integer columns
    for col in data_frame.columns:
        if data_frame[col].dtype in ['float64', 'int64']:
            data_frame[col] = data_frame[col].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else x)
    st.dataframe(
        data_frame,
        use_container_width=True,
        height=300,
        hide_index=True
    )
    return data_frame