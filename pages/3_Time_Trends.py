"""
Time Trends Analysis Page - All charts respond to filters
Volume = Containers, Performance = Shipments (B/L)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared import load_data, get_monthly_trends

st.set_page_config(page_title="Time Trends", page_icon="📈", layout="wide")
st.title("📈 Time Series & Trends Analysis")

@st.cache_data
def get_data():
    possible_paths = [
        Path(__file__).parent.parent / 'data' / 'Prysmian_Shipments_Nov23_Oct25.xlsx',
        Path('data') / 'Prysmian_Shipments_Nov23_Oct25.xlsx',
    ]
    for path in possible_paths:
        if path.exists():
            return load_data(str(path))
    st.error("Data file not found")
    st.stop()

df = get_data()

# ============== SIDEBAR FILTERS ==============
st.sidebar.header("🔍 Filters")

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

# Origin filter
all_origins = sorted(df['Origin_Country_Name'].unique().tolist())
selected_origins = st.sidebar.multiselect(
    "🌍 Origin Countries",
    options=all_origins,
    default=[],
    help="Leave empty to include all origins"
)

# Destination filter
all_destinations = sorted(df['POD_Country_Name'].unique().tolist())
selected_destinations = st.sidebar.multiselect(
    "🎯 Destination Countries",
    options=all_destinations,
    default=[],
    help="Leave empty to include all destinations"
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

if selected_destinations:
    filtered_df = filtered_df[filtered_df['POD_Country_Name'].isin(selected_destinations)]

# Show filter status
if len(filtered_df) < len(df):
    st.sidebar.success(f"✅ {len(filtered_df):,} of {len(df):,} containers")
else:
    st.sidebar.info(f"📊 All {len(df):,} containers")

# ============== CALCULATE TRENDS FROM FILTERED DATA ==============
monthly = get_monthly_trends(filtered_df)
monthly['Month_Year_Dt'] = pd.to_datetime(monthly['Month_Year'])
monthly = monthly.sort_values('Month_Year_Dt')

# Carrier monthly from filtered data (using containers for volume)
carrier_monthly = filtered_df.groupby(['Month_Year', 'Carrier_Name']).agg({
    'Container_Number': 'count',
    'Bill_of_Lading': 'nunique',
    'Arrival_Delay': 'mean'
}).reset_index()
carrier_monthly.columns = ['Month', 'Carrier', 'Containers', 'Shipments', 'Avg_Delay']
carrier_monthly['Month_Dt'] = pd.to_datetime(carrier_monthly['Month'])

# Top carriers in filtered data (by containers)
top5 = filtered_df.groupby('Carrier_Name')['Container_Number'].count().nlargest(5).index.tolist()

# ============== KPIs ==============
st.markdown("### Trend Overview")
col1, col2, col3, col4 = st.columns(4)

if len(monthly) >= 6:
    recent = monthly.tail(3)['Containers'].sum()
    prior = monthly.iloc[-6:-3]['Containers'].sum() if len(monthly) >= 6 else monthly.head(3)['Containers'].sum()
    growth = ((recent - prior) / prior * 100) if prior > 0 else 0
    col1.metric("Recent Growth (3m)", f"{growth:+.1f}%", f"{int(recent - prior):+,} containers")
else:
    col1.metric("Total Containers", f"{monthly['Containers'].sum():,}")

if len(monthly) >= 4:
    recent_delay = monthly.tail(2)['Avg_Delay'].mean()
    prior_delay = monthly.iloc[-4:-2]['Avg_Delay'].mean()
    col2.metric("Delay Trend", f"{recent_delay:.1f}d", f"{recent_delay - prior_delay:+.1f}d", delta_color="inverse")
else:
    col2.metric("Avg Delay", f"{monthly['Avg_Delay'].mean():.1f}d")

if len(monthly) > 0:
    peak_idx = monthly['Containers'].idxmax()
    peak = monthly.loc[peak_idx]
    col3.metric("Peak Month", str(peak['Month_Year']), f"{int(peak['Containers']):,} containers")
    
    best_idx = monthly['Avg_Delay'].idxmin()
    best = monthly.loc[best_idx]
    col4.metric("Best Performance", str(best['Month_Year']), f"{best['Avg_Delay']:.1f}d delay")

st.markdown("---")

# ============== TABS ==============
tab1, tab2, tab3, tab4 = st.tabs(["📊 Volume Trends", "⏱️ Delay Trends", "🏢 Carrier Evolution", "📅 Seasonality"])

with tab1:
    st.markdown("#### Monthly Container Volume")
    st.caption("*Volume measured in containers*")
    
    if len(monthly) > 0:
        monthly['MA3'] = monthly['Containers'].rolling(3, min_periods=1).mean()
        
        fig = make_subplots(specs=[[{"secondary_y": False}]])
        fig.add_trace(go.Bar(x=monthly['Month_Year_Dt'], y=monthly['Containers'], name='Containers',
                             marker_color='#1E3A5F', opacity=0.7))
        fig.add_trace(go.Scatter(x=monthly['Month_Year_Dt'], y=monthly['MA3'], name='3M Moving Avg',
                                 line=dict(color='#E74C3C', width=3)))
        fig.update_layout(height=450, legend=dict(orientation="h", y=1.02),
                          xaxis_title="Month", yaxis_title="Containers")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data for selected filters")
    
    st.markdown("#### Carrier Mix Over Time (Containers)")
    if len(carrier_monthly) > 0 and len(top5) > 0:
        carrier_top = carrier_monthly[carrier_monthly['Carrier'].isin(top5)]
        fig = px.area(carrier_top, x='Month_Dt', y='Containers', color='Carrier',
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(height=400, xaxis_title="Month", yaxis_title="Containers")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No carrier data for selected filters")

with tab2:
    st.markdown("#### Monthly Average Delay")
    st.caption("*Performance metrics based on shipments (B/L)*")
    
    if len(monthly) > 0:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=monthly['Month_Year_Dt'], y=monthly['Avg_Delay'], name='Avg Delay',
                                 line=dict(color='#E74C3C', width=2), mode='lines+markers'), secondary_y=False)
        fig.add_trace(go.Scatter(x=monthly['Month_Year_Dt'], y=monthly['Late_Rate'], name='Late %',
                                 line=dict(color='#FFC107', width=2, dash='dash')), secondary_y=True)
        fig.add_hline(y=0, line_dash="dash", line_color="green", secondary_y=False)
        fig.update_yaxes(title_text="Avg Delay (days)", secondary_y=False)
        fig.update_yaxes(title_text="Late Rate (%)", secondary_y=True)
        fig.update_layout(height=450, legend=dict(orientation="h", y=1.02))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data for selected filters")
    
    st.markdown("#### Delay Categories Over Time")
    if len(filtered_df) > 0:
        delay_monthly = filtered_df.groupby(['Month_Year', 'Delay_Category']).size().reset_index(name='Count')
        delay_monthly['Month_Dt'] = pd.to_datetime(delay_monthly['Month_Year'])
        delay_monthly = delay_monthly.sort_values('Month_Dt')
        
        fig = px.bar(delay_monthly, x='Month_Dt', y='Count', color='Delay_Category', barmode='stack',
                     color_discrete_map={'On Time/Early': '#28a745', '1-3 Days Late': '#ffc107',
                                         '4-7 Days Late': '#fd7e14', '7+ Days Late': '#dc3545'})
        fig.update_layout(height=400, xaxis_title="Month")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("#### Carrier Performance Evolution")
    
    # Let user pick from carriers in filtered data
    available_carriers = sorted(filtered_df['Carrier_Name'].unique().tolist())
    default_carriers = top5[:3] if len(top5) >= 3 else top5
    
    carriers = st.multiselect("Select Carriers to Compare",
        available_carriers, default=default_carriers)
    
    if carriers and len(carrier_monthly) > 0:
        c_trend = carrier_monthly[carrier_monthly['Carrier'].isin(carriers)]
        
        if len(c_trend) > 0:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### Container Volume Trend")
                fig = px.line(c_trend, x='Month_Dt', y='Containers', color='Carrier', markers=True)
                fig.update_layout(height=400, xaxis_title="Month")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("##### Delay Trend")
                fig = px.line(c_trend, x='Month_Dt', y='Avg_Delay', color='Carrier', markers=True)
                fig.add_hline(y=0, line_dash="dash", line_color="green")
                fig.update_layout(height=400, xaxis_title="Month")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data for selected carriers")
    else:
        st.info("Select at least one carrier to view trends")

with tab4:
    st.markdown("#### Seasonality Analysis")
    
    if len(filtered_df) > 0:
        df_s = filtered_df.copy()
        df_s['Month_Num'] = df_s['Departure_Date'].dt.month
        df_s['Quarter'] = df_s['Departure_Date'].dt.quarter
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Average Container Volume by Month")
            month_agg = df_s.groupby('Month_Num').agg({
                'Container_Number': 'count',
                'Bill_of_Lading': 'nunique',
                'Arrival_Delay': 'mean'
            }).reset_index()
            month_agg.columns = ['Month', 'Containers', 'Shipments', 'Avg_Delay']
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            month_agg['Name'] = month_agg['Month'].apply(
                lambda x: month_names[int(x)-1] if pd.notna(x) and 1 <= x <= 12 else 'Unknown')
            
            fig = px.bar(month_agg, x='Name', y='Containers', color='Avg_Delay',
                         color_continuous_scale='RdYlGn_r', text='Containers')
            fig.update_traces(textposition='outside')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("##### Performance by Quarter")
            q_agg = df_s.groupby('Quarter').agg({
                'Container_Number': 'count',
                'Bill_of_Lading': 'nunique',
                'Arrival_Delay': 'mean'
            }).reset_index()
            q_agg.columns = ['Quarter', 'Containers', 'Shipments', 'Avg_Delay']
            q_agg['Q'] = 'Q' + q_agg['Quarter'].astype(int).astype(str)
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=q_agg['Q'], y=q_agg['Containers'], name='Containers',
                                 marker_color='#1E3A5F'), secondary_y=False)
            fig.add_trace(go.Scatter(x=q_agg['Q'], y=q_agg['Avg_Delay'], name='Avg Delay',
                                     line=dict(color='#E74C3C', width=3), mode='lines+markers'), secondary_y=True)
            fig.update_yaxes(title_text="Containers", secondary_y=False)
            fig.update_yaxes(title_text="Avg Delay (days)", secondary_y=True)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data for selected filters")
