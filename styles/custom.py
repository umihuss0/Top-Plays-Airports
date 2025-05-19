# custom.py
import streamlit as st

def apply_custom_styles() -> None:
    """Inject global CSS styles for the Streamlit app."""
    st.markdown(
        """
        <style>
        /* ——— base fonts & colours ——— */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'); /* Added 700 weight */
        
        :root {
            color-scheme: light; /* FORCE LIGHT MODE */

            --brand-primary: #4F8EF7; /* Your main light blue */
            --brand-dark: #0A2540;    /* Dark blue for text */
            --text-muted: #64748B;    /* For less prominent text */
            --bg-main: #F6F9FC;
            --bg-card: #FFFFFF;
            --border-color: #e0e0e0; /* Consistent border color */
        }

        * { font-family: 'Inter', sans-serif; box-sizing: border-box; }
        body { 
            background: var(--bg-main); 
            color: var(--brand-dark); 
            font-size:16px; 
            line-height: 1.6; /* Improved readability */
        }

        /* ——— fix Streamlit's hidden tab-panel wrapper ——— */
        [data-baseweb="tab-panel"]{
            background:transparent !important;
            padding:0 !important;
            border-radius:0 !important;
            box-shadow:none !important;
        }

        /* ——— Summary-card row (KPI Cards) ——— */
        .summary-cards-container{
            display:flex; gap:20px; /* Slightly reduced gap */ 
            flex-wrap:wrap; margin-bottom:0;
        }
        .kpi-card{
            background: var(--bg-card); 
            border-radius: 12px; /* Slightly smaller radius for a sharper look */
            padding: 20px;      /* Slightly reduced padding */
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07), /* More subtle shadow */
                        0 2px 4px -1px rgba(0,0,0,0.04);
            min-width:180px; /* Adjusted min-width */
            height:100%;
            border: 1px solid var(--border-color); /* Subtle border for definition */
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out; /* For subtle hover */
        }
        .kpi-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.08),
                        0  4px  6px -2px rgba(0,0,0,0.05);
        }

        .summary-title   { 
            font-weight:500; /* Medium weight for title */
            font-size:0.9rem; /* Slightly smaller */
            color: var(--text-muted); 
            margin-bottom:8px; /* Adjusted margin */
        }
        .summary-value   { 
            font-weight:600; 
            font-size:1.8rem; /* Slightly adjusted size */
            color: var(--brand-dark); 
            margin-bottom:6px;  
        }
        .summary-subtitle{ 
            color: var(--brand-primary); /* Using the CSS variable */
            font-size:0.85rem; /* Slightly smaller */
            font-weight: 500;
        }

        /* ——— Section titles ——— */
        .section-title{
            margin: 2rem 0 1rem 0; /* More space above, consistent below */
            font-weight:600; 
            font-size:1.25rem; /* Slightly larger */
            color: var(--brand-dark);
            border-bottom: 1px solid var(--border-color); /* Subtle separator */
            padding-bottom: 0.5rem;
        }

        /* ——— Layout tweaks (mostly handled in app.py now for header) ——— */
        footer{display:none;}

        /* ——— Streamlit UI Element Tweaks ——— */
        /* Tabs */
        button[data-baseweb="tab"] {
            font-weight: 500 !important;
            font-size: 1rem !important;
            padding-bottom: 0.75rem !important; /* More space below text */
        }
        button[data-baseweb="tab"]:hover {
            background-color: rgba(79, 142, 247, 0.05) !important; /* Subtle hover for tabs */
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: var(--brand-primary) !important; 
        }
        
        /* Dataframe styling (optional, can be extensive) */
        .stDataFrame {
            border: 1px solid var(--border-color) !important;
            border-radius: 8px !important;
        }
        .stDataFrame th {
            background-color: var(--bg-main) !important; /* Lighter header for tables */
            color: var(--brand-dark) !important;
            font-weight: 600 !important;
        }


        /* ——— Responsive tweaks ——— */
        @media(max-width:768px){
            .summary-cards-container{flex-direction:column;}
            /* .block-container padding is handled in app.py's global_css for responsiveness */
            .section-title { font-size: 1.1rem; }
            .summary-value { font-size: 1.6rem; }
        }
        
        /* Link hover (already present, good) */
        .header-link:hover {
         color: #007bff; 
         text-decoration: underline;
        }
        
        /* Network label (already present, good) */
        span.network-label {
            color: var(--text-muted); 
            font-style: italic;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )