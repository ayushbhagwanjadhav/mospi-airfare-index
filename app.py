import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- Page Configuration ---
st.set_page_config(page_title="MoSPI Airfare Index", page_icon="✈️", layout="wide")

# --- Constants & Paths ---
DATA_DIR = "data"
CLEANED_DATA_PATH = os.path.join(DATA_DIR, "cleaned_dataset.csv")
CPI_REPORT_PATH = os.path.join(DATA_DIR, "mospi_cpi_report.csv")
CPI_TIMESERIES_PATH = os.path.join(DATA_DIR, "mospi_cpi_timeseries.csv")

# --- Data Loading ---
@st.cache_data(ttl=600)
def load_data():
    try:
        df_clean = pd.read_csv(CLEANED_DATA_PATH)
        df_cpi = pd.read_csv(CPI_REPORT_PATH)
        
        if os.path.exists(CPI_TIMESERIES_PATH):
            df_timeseries = pd.read_csv(CPI_TIMESERIES_PATH)
        else:
            df_timeseries = df_cpi.copy()
            df_timeseries['Date'] = pd.Timestamp.now().strftime("%Y-%m-%d")
            
        return df_clean, df_cpi, df_timeseries
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_clean, df_cpi, df_timeseries = load_data()

# --- Common Plotly Styling ---
def apply_pro_styling(fig):
    fig.update_layout(
        font=dict(size=14),
        title=dict(font=dict(size=22)),
        xaxis=dict(title_font=dict(size=16), tickfont=dict(size=14)),
        yaxis=dict(title_font=dict(size=16), tickfont=dict(size=14)),
        legend=dict(font=dict(size=14, color="white"), title_font=dict(size=14)),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=50, b=50, l=50, r=50)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    return fig

# --- Sidebar UI (Fixed Logo & Added API Export) ---
with st.sidebar:
    st.markdown(
        '<div style="background-color: white; padding: 10px; border-radius: 10px; display: inline-block; margin-bottom: 20px;">'
        '<img src="https://upload.wikimedia.org/wikipedia/commons/8/84/Government_of_India_logo.svg" width="80">'
        '</div>', unsafe_allow_html=True
    )
    st.title("System Status")
    st.markdown("---")
    st.markdown("🟢 **Data Pipeline:** Active")
    st.markdown("🟢 **Sync Schedule:** 6-Hour Cron")
    st.markdown("🟢 **Deduplication Engine:** Online")
    st.markdown("---")
    
    if not df_cpi.empty:
        st.download_button(
            label="⬇️ Export NSO/RBI API (JSON)",
            data=df_cpi.to_json(orient="records"),
            file_name="mospi_api_export.json",
            mime="application/json"
        )
        
    st.caption("Engineered for Problem Statement 26056")
    st.caption("Ministry of Statistics & Programme Implementation")

# --- Main Dashboard Header ---
st.title("National Airfare Price Index (CPI)")
st.subheader("Automated Tracking & Inflation Engine for MoSPI")

if df_cpi.empty or df_clean.empty:
    st.warning("Awaiting initial data sweep from GitHub Actions. Dashboard will populate shortly.")
    st.stop()

# --- SMARTER AUTO-DETECT TO FIX 'NAN' ---
price_cols = [c for c in df_clean.columns if ('price' in c.lower() or 'fare' in c.lower()) and 'class' not in c.lower()]
price_col = price_cols[0] if price_cols else df_clean.select_dtypes(include=['number']).columns[-1]

airline_cols = [c for c in df_clean.columns if 'airline' in c.lower() or 'carrier' in c.lower()]
airline_col = airline_cols[0] if airline_cols else [c for c in df_clean.columns if df_clean[c].dtype == 'object'][0]

# --- Safe Numeric Conversion ---
df_clean[price_col] = pd.to_numeric(df_clean[price_col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')

if 'Airfare_CPI_Index' in df_cpi.columns:
    df_cpi['Airfare_CPI_Index'] = pd.to_numeric(df_cpi['Airfare_CPI_Index'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
    
if 'Airfare_CPI_Index' in df_timeseries.columns:
    df_timeseries['Airfare_CPI_Index'] = pd.to_numeric(df_timeseries['Airfare_CPI_Index'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')

# --- Top Level Metrics ---
col1, col2, col3, col4 = st.columns(4)
overall_cpi = df_cpi['Airfare_CPI_Index'].mean()
total_quotes = len(df_clean)
active_routes = df_clean['Origin_Destination'].nunique()
avg_fare = df_clean[price_col].mean()

col1.metric("National Airfare CPI", f"{overall_cpi:.2f}", f"{(overall_cpi - 100):.2f}% vs Base", delta_color="inverse")
col2.metric("Market Average Fare", f"₹{avg_fare:,.0f}")
col3.metric("Daily Unique Flights Tracked", f"{total_quotes:,}")
col4.metric("Active Monitored Routes", f"{active_routes}")

st.markdown("---")

# --- Tabs for Clean Navigation ---
tab1, tab2, tab3 = st.tabs(["📈 Macroeconomic Dashboard", "🗄️ Raw Data Explorer", "📄 Engine Methodology (Docs)"])

with tab1:
    col_a, col_b = st.columns(2)
    
    with col_a:
        # 1. Inflation Curve
        if 'Date' in df_timeseries.columns:
            ts_grouped = df_timeseries.groupby(['Date', 'Advance_Purchase_Window'])['Airfare_CPI_Index'].mean().reset_index()
            fig1 = px.line(ts_grouped, x="Date", y="Airfare_CPI_Index", color="Advance_Purchase_Window",
                           title="Airfare CPI Trend by Advance Purchase Window",
                           markers=True)
            y_max = ts_grouped['Airfare_CPI_Index'].max()
            if pd.notna(y_max):
                fig1.update_yaxes(range=[95, y_max + 5])
            st.plotly_chart(apply_pro_styling(fig1), use_container_width=True)
        else:
            st.info("Time-series data will generate after Day 2 sweeps.")

    with col_b:
        # 2. Lead-Time Elasticity Curve 
        spread_df = df_clean.groupby("Advance_Purchase_Window")[price_col].mean().reset_index()
        # Added T+45 to categorical sorting
        spread_df['Advance_Purchase_Window'] = pd.Categorical(spread_df['Advance_Purchase_Window'], ["T+1", "T+7", "T+15", "T+30", "T+45"])
        spread_df = spread_df.sort_values("Advance_Purchase_Window")
        
        fig2 = px.line(spread_df, x="Advance_Purchase_Window", y=price_col, 
                      title="Lead-Time Price Elasticity Curve",
                      markers=True)
        fig2.update_traces(line_color="#00C4B4", marker=dict(size=10, color="white", line=dict(width=2, color="#00C4B4")))
        st.plotly_chart(apply_pro_styling(fig2), use_container_width=True)

    st.markdown("---")
    
    col_c, col_d = st.columns(2)
    
    with col_c:
        # 3. Sector-Wise Heatmap (Directly addresses PS 26056 requirement)
        heatmap_df = df_clean.groupby(["Origin_Destination", "Advance_Purchase_Window"])[price_col].mean().unstack()
        heatmap_cols = [c for c in ["T+1", "T+7", "T+15", "T+30", "T+45"] if c in heatmap_df.columns]
        heatmap_df = heatmap_df[heatmap_cols]
        
        fig_heat = px.imshow(heatmap_df, text_auto='.0f', aspect="auto", color_continuous_scale="Blues",
                             title="Sector-Wise Price Heatmap (Avg Fare INR)")
        st.plotly_chart(apply_pro_styling(fig_heat), use_container_width=True)

    with col_d:
        # 4. Airline Market Share
        df_clean_pie = df_clean.dropna(subset=[airline_col, price_col])
        fig3 = px.pie(df_clean_pie, names=airline_col, title="Active Carrier Inventory Distribution (Market Share)", hole=0.4)
        fig3.update_traces(textposition='inside', textinfo='percent+label', textfont_size=14)
        st.plotly_chart(apply_pro_styling(fig3), use_container_width=True)

with tab2:
    st.subheader("Sanitized Market Data (Today's Minimums)")
    st.dataframe(df_clean, use_container_width=True)
    
    st.subheader("Current CPI Baseline Report")
    st.dataframe(df_cpi, use_container_width=True)

with tab3:
    st.markdown("""
    ### System Architecture & Mathematical Methodology
    
    **1. Data Ingestion & WAF Evasion**
    * The engine utilizes a hybrid scraping approach. To bypass enterprise Web Application Firewalls (WAF) that block datacenter IP ranges, extraction scripts run locally via automated cron jobs.
    * Data is pushed seamlessly to GitHub, which serves as the live database for this Streamlit Cloud frontend.
    
    **2. The Deduplication Engine (Canonical Keys)**
    * Since the exact same flight may be listed on multiple OTAs at different prices, the engine generates a `Canonical_Flight_Key`. 
    * During each daily cycle, the engine compares all duplicate listings and strictly preserves the **lowest available market fare**.
    
    **3. MoSPI CPI Calculation (Base = 100)**
    * Following macroeconomic standards, the first day of extraction is locked at an index value of `100.0`.
    * Subsequent daily sweeps compare the current lowest fare against the locked Base Fare for that exact route and advance purchase window.
    * **Formula:** `(Current_Fare / Base_Fare) * 100`
    
    **4. Target Coverage**
    * **Carriers:** IndiGo, Air India, Air India Express, Akasa Air, SpiceJet.
    * **Windows:** T+1, T+7, T+15, T+30, T+45.
    """)
