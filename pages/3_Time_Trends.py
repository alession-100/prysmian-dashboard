"""
Time Trends Analysis Page
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

# Monthly trends
monthly = get_monthly_trends(df)
monthly['Month_Year_Dt'] = pd.to_datetime(monthly['Month_Year'])
monthly = monthly.sort_values('Month_Year_Dt')

# Carrier monthly
carrier_monthly = df.groupby(['Month_Year', 'Carrier_Name']).agg({
    'Bill_of_Lading': 'nunique', 'Arrival_Delay': 'mean'
}).reset_index()
carrier_monthly.columns = ['Month', 'Carrier', 'Shipments', 'Avg_Delay']
carrier_monthly['Month_Dt'] = pd.to_datetime(carrier_monthly['Month'])

top5 = df['Carrier_Name'].value_counts().head(5).index.tolist()

# KPIs
st.markdown("### Trend Overview")
col1, col2, col3, col4 = st.columns(4)

if len(monthly) >= 12:
    recent = monthly.tail(6)['Shipments'].sum()
    prior = monthly.iloc[-12:-6]['Shipments'].sum()
    growth = ((recent - prior) / prior * 100) if prior > 0 else 0
else:
    recent = monthly.tail(max(1, len(monthly)//2))['Shipments'].sum()
    prior = monthly.head(max(1, len(monthly)//2))['Shipments'].sum()
    growth = ((recent - prior) / prior * 100) if prior > 0 else 0

col1.metric("Period Growth", f"{growth:+.1f}%", f"{int(recent - prior):+,} shipments")

if len(monthly) >= 6:
    recent_delay = monthly.tail(3)['Avg_Delay'].mean()
    prior_delay = monthly.iloc[-6:-3]['Avg_Delay'].mean()
else:
    recent_delay = monthly.tail(max(1, len(monthly)//2))['Avg_Delay'].mean()
    prior_delay = monthly.head(max(1, len(monthly)//2))['Avg_Delay'].mean()
    
col2.metric("Delay Trend", f"{recent_delay:.1f}d", f"{recent_delay - prior_delay:+.1f}d", delta_color="inverse")

peak_idx = monthly['Shipments'].idxmax()
peak = monthly.loc[peak_idx]
col3.metric("Peak Month", str(peak['Month_Year']), f"{int(peak['Shipments']):,} shipments")

best_idx = monthly['Avg_Delay'].idxmin()
best = monthly.loc[best_idx]
col4.metric("Best Performance", str(best['Month_Year']), f"{best['Avg_Delay']:.1f}d delay")

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Volume Trends", "⏱️ Delay Trends", "🏢 Carrier Evolution", "📅 Seasonality"])

with tab1:
    st.markdown("#### Monthly Shipment Volume")
    
    monthly['MA3'] = monthly['Shipments'].rolling(3, min_periods=1).mean()
    
    fig = make_subplots(specs=[[{"secondary_y": False}]])
    fig.add_trace(go.Bar(x=monthly['Month_Year_Dt'], y=monthly['Shipments'], name='Shipments',
                         marker_color='#1E3A5F', opacity=0.7))
    fig.add_trace(go.Scatter(x=monthly['Month_Year_Dt'], y=monthly['MA3'], name='3M Moving Avg',
                             line=dict(color='#E74C3C', width=3)))
    fig.update_layout(height=450, legend=dict(orientation="h", y=1.02),
                      xaxis_title="Month", yaxis_title="Shipments (B/L)")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("#### Carrier Mix Over Time")
    carrier_top = carrier_monthly[carrier_monthly['Carrier'].isin(top5)]
    fig = px.area(carrier_top, x='Month_Dt', y='Shipments', color='Carrier',
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(height=400, xaxis_title="Month", yaxis_title="Shipments")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("#### Monthly Average Delay")
    
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
    
    st.markdown("#### Delay Categories Over Time")
    delay_monthly = df.groupby(['Month_Year', 'Delay_Category']).size().reset_index(name='Count')
    delay_monthly['Month_Dt'] = pd.to_datetime(delay_monthly['Month_Year'])
    delay_monthly = delay_monthly.sort_values('Month_Dt')
    
    fig = px.bar(delay_monthly, x='Month_Dt', y='Count', color='Delay_Category', barmode='stack',
                 color_discrete_map={'On Time/Early': '#28a745', '1-3 Days Late': '#ffc107',
                                     '4-7 Days Late': '#fd7e14', '7+ Days Late': '#dc3545'})
    fig.update_layout(height=400, xaxis_title="Month")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("#### Carrier Performance Evolution")
    
    carriers = st.multiselect("Select Carriers to Compare",
        sorted(df['Carrier_Name'].unique().tolist()), default=top5[:3])
    
    if carriers:
        c_trend = carrier_monthly[carrier_monthly['Carrier'].isin(carriers)]
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### Volume Trend")
            fig = px.line(c_trend, x='Month_Dt', y='Shipments', color='Carrier', markers=True)
            fig.update_layout(height=400, xaxis_title="Month")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("##### Delay Trend")
            fig = px.line(c_trend, x='Month_Dt', y='Avg_Delay', color='Carrier', markers=True)
            fig.add_hline(y=0, line_dash="dash", line_color="green")
            fig.update_layout(height=400, xaxis_title="Month")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select at least one carrier to view trends")

with tab4:
    st.markdown("#### Seasonality Analysis")
    
    df_s = df.copy()
    df_s['Month_Num'] = df_s['Departure_Date'].dt.month
    df_s['Quarter'] = df_s['Departure_Date'].dt.quarter
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Average Volume by Month")
        month_agg = df_s.groupby('Month_Num').agg({
            'Bill_of_Lading': 'nunique', 'Arrival_Delay': 'mean'
        }).reset_index()
        month_agg.columns = ['Month', 'Shipments', 'Avg_Delay']
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        month_agg['Name'] = month_agg['Month'].apply(lambda x: month_names[int(x)-1] if pd.notna(x) and 1 <= x <= 12 else 'Unknown')
        
        fig = px.bar(month_agg, x='Name', y='Shipments', color='Avg_Delay',
                     color_continuous_scale='RdYlGn_r', text='Shipments')
        fig.update_traces(textposition='outside')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("##### Performance by Quarter")
        q_agg = df_s.groupby('Quarter').agg({
            'Bill_of_Lading': 'nunique', 'Arrival_Delay': 'mean'
        }).reset_index()
        q_agg.columns = ['Quarter', 'Shipments', 'Avg_Delay']
        q_agg['Q'] = 'Q' + q_agg['Quarter'].astype(int).astype(str)
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=q_agg['Q'], y=q_agg['Shipments'], name='Shipments',
                             marker_color='#1E3A5F'), secondary_y=False)
        fig.add_trace(go.Scatter(x=q_agg['Q'], y=q_agg['Avg_Delay'], name='Avg Delay',
                                 line=dict(color='#E74C3C', width=3), mode='lines+markers'), secondary_y=True)
        fig.update_yaxes(title_text="Shipments", secondary_y=False)
        fig.update_yaxes(title_text="Avg Delay (days)", secondary_y=True)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
