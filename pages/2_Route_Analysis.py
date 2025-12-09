"""
Route Analysis Page
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared import load_data, get_route_stats, get_carrier_route_matrix

st.set_page_config(page_title="Route Analysis", page_icon="🗺️", layout="wide")
st.title("🗺️ Route & Geographic Analysis")

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

# Sidebar
st.sidebar.header("Filters")
min_volume = st.sidebar.slider("Min Route Volume", 5, 100, 10)

# Stats
route_stats = get_route_stats(df)
route_stats_filtered = route_stats[route_stats['Shipments'] >= min_volume]

origin_stats = df.groupby('Origin_Country_Name').agg({
    'Bill_of_Lading': 'nunique', 'Arrival_Delay': 'mean', 'Is_Late': 'mean'
}).reset_index()
origin_stats.columns = ['Country', 'Shipments', 'Avg_Delay', 'Late_Rate']
origin_stats['Late_Rate'] = (origin_stats['Late_Rate'] * 100).round(1)
origin_stats = origin_stats.sort_values('Shipments', ascending=False)

dest_stats = df.groupby('POD_Country_Name').agg({
    'Bill_of_Lading': 'nunique', 'Arrival_Delay': 'mean', 'Is_Late': 'mean'
}).reset_index()
dest_stats.columns = ['Country', 'Shipments', 'Avg_Delay', 'Late_Rate']
dest_stats['Late_Rate'] = (dest_stats['Late_Rate'] * 100).round(1)
dest_stats = dest_stats.sort_values('Shipments', ascending=False)

# KPIs
st.markdown("### Route Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Routes", len(route_stats_filtered))
col2.metric("Origin Countries", df['Origin_Country_Name'].nunique())
col3.metric("Destination Countries", df['POD_Country_Name'].nunique())
if len(route_stats_filtered) > 0:
    best = route_stats_filtered.loc[route_stats_filtered['On_Time_Rate'].idxmax()]
    col4.metric("Best Route", f"{best['On_Time_Rate']:.0f}% on-time")

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🛤️ Top Routes", "🌍 Geographic", "🔥 Heatmaps", "📋 Data"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Top 15 Routes by Volume")
        fig = px.bar(route_stats_filtered.head(15), x='Shipments', y='Route', orientation='h',
                     color='Avg_Delay', color_continuous_scale='RdYlGn_r', text='Shipments')
        fig.update_traces(textposition='outside')
        fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Route Performance Scatter")
        scatter_data = route_stats_filtered.copy()
        scatter_data['Bubble_Size'] = scatter_data['Avg_Delay'].abs() + 3
        
        fig = px.scatter(scatter_data, x='Shipments', y='On_Time_Rate',
                         size='Bubble_Size', color='Severe_Late_Rate', color_continuous_scale='RdYlGn_r',
                         hover_name='Route')
        fig.add_hline(y=50, line_dash="dash", line_color="gray")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("#### Routes with Highest Delays")
    worst = route_stats_filtered.nlargest(10, 'Avg_Delay')
    fig = px.bar(worst, x='Route', y='Avg_Delay', color='Severe_Late_Rate',
                 color_continuous_scale='Reds', text='Avg_Delay')
    fig.update_traces(texttemplate='%{text:.1f}d', textposition='outside')
    fig.update_layout(height=400, xaxis_tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Shipments by Origin Country")
        fig = px.bar(origin_stats.head(12), x='Country', y='Shipments',
                     color='Avg_Delay', color_continuous_scale='RdYlGn_r', text='Shipments')
        fig.update_traces(textposition='outside')
        fig.update_layout(height=400, xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Shipments by Destination Country")
        fig = px.bar(dest_stats.head(12), x='Country', y='Shipments',
                     color='Avg_Delay', color_continuous_scale='RdYlGn_r', text='Shipments')
        fig.update_traces(textposition='outside')
        fig.update_layout(height=400, xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("#### World Map")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Origin Volume")
        fig = px.choropleth(origin_stats, locations='Country', locationmode='country names',
                            color='Shipments', color_continuous_scale='Blues',
                            hover_data={'Avg_Delay': ':.1f'})
        fig.update_layout(height=350, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("##### Destination Volume")
        fig = px.choropleth(dest_stats, locations='Country', locationmode='country names',
                            color='Shipments', color_continuous_scale='Greens',
                            hover_data={'Avg_Delay': ':.1f'})
        fig.update_layout(height=350, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("#### Carrier x Route Performance Matrix")
    
    metric = st.radio("Metric:", ["Volume", "Avg Delay", "On-Time %"], horizontal=True)
    
    top_carriers = df['Carrier_Name'].value_counts().head(8).index.tolist()
    top_routes = df['Route'].value_counts().head(10).index.tolist()
    df_sub = df[(df['Carrier_Name'].isin(top_carriers)) & (df['Route'].isin(top_routes))]
    
    if metric == "Volume":
        matrix = get_carrier_route_matrix(df_sub, 'count')
        colorscale = 'Blues'
    elif metric == "Avg Delay":
        matrix = get_carrier_route_matrix(df_sub, 'delay')
        colorscale = 'RdYlGn_r'
    else:
        matrix = get_carrier_route_matrix(df_sub, 'on_time')
        colorscale = 'RdYlGn'
    
    if not matrix.empty:
        fig = px.imshow(matrix, color_continuous_scale=colorscale, aspect='auto')
        fig.update_layout(height=450)
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Not enough data for selected combination")

with tab4:
    st.markdown("#### Route Data")
    display_cols = ['Route', 'Shipments', 'Containers', 'Avg_Delay', 'On_Time_Rate', 'Severe_Late_Rate']
    
    st.dataframe(
        route_stats_filtered[display_cols].style.format({
            'Avg_Delay': '{:.1f}', 'On_Time_Rate': '{:.1f}%',
            'Severe_Late_Rate': '{:.1f}%', 'Shipments': '{:,}', 'Containers': '{:,}'
        }),
        use_container_width=True, height=500
    )
    
    csv = route_stats_filtered.to_csv(index=False)
    st.download_button("📥 Download Route Data (CSV)", csv, "route_statistics.csv", "text/csv")
