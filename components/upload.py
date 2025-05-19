import streamlit as st
import pandas as pd
from utils.data_processing import process_file

def render_upload_dropzone():
    """Render a custom styled file upload dropzone"""
    st.markdown(
        """
        <div class="upload-container" style="text-align:center; margin-bottom:1rem;">
            <div class="upload-icon" style="margin-bottom:0.5rem;">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#4F8EF7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-cloud-upload">
                    <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"></path>
                    <path d="M12 12v9"></path>
                    <path d="m16 16-4-4-4 4"></path>
                </svg>
            </div>
            <div class="upload-text" style="font-size:1.1rem; font-weight:600;">Drag and drop your file below or click to browse</div>
            <div class="upload-subtext" style="font-size:0.95rem; color:#555;">Accepts .xlsx and .csv files</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    # Place the uploader directly (not hidden)
    uploaded_file = st.file_uploader(
        "Upload Excel or CSV",
        type=["xlsx", "csv"],
        label_visibility="visible"
    )
    st.caption("Accepted file types: .xlsx, .csv. Drag-and-drop or click above.")
    
    # --- ADD YOUR NEW INSTRUCTIONS HERE ---
    st.markdown("**Directions:** Upload Hourly report sourced from PowerBI reporting.")
    # --- END OF ADDED CODE ---
    
    # If file is uploaded, process it
    if uploaded_file is not None and not st.session_state.get("file_processed", False):
        data = process_file(uploaded_file)
        st.session_state.data = data
        
        # Add download button for processed report
        report_bytes = data.get('report_bytes', b'')
        today_str = pd.Timestamp.now().strftime('%Y-%m-%d')
        st.download_button(
            label="Download Total Plays Report",
            data=report_bytes,
            file_name=f"PlayRate_Report_{today_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            on_click=lambda: st.toast("Report ready ✓", icon="✅")
        )
    
    return uploaded_file