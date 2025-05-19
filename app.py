import streamlit as st
from components.sidebar import render_sidebar
from components.upload import render_upload_dropzone
from components.overview import render_overview
from components.market_drilldown import render_market_drilldown
from styles.custom import apply_custom_styles

# Page configuration
st.set_page_config(
    page_title="Top Plays Finder - Airports",
    page_icon="✈️", # Or a custom SVG string for a sharper icon
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state variables if they don't exist
if "file_processed" not in st.session_state:
    st.session_state.file_processed = False
if "show_tabs" not in st.session_state:
    st.session_state.show_tabs = False

# Custom Header
custom_header_html = f"""
<div style="
    position: fixed; 
    top: 0;
    left: 0;
    width: 100%; 
    display: flex;
    align-items: center; 
    justify-content: space-between; 
    padding: 0.85rem 2rem; 
    border-bottom: 1px solid var(--border-color, #e0e0e0); 
    background-color: var(--bg-card, white); 
    z-index: 999; 
">
    <div style="display: flex; align-items: center;">
        <span style="
            font-size: 1.8rem; 
            font-weight: 600;
            color: var(--brand-dark, #0A2540); 
            line-height: 1.2;
            margin-right: 0.6rem; 
        ">
            Top Plays Finder
        </span>
        <span style="
            font-size: 1.6rem; 
            color: var(--brand-primary, #4F8EF7); 
            vertical-align: middle; 
            margin-right: 0.6rem; 
        ">
            ✈️
        </span>
        <span style="
            font-size: 1.8rem; 
            font-weight: 400; 
            color: var(--text-muted, #555); 
        ">
            - Airports
        </span>
    </div>
    <a href="#" class="header-link" style='color: var(--text-muted, #6b7280); font-size:0.85rem; text-decoration: none;'>v1.0</a>
</div>
<div style="height: 68px;"></div>
"""
st.markdown(custom_header_html, unsafe_allow_html=True)

# Global CSS overrides
global_css = """
<style>
.main .block-container {
    padding-top: 1.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 100% !important;
}
header[data-testid="stHeader"] {
    display: none !important; 
}

body {
    padding-top: 0 !important; 
}

section[data-testid="stSidebar"] { 
    background: var(--brand-dark, #0A2540) !important; 
    min-width:60px !important; 
    max-width:60px !important; 
    z-index: 1000; 
}
</style>
"""
st.markdown(global_css, unsafe_allow_html=True)

# Apply custom styles (comes AFTER global_css so it can use its variables)
apply_custom_styles()

# --- Main application logic ---
render_sidebar()

with st.container():
    uploaded_file = render_upload_dropzone()
    if uploaded_file is not None:
        st.session_state.file_processed = True
        st.session_state.show_tabs = True
        st.toast("File uploaded successfully!", icon="🎉")

if st.session_state.get("show_tabs", False):
    tabs = st.tabs(["Overview", "Market Drill-down"]) 
    with tabs[0]:
        render_overview()
    with tabs[1]:
        render_market_drilldown()

# The previously misplaced session state initializations at the end of the script
# have been removed, as they are now correctly handled at the top.