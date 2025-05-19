import streamlit as st
# from components.data_table import render_data_table # Assuming this is in your project
import plotly.express as px
import pandas as pd

# Dummy render_data_table if not available, for testing standalone
if 'render_data_table' not in globals():
    def render_data_table(df: pd.DataFrame):
        st.dataframe(df, use_container_width=True, hide_index=True)

# ──────────────────────────────────────────────────────────────────────────────
# Constants for Prime Play Window logic
# ──────────────────────────────────────────────────────────────────────────────
MIN_PRIME_WINDOW_LEN = 2
MAX_PRIME_WINDOW_LEN = 4
MIN_PLAYS_PERCENT_OF_RANGE1 = 0.70 # For justifying a second window

# Constants for new scoring logic (from market_drilldown.py)
LOW_HOUR_RELATIVE_THRESHOLD = 0.70  # Min hour < 70% of window's *density* (avg plays/hr)
WEAK_HOUR_PENALTY_PER_FRACTION = 0.20 # -20% to density score for each weak hour *fraction* of window

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def vertical_spacer(height_px: int = 24) -> None:
    st.markdown(f"<div style='height:{height_px}px'></div>", unsafe_allow_html=True)

def format_hour(hour_24: int) -> str: # Assuming hour_24 will be an int here
    hour = int(hour_24)
    if hour in (0, 24):
        return "12am"
    if hour == 12:
        return "12pm"
    return f"{hour}am" if hour < 12 else f"{hour - 12}pm"

# ──────────────────────────────────────────────────────────────────────────────
# Prime Play Window Finder Logic (Incorporated from market_drilldown.py)
# ──────────────────────────────────────────────────────────────────────────────
def find_prime_play_windows(overall_hourly_df: pd.DataFrame | None) -> list:
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

    for i in range(n_hours_available):
        start_hour_val = df_filtered['Hour_24'].iloc[i] # Renamed from start_hour_series for clarity
        for dur in range(MIN_PRIME_WINDOW_LEN, MAX_PRIME_WINDOW_LEN + 1):
            if i + dur > n_hours_available: break
            slice_df = df_filtered.iloc[i : i + dur]
            # Check for contiguous hours (e.g. if source data could miss an hour like 8am)
            if slice_df['Hour_24'].iloc[-1] != start_hour_val + dur - 1: break 

            total_plays = slice_df['Total_Plays'].sum()
            density = total_plays / dur if dur > 0 else 0
            # Weak hour definition: an hour's plays < threshold * window's average plays per hour (density)
            weak_mask = slice_df['Total_Plays'] < LOW_HOUR_RELATIVE_THRESHOLD * density
            weak_count = weak_mask.sum()
            # Penalty: for each weak hour, reduce score proportionally
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

    # Sort by Rank_Score (desc), then by duration (asc for tie-break), then start hour (asc)
    windows_df_sorted = windows_df.sort_values(
        by=["Rank_Score", "Window_Duration", "Window_Start"],
        ascending=[False, True, True]
    ).reset_index(drop=True)
    
    if windows_df_sorted.empty: return []

    # --- Helper function for trimming a window ---
    def _trim_window(start_hr, end_hr, duration_val, source_df_filtered):
        _current_start = int(start_hr)
        _current_end = int(end_hr)
        _current_duration = int(duration_val)

        # Trim weak start hour
        while _current_duration > MIN_PRIME_WINDOW_LEN:
            first_hour_plays_series = source_df_filtered[source_df_filtered['Hour_24'] == _current_start]['Total_Plays']
            if first_hour_plays_series.empty: break 
            first_hour_plays = first_hour_plays_series.iloc[0]

            current_window_segment_df = source_df_filtered[
                (source_df_filtered['Hour_24'] >= _current_start) & (source_df_filtered['Hour_24'] <= _current_end)
            ]
            if current_window_segment_df.empty or _current_duration == 0: break
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
            if last_hour_plays_series.empty: break
            last_hour_plays = last_hour_plays_series.iloc[0]
            
            current_window_segment_df = source_df_filtered[
                (source_df_filtered['Hour_24'] >= _current_start) & (source_df_filtered['Hour_24'] <= _current_end)
            ]
            if current_window_segment_df.empty or _current_duration == 0: break
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
        df_filtered # Pass the filtered dataframe for trimming lookups
    )
    
    # A window must meet minimum length after trimming to be valid.
    # _trim_window ensures duration >= MIN_PRIME_WINDOW_LEN if it started >= MIN_PRIME_WINDOW_LEN.
    # If somehow the best window becomes too short (e.g. if MIN_PRIME_WINDOW_LEN was 1 and it got trimmed to 0)
    # this check would be useful. Given current constraints, it's mostly a safeguard.
    if w1_trimmed_duration < MIN_PRIME_WINDOW_LEN:
        return [] # No valid primary window found
        
    result = [(w1_trimmed_start, w1_trimmed_end, w1_trimmed_plays)]

    # --- Determine if a second window is justified (and trim it) ---
    range1_plays_for_comparison = w1_trimmed_plays 
    potential_range2_candidates = windows_df_sorted.iloc[1:].copy() 
    selected_window2_details = None

    for idx, candidate_w2_series in potential_range2_candidates.iterrows():
        # Check for overlap with the *trimmed* Window 1
        no_overlap = (candidate_w2_series["Window_End"] < w1_trimmed_start) or \
                     (candidate_w2_series["Window_Start"] > w1_trimmed_end)
        if not no_overlap:
            continue

        # Initial check: candidate's *original* plays vs. W1's *trimmed* plays
        initial_plays_ok = candidate_w2_series["Window_Total_Plays"] >= MIN_PLAYS_PERCENT_OF_RANGE1 * range1_plays_for_comparison
        if not initial_plays_ok:
            continue
        
        # If initial checks pass, trim this candidate Window #2
        w2_cand_trimmed_start, w2_cand_trimmed_end, w2_cand_trimmed_duration, w2_cand_trimmed_plays = _trim_window(
            candidate_w2_series["Window_Start"],
            candidate_w2_series["Window_End"],
            candidate_w2_series["Window_Duration"],
            df_filtered # Pass the filtered dataframe for trimming lookups
        )

        # Candidate W2 must still be valid (duration) after its own trimming
        if w2_cand_trimmed_duration < MIN_PRIME_WINDOW_LEN:
             continue # This candidate is no longer valid after trimming

        # Final check: candidate's *trimmed* plays vs. W1's *trimmed* plays
        final_plays_ok = w2_cand_trimmed_plays >= MIN_PLAYS_PERCENT_OF_RANGE1 * range1_plays_for_comparison
        
        if final_plays_ok:
            # Crucial: Re-check for overlap *after both windows have been trimmed*
            # This is because W2 candidate might have shifted due to its own trimming.
            still_no_overlap_after_w2_trim = (w2_cand_trimmed_end < w1_trimmed_start) or \
                                             (w2_cand_trimmed_start > w1_trimmed_end)
            if still_no_overlap_after_w2_trim:
                selected_window2_details = (w2_cand_trimmed_start, w2_cand_trimmed_end, w2_cand_trimmed_plays)
                break # Found a suitable, trimmed W2

    if selected_window2_details:
        result.append(selected_window2_details)
            
    return result


def render_overview_chart(overall_hourly: pd.DataFrame | None) -> None:
    if overall_hourly is None or overall_hourly.empty:
        st.info("No data to display.")
        return

    df = overall_hourly.copy()
    df["Hour_24"] = df["Hour_24"].astype(int)
    df["Hour"] = df["Hour_24"].apply(format_hour)
    df = df.sort_values("Hour_24")

    fig = px.bar(
        df,
        x="Hour",
        y="Total_Plays",
        color="Total_Plays",
        color_continuous_scale=["#E0E7FF", "#4F8EF7"],
        template="plotly_white",
    )
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=14),
        coloraxis_showscale=False,
        xaxis=dict(
            type='category',
            tickmode="array",
            tickvals=list(df["Hour"]),
            ticktext=list(df["Hour"]),
        ),
    )
    st.plotly_chart(fig, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# Main view (Corrected)
# ──────────────────────────────────────────────────────────────────────────────
def render_overview() -> None:
    """Overview tab: Prime Play Windows → KPI cards → top-10 table → bar chart."""
    data = st.session_state.get("data", {})
    overall_hourly = data.get("overall_hourly") # This should be a DataFrame with 'Hour_24' and 'Total_Plays'

    # ── PRIME PLAY WINDOW(S) SECTION (NEW) ──────────────────────────────────
    st.markdown('<h3 class="section-title">Prime Play Window(s)</h3>', unsafe_allow_html=True)
    
    # Ensure overall_hourly is prepared if it's None or empty, or lacks required columns
    # The find_prime_play_windows function now handles this internally, but good to be aware.
    prime_windows_list = find_prime_play_windows(overall_hourly)

    if not prime_windows_list:
        st.markdown(
            """
            <div class="kpi-card" style="text-align: center; padding: 20px 0;">
                <span style="color: #6c757d; font-size: 0.9rem;">No qualifying hours (7 am – 9 pm) or valid windows found.</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown('<div class="summary-cards-container">', unsafe_allow_html=True)
        cols = st.columns(len(prime_windows_list))

        for idx, window_data in enumerate(prime_windows_list):
            start_hour, end_hour, total_plays = window_data
            
            range_str = f"{format_hour(start_hour)} – {format_hour(end_hour)}"
            plays_str = f"{total_plays:,} Total Plays"

            card_label = "Prime Window"
            if len(prime_windows_list) > 1:
                card_label = f"Window {idx + 1}"
            
            with cols[idx]:
                cols[idx].markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="summary-title">{card_label}</div>
                        <div class="summary-value">{range_str}</div>
                        <div class="summary-subtitle">{plays_str}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    vertical_spacer()

    # ── 1. KPI SUMMARY CARDS (Existing) ─────────────────────────────────────
    st.markdown('<div class="summary-cards-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    card_titles = ["Top Hour", "2nd Best", "3rd Best"]
    rows_for_kpi = []
    # For KPI cards, we still need 'Rank' if we use nsmallest.
    # If 'Rank' is not in overall_hourly, we might need to calculate it or sort by Total_Plays.
    # Assuming overall_hourly is pre-processed to include 'Rank' for this section.
    # If not, this part might need adjustment or rely on sorting by 'Total_Plays'.
    if overall_hourly is not None and not overall_hourly.empty and 'Total_Plays' in overall_hourly.columns:
        # Create Rank if not present, for compatibility with existing KPI logic
        # This 'Rank' is based purely on Total_Plays, not the window Rank_Score.
        temp_hourly_for_kpi = overall_hourly.copy()
        if 'Rank' not in temp_hourly_for_kpi.columns:
            temp_hourly_for_kpi['Rank'] = temp_hourly_for_kpi['Total_Plays'].rank(method="dense", ascending=False).astype(int)
        
        # Filter for displayable hours if necessary (e.g. 7-21), though Top Hour KPI might be outside this
        # For simplicity, using all hours for Top Hour KPIs as per original likely intent.
        # Ensure Hour_24 is int for format_hour
        temp_hourly_for_kpi['Hour_24'] = pd.to_numeric(temp_hourly_for_kpi['Hour_24'], errors='coerce').dropna().astype(int)

        if 'Rank' in temp_hourly_for_kpi.columns and pd.api.types.is_numeric_dtype(temp_hourly_for_kpi['Rank']):
            if 'Hour_24' in temp_hourly_for_kpi.columns and 'Total_Plays' in temp_hourly_for_kpi.columns:
                top3 = temp_hourly_for_kpi.sort_values(by=["Rank", "Hour_24"], ascending=[True,True]).head(3)
                rows_for_kpi = top3.to_dict("records")
    
    for idx, col in enumerate([col1, col2, col3]):
        with col:
            if idx < len(rows_for_kpi):
                hour_val = rows_for_kpi[idx]["Hour_24"]
                totalplays_val = rows_for_kpi[idx]["Total_Plays"]
                
                hour_display = format_hour(int(hour_val)) # Ensure int for format_hour
                totalplays_display = f"{int(totalplays_val):,} Total Plays"
            else:
                hour_display, totalplays_display = "-", "No Data"

            col.markdown(
                f"""
                <div class="kpi-card">
                    <div class="summary-title">{card_titles[idx]}</div>
                    <div class="summary-value">{hour_display}</div>
                    <div class="summary-subtitle">{totalplays_display}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

    # ── 2. TOP-10 TABLE (Existing) ──────────────────────────────────────────
    vertical_spacer()
    st.markdown(
        '<h3 class="section-title">Top 10 Hours by Total Plays</h3>',
        unsafe_allow_html=True,
    )

    if overall_hourly is not None and not overall_hourly.empty and 'Total_Plays' in overall_hourly.columns:
        # Similar to KPI cards, ensure 'Rank' and 'Hour_24' are ready for the table.
        temp_hourly_for_table = overall_hourly.copy()
        if 'Rank' not in temp_hourly_for_table.columns:
             temp_hourly_for_table['Rank'] = temp_hourly_for_table['Total_Plays'].rank(method="dense", ascending=False).astype(int)
        
        temp_hourly_for_table['Hour_24'] = pd.to_numeric(temp_hourly_for_table['Hour_24'], errors='coerce').dropna().astype(int)

        if ('Rank' in temp_hourly_for_table.columns and 
            pd.api.types.is_numeric_dtype(temp_hourly_for_table['Rank']) and
            'Hour_24' in temp_hourly_for_table.columns and 
            'Total_Plays' in temp_hourly_for_table.columns):
            
            top10_df = (
                temp_hourly_for_table.sort_values(by=["Rank", "Hour_24"], ascending=[True,True]).head(10)
                .assign(
                    Hour=lambda df_: df_["Hour_24"].astype(int).apply(format_hour),
                    # Total Plays formatting changed to ensure it's int then formatted
                    **{"Total Plays": lambda df_: df_["Total_Plays"].astype(float).astype(int).map(lambda x: f"{x:,}")},
                )[["Hour", "Total Plays", "Rank"]]
            )
            render_data_table(top10_df)
        else:
            st.caption("Required columns for Top 10 table are missing or not numeric.")
            render_data_table(pd.DataFrame(columns=["Hour", "Total Plays", "Rank"]))
    else:
        st.caption("No overall hourly data to display for Top 10 table.")
        render_data_table(pd.DataFrame(columns=["Hour", "Total Plays", "Rank"]))

    # ── 3. BAR CHART (Existing) ─────────────────────────────────────────────
    vertical_spacer()
    st.markdown(
        '<h3 class="section-title">Total Plays by Hour (All Inventory)</h3>',
        unsafe_allow_html=True,
    )
    render_overview_chart(overall_hourly)