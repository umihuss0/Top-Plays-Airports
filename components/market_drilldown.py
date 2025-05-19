import streamlit as st
import pandas as pd
# import numpy as np # Not strictly needed if using .mean() on Series and handling empty slices

# ──────────────────────────────────────────────────────────────────────────────
# Constants for Prime Play Window logic
# ──────────────────────────────────────────────────────────────────────────────
MIN_PRIME_WINDOW_LEN = 2
MAX_PRIME_WINDOW_LEN = 4
MIN_PLAYS_PERCENT_OF_RANGE1 = 0.70 # For justifying a second window

# Constants for new scoring logic (as per "Recommended scoring tweaks")
LOW_HOUR_RELATIVE_THRESHOLD = 0.70  # Min hour < 70% of window's *density* (avg plays/hr)
WEAK_HOUR_PENALTY_PER_FRACTION = 0.20 # -20% to density score for each weak hour *fraction* of window


# ─── AIRPORT DICTIONARIES ────
AIRPORT_TO_MARKET = {
    "ATL": "Atlanta", "AUS": "Austin", "BNA": "Nashville", "BTR": "Baton Rouge",
    "BWI": "Baltimore / Washington", "CAK": "Akron / Canton", "CLE": "Cleveland",
    "CMH": "Columbus", "CRP": "Corpus Christi", "DAB": "Daytona Beach",
    "DCA": "Washington DC", "DEN": "Denver", "DTW": "Detroit", "ELP": "El Paso",
    "EWR": "New Jersey", "FAR": "Fargo", "FAT": "Fresno", "FLL": "Ft. Lauderdale",
    "GSO": "Greensboro", "HNL": "Honolulu", "HSV": "Huntsville", "IAD": "Washington DC",
    "ICT": "Wichita", "JAN": "Jackson (MS)", "JFK": "New York", "LBB": "Lubbock",
    "LGA": "New York", "MDT": "Harrisburg", "MDW": "Chicago",
    "MSP": "Minneapolis / St Paul", "MSY": "New Orleans", "OMA": "Omaha",
    "ORD": "Chicago", "PBI": "Palm Beach", "PHL": "Philadelphia", "PSC": "Tri-Cities",
    "RDU": "Raleigh-Durham", "ROA": "Roanoke–Blacksburg", "SAN": "San Diego",
    "SEA": "Seattle", "SFO": "San Francisco", "SMF": "Sacramento",
    "SWF": "Hudson Valley / NY", "TLH": "Tallahassee", "VPS": "Destin-Fort Walton",
}

AIRPORT_LONG_NAME = {
    "ATL": "Hartsfield-Jackson Atlanta International Airport",
    "AUS": "Austin-Bergstrom International Airport", "BNA": "Nashville International Airport",
    "BTR": "Baton Rouge Metropolitan Airport",
    "BWI": "Baltimore/Washington International Thurgood Marshall Airport",
    "CAK": "Akron-Canton Airport", "CLE": "Cleveland-Hopkins International Airport",
    "CMH": "John Glenn Columbus International Airport",
    "CRP": "Corpus Christi International Airport",
    "DAB": "Daytona Beach International Airport",
    "DCA": "Ronald Reagan Washington National Airport", "DEN": "Denver International Airport",
    "DTW": "Detroit Metropolitan Wayne County Airport", "ELP": "El Paso International Airport",
    "EWR": "Newark Liberty International Airport", "FAR": "Hector International Airport",
    "FAT": "Fresno Yosemite International Airport",
    "FLL": "Ft. Lauderdale-Hollywood International Airport",
    "GSO": "Piedmont Triad International Airport",
    "HNL": "Daniel K. Inouye International Airport", "HSV": "Huntsville International Airport",
    "IAD": "Washington Dulles International Airport",
    "ICT": "Wichita Dwight D. Eisenhower National Airport",
    "JAN": "Jackson-Medgar Wiley Evers International Airport",
    "JFK": "John F. Kennedy International Airport",
    "LBB": "Lubbock Preston Smith International Airport", "LGA": "LaGuardia Airport",
    "MDT": "Harrisburg International Airport", "MDW": "Chicago Midway International Airport",
    "MSP": "Minneapolis-St. Paul International Airport",
    "MSY": "Louis Armstrong New Orleans International Airport",
    "OMA": "Omaha Eppley Airfield", "ORD": "Chicago O’Hare International Airport",
    "PBI": "Palm Beach International Airport", "PHL": "Philadelphia International Airport",
    "PSC": "Tri-Cities Airport", "RDU": "Raleigh-Durham International Airport",
    "ROA": "Roanoke-Blacksburg Regional Airport", "SAN": "San Diego International Airport",
    "SEA": "Seattle-Tacoma International Airport", "SFO": "San Francisco International Airport",
    "SMF": "Sacramento International Airport", "SWF": "New York Stewart International Airport",
    "TLH": "Tallahassee International Airport", "VPS": "Destin-Fort Walton Beach Airport",
}
# ──────────────────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────────────────
def extract_airport(network_code: str | float) -> str | None:
    if pd.isna(network_code): return None
    if isinstance(network_code, str):
        stripped_full_code = network_code.strip()
        if stripped_full_code:
            parts = stripped_full_code.split("_")
            if parts: return parts[0].strip().upper()
    return None

def make_market_label(airport_code: str | None) -> str:
    if not airport_code: return "Unknown Market"
    code_to_lookup = str(airport_code).strip().upper()
    return AIRPORT_TO_MARKET.get(code_to_lookup, code_to_lookup)

def format_hour(hour_24: int | float | None) -> str:
    if pd.isna(hour_24): return "-"
    h = int(hour_24)
    if h in (0, 24): return "12am"
    if h == 12: return "12pm"
    return f"{h}am" if h < 12 else f"{h-12}pm"

def vertical_spacer(height_px: int = 24) -> None: # Renamed arg to avoid conflict with px module
    st.markdown(f"<div style='height:{height_px}px'></div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Prime Play Window Finder Logic (Incorporating new scoring and edge trimming)
# ──────────────────────────────────────────────────────────────────────────────
# In components/market_drilldown.py
# ... (constants and other helper functions remain the same) ...

# ──────────────────────────────────────────────────────────────────────────────
# Prime Play Window Finder Logic (Updated for Window #2 Trimming Debug)
# ──────────────────────────────────────────────────────────────────────────────
def find_prime_play_windows(overall_hourly_df: pd.DataFrame | None) -> list:
    # ... (Initial checks and df_filtered preparation - same as before) ...
    if overall_hourly_df is None or overall_hourly_df.empty: return []
    if 'Hour_24' not in overall_hourly_df.columns or 'Total_Plays' not in overall_hourly_df.columns: return []

    df = overall_hourly_df.copy()
    df['Hour_24'] = pd.to_numeric(df['Hour_24'], errors='coerce')
    df.dropna(subset=['Hour_24'], inplace=True)
    df['Hour_24'] = df['Hour_24'].astype(int)
    df['Total_Plays'] = pd.to_numeric(df['Total_Plays'], errors='coerce').fillna(0)
    df_filtered = df.query("7 <= Hour_24 <= 21").sort_values("Hour_24").reset_index(drop=True)
    if df_filtered.empty: return []
    
    all_windows = []
    n_hours_available = len(df_filtered)
    if n_hours_available < MIN_PRIME_WINDOW_LEN: return []

    # ... (window generation loop - same as before) ...
    for i in range(n_hours_available):
        start_hour_series = df_filtered['Hour_24'].iloc[i]
        for dur in range(MIN_PRIME_WINDOW_LEN, MAX_PRIME_WINDOW_LEN + 1):
            if i + dur > n_hours_available: break
            slice_df = df_filtered.iloc[i : i + dur]
            if slice_df['Hour_24'].iloc[-1] != start_hour_series + dur - 1: break

            total_plays = slice_df['Total_Plays'].sum()
            density = total_plays / dur if dur > 0 else 0
            weak_mask = slice_df['Total_Plays'] < LOW_HOUR_RELATIVE_THRESHOLD * density
            weak_count = weak_mask.sum()
            penalty_multiplier = 1.0 - (WEAK_HOUR_PENALTY_PER_FRACTION * (weak_count / dur)) if dur > 0 else 1.0
            rank_score = density * penalty_multiplier

            all_windows.append({
                "Window_Start": int(slice_df['Hour_24'].iloc[0]),
                "Window_End": int(slice_df['Hour_24'].iloc[-1]),
                "Window_Duration": int(dur),
                "Window_Total_Plays": int(total_plays),
                "Density": round(density, 2),
                "Weak_Count": int(weak_count),
                "Rank_Score": round(rank_score, 2)
            })
    
    if not all_windows: return []
    windows_df = pd.DataFrame(all_windows)
    if windows_df.empty: return []

    windows_df_sorted = windows_df.sort_values(
        by=["Rank_Score", "Window_Duration", "Window_Start"],
        ascending=[False, True, True]
    ).reset_index(drop=True)
    
    if windows_df_sorted.empty: return []

    # --- Helper function for trimming a window ---
    def _trim_window(start_hr, end_hr, duration_val, source_df_filtered): # Removed context_debug
        _current_start = int(start_hr)
        _current_end = int(end_hr)
        _current_duration = int(duration_val)

        # Trim weak start hour
        while _current_duration > MIN_PRIME_WINDOW_LEN:
            first_hour_plays_series = source_df_filtered[source_df_filtered['Hour_24'] == _current_start]['Total_Plays']
            if first_hour_plays_series.empty: 
                break
            first_hour_plays = first_hour_plays_series.iloc[0]

            current_window_segment_df = source_df_filtered[
                (source_df_filtered['Hour_24'] >= _current_start) & (source_df_filtered['Hour_24'] <= _current_end)
            ]
            if current_window_segment_df.empty or _current_duration == 0: 
                break 
            current_segment_total_plays = current_window_segment_df['Total_Plays'].sum()
            current_segment_density = current_segment_total_plays / _current_duration

            if first_hour_plays < LOW_HOUR_RELATIVE_THRESHOLD * current_segment_density:
                _current_start += 1
                _current_duration -= 1
            else:
                break 

        # Trim weak end hour
        while _current_duration > MIN_PRIME_WINDOW_LEN:
            last_hour_plays_series = source_df_filtered[source_df_filtered['Hour_24'] == _current_end]['Total_Plays']
            if last_hour_plays_series.empty: 
                break
            last_hour_plays = last_hour_plays_series.iloc[0]
            
            current_window_segment_df = source_df_filtered[
                (source_df_filtered['Hour_24'] >= _current_start) & (source_df_filtered['Hour_24'] <= _current_end)
            ]
            if current_window_segment_df.empty or _current_duration == 0: 
                break
            current_segment_total_plays = current_window_segment_df['Total_Plays'].sum()
            current_segment_density = current_segment_total_plays / _current_duration
            
            if last_hour_plays < LOW_HOUR_RELATIVE_THRESHOLD * current_segment_density:
                _current_end -= 1
                _current_duration -= 1
            else:
                break
        
        final_trimmed_plays_df = source_df_filtered[
            (source_df_filtered['Hour_24'] >= _current_start) & (source_df_filtered['Hour_24'] <= _current_end)
        ]
        final_trimmed_plays = final_trimmed_plays_df['Total_Plays'].sum() if not final_trimmed_plays_df.empty else 0
        
        return _current_start, _current_end, _current_duration, int(final_trimmed_plays)

    # --- Select and Trim Window #1 ---
    best_window1_original_series = windows_df_sorted.iloc[0]
    w1_trimmed_start, w1_trimmed_end, w1_trimmed_duration, w1_trimmed_plays = _trim_window(
        best_window1_original_series["Window_Start"],
        best_window1_original_series["Window_End"],
        best_window1_original_series["Window_Duration"],
        df_filtered
    )
    result = [(w1_trimmed_start, w1_trimmed_end, w1_trimmed_plays)]

    # --- Determine if a second window is justified (and trim it) ---
    range1_plays_for_comparison = w1_trimmed_plays 
    potential_range2_candidates = windows_df_sorted.iloc[1:].copy() 
    selected_window2_details = None

    for idx, candidate_w2_series in potential_range2_candidates.iterrows():
        no_overlap = (candidate_w2_series["Window_End"] < w1_trimmed_start) or \
                     (candidate_w2_series["Window_Start"] > w1_trimmed_end)
        if not no_overlap:
            continue

        initial_plays_ok = candidate_w2_series["Window_Total_Plays"] >= MIN_PLAYS_PERCENT_OF_RANGE1 * range1_plays_for_comparison
        if not initial_plays_ok:
            continue
        
        # If initial checks pass, trim this candidate Window #2
        w2_cand_trimmed_start, w2_cand_trimmed_end, w2_cand_trimmed_duration, w2_cand_trimmed_plays = _trim_window(
            candidate_w2_series["Window_Start"],
            candidate_w2_series["Window_End"],
            candidate_w2_series["Window_Duration"],
            df_filtered
        )

        if w2_cand_trimmed_duration < MIN_PRIME_WINDOW_LEN:
             continue

        final_plays_ok = w2_cand_trimmed_plays >= MIN_PLAYS_PERCENT_OF_RANGE1 * range1_plays_for_comparison
        
        if final_plays_ok:
            selected_window2_details = (w2_cand_trimmed_start, w2_cand_trimmed_end, w2_cand_trimmed_plays)
            break 

    if selected_window2_details:
        result.append(selected_window2_details)
            
    return result
# ──────────────────────────────────────────────────────────────────────────────
# Main render function
# ──────────────────────────────────────────────────────────────────────────────
def render_market_drilldown() -> None:
    raw_df: pd.DataFrame | None = st.session_state.get("data", {}).get("raw")

    if raw_df is None or raw_df.empty:
        st.info("Upload a report to see market details.")
        return

    df = raw_df.copy()
    if "Network Code" in df.columns and "Network_Code" not in df.columns:
        df = df.rename(columns={"Network Code": "Network_Code"})

    if "Network_Code" not in df.columns:
        st.error("Column 'Network Code' not found in the upload.")
        return
    
    # Ensure 'Hour_24' column exists and is numeric for grouping
    if 'Hour_24' not in df.columns:
        st.error("Column 'Hour_24' not found in the upload, which is required for hourly analysis.")
        return
    df['Hour_24'] = pd.to_numeric(df['Hour_24'], errors='coerce')
    df.dropna(subset=['Hour_24'], inplace=True) # Remove rows where Hour_24 could not be converted
    df['Hour_24'] = df['Hour_24'].astype(int)

    # Ensure '# Plays' column exists and is numeric
    if '# Plays' not in df.columns:
        st.error("Column '# Plays' not found in the upload, which is required for hourly analysis.")
        return
    df['# Plays'] = pd.to_numeric(df['# Plays'], errors='coerce').fillna(0)


    if "Airport" not in df.columns:
        df["Airport"] = df["Network_Code"].apply(extract_airport)
    else:
        df["Airport"] = df["Airport"].apply(lambda x: str(x).strip().upper() if pd.notna(x) else None)

    df["Market"] = df["Airport"].apply(make_market_label)
    st.write("") # Creates a bit of space before the first expander
    sorted_market_labels = sorted(df["Market"].dropna().unique().tolist())

    for market_group_name in sorted_market_labels:
        market_group_df = df[df["Market"] == market_group_name].copy()
        unique_airport_codes_in_group = sorted(market_group_df["Airport"].dropna().unique())

        for airport_code in unique_airport_codes_in_group:
            market_df = market_group_df[market_group_df["Airport"] == airport_code].copy()
            if market_df.empty: continue

            networks = sorted(market_df["Network_Code"].dropna().unique())
            market_name_from_dict = make_market_label(airport_code)
            long_name_from_dict = AIRPORT_LONG_NAME.get(str(airport_code) if airport_code else "", "")

            expander_main_label = f"{market_name_from_dict} ({airport_code})"
            if long_name_from_dict:
                expander_main_label += f" – {long_name_from_dict}"
            
            network_display_items = [f"[{n}]" for n in networks]
            second_line_html = f'<span class="network-label">Networks used:</span> {", ".join(network_display_items) if network_display_items else "–"}'
            
            with st.expander(expander_main_label, expanded=False):
                st.markdown(second_line_html, unsafe_allow_html=True)
                
                hourly = (
                    market_df.groupby("Hour_24", as_index=False)["# Plays"]
                    .sum()
                    .rename(columns={"# Plays": "Total_Plays"}) # This provides Total_Plays
                )
                # Ensure Total_Plays is numeric here as well, though '# Plays' conversion earlier should handle it.
                hourly["Total_Plays"] = pd.to_numeric(hourly["Total_Plays"], errors='coerce').fillna(0)
                hourly = hourly.sort_values(["Total_Plays", "Hour_24"], ascending=[False, True])

                if not hourly.empty:
                    hourly["Rank"] = hourly["Total_Plays"].rank(method="dense", ascending=False).astype(int)
                    hourly = hourly.sort_values(["Rank", "Hour_24"])
                else:
                    # Ensure `hourly` has the right columns even if empty for `find_prime_play_windows`
                    hourly = pd.DataFrame(columns=["Hour_24", "Total_Plays", "Rank"])


                # ── PRIME PLAY WINDOW(S) SECTION FOR THIS AIRPORT (NEW) ──────────────
                # Using h4 or a bolded st.markdown for subsection title
                st.markdown('**Prime Play Window(s)**', unsafe_allow_html=False) # Simple bold text
                # or st.markdown('<h4 class="subsection-title">Prime Play Window(s)</h4>', unsafe_allow_html=True)

                prime_windows_list_airport = find_prime_play_windows(hourly) # Pass the airport-specific hourly data

                if not prime_windows_list_airport:
                    st.markdown(
                        """
                        <div class="kpi-card" style="text-align: center; padding: 10px 0; margin-bottom: 10px;">
                            <span style="color: #6c757d; font-size: 0.85rem;">No qualifying hours (7 am – 9 pm)</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    # Using st.columns for horizontal layout of prime window cards.
                    prime_window_cols = st.columns(len(prime_windows_list_airport))

                    for idx, window_data in enumerate(prime_windows_list_airport):
                        start_hour, end_hour, total_plays = window_data
                        
                        range_str = f"{format_hour(start_hour)} – {format_hour(end_hour)}"
                        plays_str = f"{total_plays:,} Total Plays"

                        card_label = "Prime Window"
                        if len(prime_windows_list_airport) > 1:
                            card_label = f"Window {idx + 1}"
                        
                        with prime_window_cols[idx]:
                            # You can add a class like 'range-card' for specific styling
                            prime_window_cols[idx].markdown(
                                f"""
                                <div class="kpi-card range-card">
                                    <div class="summary-title">{card_label}</div>
                                    <div class="summary-value">{range_str}</div>
                                    <div class="summary-subtitle">{plays_str}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                vertical_spacer(15) # Space before Top Hour KPIs

                # --- Existing Top 3 KPI cards ---
                top3 = hourly.head(3)
                titles = ["Top Hour", "2nd Best", "3rd Best"]
                cols = st.columns(3)
                for idx_kpi, col_kpi in enumerate(cols):
                    with col_kpi:
                        if idx_kpi < len(top3):
                            row = top3.iloc[idx_kpi]
                            hour_val, total_plays_val = row.get("Hour_24"), row.get("Total_Plays")
                            hour_display = format_hour(hour_val)
                            plays_display = f"{int(total_plays_val):,} Total Plays" if pd.notna(total_plays_val) and total_plays_val > 0 else ("0 Total Plays" if pd.notna(total_plays_val) else "No Data")
                        else:
                            hour_display, plays_display = "-", "No Data"
                        col_kpi.markdown(f'<div class="kpi-card"><div class="summary-title">{titles[idx_kpi]}</div><div class="summary-value">{hour_display}</div><div class="summary-subtitle">{plays_display}</div></div>', unsafe_allow_html=True)
                
                vertical_spacer() # Existing spacer
                st.markdown('<h3 class="section-title">Top 10 Hours by Total Plays</h3>', unsafe_allow_html=True)

                if not hourly.empty:
                    tbl_data = hourly.head(10).copy()
                    tbl_data["Hour"] = tbl_data["Hour_24"].apply(format_hour)
                    # Rank should already be there from earlier calculation
                    if "Rank" not in tbl_data.columns: 
                        tbl_data["Rank"] = tbl_data["Total_Plays"].rank(method="dense", ascending=False).astype(int)
                    
                    tbl_data = tbl_data[["Hour", "Total_Plays", "Rank"]].rename(columns={"Total_Plays": "Total Plays"})
                    tbl_data["Total Plays"] = pd.to_numeric(tbl_data["Total Plays"], errors='coerce').fillna(0).astype(int)
                    tbl_data["Rank"] = pd.to_numeric(tbl_data["Rank"], errors='coerce').fillna(0).astype(int)
                    st.dataframe(tbl_data.style.format({"Total Plays": "{:,}", "Rank": "{}"}), use_container_width=True, hide_index=True)
                else:
                    st.caption("No hourly data to display for this airport.")