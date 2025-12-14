"""
Prysmian Ocean Logistics Analytics Dashboard
Main application - Executive Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from shared import load_data, calculate_kpis, get_carrier_stats

# Page config
st.set_page_config(
    page_title="Executive Dashboard | Prysmian Logistics",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 700; color: #1E3A5F; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #666; margin-bottom: 2rem; }
    /* Hide default page name and show custom name */
    [data-testid="stSidebarNav"] li:first-child a span { visibility: hidden; position: relative; }
    [data-testid="stSidebarNav"] li:first-child a span::after { 
        content: "Executive Dashboard"; visibility: visible; position: absolute; left: 0; 
    }
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def get_data():
    possible_paths = [
        Path(__file__).parent / 'data' / 'Prysmian_Shipments_Nov23_Oct25.xlsx',
        Path('data') / 'Prysmian_Shipments_Nov23_Oct25.xlsx',
    ]
    for path in possible_paths:
        if path.exists():
            return load_data(str(path))
    st.error("Data file not found. Please ensure data/Prysmian_Shipments_Nov23_Oct25.xlsx exists.")
    st.stop()

df = get_data()

# ============== SIDEBAR FILTERS ==============
st.sidebar.title("🚢 Prysmian Analytics")
st.sidebar.markdown("### 🔍 Global Filters")

# Date filter
if 'Departure_Date' in df.columns and df['Departure_Date'].notna().any():
    min_date = df['Departure_Date'].min().date()
    max_date = df['Departure_Date'].max().date()
    date_range = st.sidebar.date_input(
        "📅 Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    date_range = None

# Carrier filter
all_carriers = sorted(df['Carrier_Name'].unique().tolist())
selected_carriers = st.sidebar.multiselect(
    "🏢 Carriers",
    options=all_carriers,
    default=[],
    help="Leave empty to include all carriers"
)

# Origin country filter
all_origins = sorted(df['Origin_Country_Name'].unique().tolist())
selected_origins = st.sidebar.multiselect(
    "🌍 Origin Countries",
    options=all_origins,
    default=[],
    help="Leave empty to include all origins"
)

st.sidebar.markdown("---")

# ============== APPLY FILTERS ==============
filtered_df = df.copy()

if date_range and len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df['Departure_Date'].dt.date >= date_range[0]) &
        (filtered_df['Departure_Date'].dt.date <= date_range[1])
    ]

if selected_carriers:
    filtered_df = filtered_df[filtered_df['Carrier_Name'].isin(selected_carriers)]

if selected_origins:
    filtered_df = filtered_df[filtered_df['Origin_Country_Name'].isin(selected_origins)]

# Show filter status
total_records = len(df)
filtered_records = len(filtered_df)
if filtered_records < total_records:
    st.sidebar.success(f"✅ Showing {filtered_records:,} of {total_records:,} containers")
else:
    st.sidebar.info(f"📊 Showing all {total_records:,} containers")

# ============== CALCULATE METRICS ==============
kpis = calculate_kpis(filtered_df)
carrier_stats = get_carrier_stats(filtered_df)

# ============== HEADER ==============
st.markdown('<p class="main-header">🚢 Prysmian Ocean Logistics Analytics</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Executive Dashboard | Container Shipment Performance (Nov 2023 - Oct 2025)</p>', unsafe_allow_html=True)

# Filter indicator
if selected_carriers or selected_origins:
    filter_parts = []
    if selected_carriers:
        filter_parts.append(f"{len(selected_carriers)} carriers")
    if selected_origins:
        filter_parts.append(f"{len(selected_origins)} origins")
    st.info(f"🔍 **Filtered view**: {', '.join(filter_parts)} | {kpis['total_shipments']:,} shipments ({kpis['total_containers']:,} containers)")

# ============== KPI ROW ==============
st.markdown("### Key Performance Indicators")
col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Shipments (B/L)", f"{kpis['total_shipments']:,}")
col2.metric("Containers", f"{kpis['total_containers']:,}")
col3.metric("On-Time Rate", f"{kpis['on_time_rate']:.1f}%")
col4.metric("Avg Delay", f"{kpis['avg_delay']:.1f} days")
col5.metric("Severe Late (>7d)", f"{kpis['severe_late_rate']:.1f}%")
col6.metric("Carriers", f"{kpis['total_carriers']}")

st.markdown("---")

# ============== CHARTS ==============
# NOTE: Volume = Containers, Performance = Shipments (B/L)
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.markdown("### Top Carriers by Container Volume")
    chart_data = carrier_stats.sort_values('Containers', ascending=False).head(12)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=chart_data['Carrier_Name'],
        y=chart_data['Containers'],
        marker_color='#1E3A5F',
        text=chart_data['Containers'],
        textposition='outside'
    ))
    fig.update_layout(height=400, xaxis_title="Carrier", yaxis_title="Containers",
                      margin=dict(t=20, b=80))
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown("### Market Share (by Containers)")
    top5 = carrier_stats.sort_values('Containers', ascending=False).head(5).copy()
    others = carrier_stats.sort_values('Containers', ascending=False).iloc[5:]['Containers'].sum() if len(carrier_stats) > 5 else 0
    
    if others > 0:
        pie_data = pd.concat([top5[['Carrier_Name', 'Containers']],
                              pd.DataFrame({'Carrier_Name': ['Others'], 'Containers': [others]})])
    else:
        pie_data = top5[['Carrier_Name', 'Containers']]
    
    fig = px.pie(pie_data, values='Containers', names='Carrier_Name',
                 color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4)
    fig.update_traces(textposition='outside', textinfo='percent+label')
    fig.update_layout(height=400, showlegend=False, margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Delay Analysis (Performance = Shipments)
col_d1, col_d2 = st.columns(2)

with col_d1:
    st.markdown("### Delay Distribution")
    delay_dist = filtered_df['Delay_Category'].value_counts().reset_index()
    delay_dist.columns = ['Category', 'Count']
    
    color_map = {'On Time/Early': '#28a745', '1-3 Days Late': '#ffc107',
                 '4-7 Days Late': '#fd7e14', '7+ Days Late': '#dc3545'}
    
    fig = px.bar(delay_dist, x='Category', y='Count', color='Category',
                 color_discrete_map=color_map, text='Count')
    fig.update_layout(height=350, showlegend=False)
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

with col_d2:
    st.markdown("### Carrier Performance Quadrant")
    carrier_perf = carrier_stats.copy()
    carrier_perf['Bubble_Size'] = carrier_perf['Containers'] / carrier_perf['Containers'].max() * 50 + 10
    
    fig = px.scatter(carrier_perf, x='Containers', y='On_Time_Rate',
                     size='Bubble_Size', color='Avg_Delay', color_continuous_scale='RdYlGn_r',
                     hover_name='Carrier_Name', text='Carrier_Name',
                     hover_data={'Shipments': True, 'Containers': True, 'Avg_Delay': ':.1f'})
    fig.update_traces(textposition='top center', textfont_size=9)
    fig.add_hline(y=50, line_dash="dash", line_color="gray")
    fig.update_layout(height=350, xaxis_title="Volume (Containers)", yaxis_title="On-Time Rate (%)")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Quick Insights
st.markdown("### Quick Insights")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 🏆 Best Performer")
    qualified = carrier_stats[carrier_stats['Shipments'] >= 20]
    if len(qualified) > 0:
        best = qualified.loc[qualified['On_Time_Rate'].idxmax()]
        st.success(f"**{best['Carrier_Name']}**\n\n"
                   f"- On-Time: **{best['On_Time_Rate']:.1f}%**\n"
                   f"- Avg Delay: {best['Avg_Delay']:.1f} days\n"
                   f"- Containers: {int(best['Containers']):,}")
    else:
        st.warning("No carriers with 20+ shipments in filtered data")

with col2:
    st.markdown("#### ⚠️ Highest Risk")
    if len(carrier_stats) > 0:
        worst = carrier_stats.loc[carrier_stats['Severe_Late_Rate'].idxmax()]
        st.error(f"**{worst['Carrier_Name']}**\n\n"
                 f"- Severe Late: **{worst['Severe_Late_Rate']:.1f}%**\n"
                 f"- Avg Delay: {worst['Avg_Delay']:.1f} days\n"
                 f"- Containers: {int(worst['Containers']):,}")
    else:
        st.info("No data available")

with col3:
    st.markdown("#### 📊 Volume Leader")
    if len(carrier_stats) > 0:
        leader = carrier_stats.sort_values('Containers', ascending=False).iloc[0]
        container_share = leader['Containers'] / carrier_stats['Containers'].sum() * 100
        st.info(f"**{leader['Carrier_Name']}**\n\n"
                f"- Market Share: **{container_share:.1f}%**\n"
                f"- On-Time: {leader['On_Time_Rate']:.1f}%\n"
                f"- Containers: {int(leader['Containers']):,}")
    else:
        st.info("No data available")

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    Prysmian Ocean Logistics Analytics | GEMOS Challenge 2025<br>
    <small>Volume = Containers | Performance metrics based on unique Bill of Lading | Use sidebar filters to explore data</small>
</div>
""", unsafe_allow_html=True)
