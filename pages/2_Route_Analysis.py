"""
Route Analysis Page - All charts respond to filters
Volume = Containers, Performance = Shipments (B/L)
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
st.sidebar.markdown("### 📊 Statistical Filters")

# Min containers (volume filter)
min_containers = st.sidebar.slider("📦 Min Route Containers", 1, 200, 20,
                                    help="Minimum container count for route to appear")

# Min shipments (performance filter)
min_shipments = st.sidebar.slider("📋 Min Route Shipments", 1, 50, 5,
                                   help="Minimum shipment count for route to appear")

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

# ============== CALCULATE STATS FROM FILTERED DATA ==============
route_stats = get_route_stats(filtered_df)

# Apply filters
route_stats_by_containers = route_stats[route_stats['Containers'] >= min_containers]
route_stats_by_shipments = route_stats[route_stats['Shipments'] >= min_shipments]

# Origin stats from filtered data (using containers for volume)
origin_stats = filtered_df.groupby('Origin_Country_Name').agg({
    'Container_Number': 'count',
    'Bill_of_Lading': 'nunique',
    'Arrival_Delay': 'mean',
    'Is_Late': 'mean'
}).reset_index()
origin_stats.columns = ['Country', 'Containers', 'Shipments', 'Avg_Delay', 'Late_Rate']
origin_stats['Late_Rate'] = (origin_stats['Late_Rate'] * 100).round(1)
origin_stats = origin_stats.sort_values('Containers', ascending=False)

# Destination stats from filtered data (using containers for volume)
dest_stats = filtered_df.groupby('POD_Country_Name').agg({
    'Container_Number': 'count',
    'Bill_of_Lading': 'nunique',
    'Arrival_Delay': 'mean',
    'Is_Late': 'mean'
}).reset_index()
dest_stats.columns = ['Country', 'Containers', 'Shipments', 'Avg_Delay', 'Late_Rate']
dest_stats['Late_Rate'] = (dest_stats['Late_Rate'] * 100).round(1)
dest_stats = dest_stats.sort_values('Containers', ascending=False)

# ============== KPIs ==============
st.markdown("### Route Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Routes", len(route_stats_by_containers))
col2.metric("Origin Countries", filtered_df['Origin_Country_Name'].nunique())
col3.metric("Destination Countries", filtered_df['POD_Country_Name'].nunique())

# Best route - show route name if 100% on-time
if len(route_stats_by_shipments) > 0:
    best = route_stats_by_shipments.loc[route_stats_by_shipments['On_Time_Rate'].idxmax()]
    if best['On_Time_Rate'] >= 100:
        col4.metric("Best Route - 100% on-time", best['Route'])
    else:
        col4.metric("Best Route", f"{best['On_Time_Rate']:.0f}% on-time", best['Route'])

st.markdown("---")

# ============== TABS ==============
tab1, tab2, tab3, tab4 = st.tabs(["🛤️ Top Routes", "🌍 Geographic", "🔥 Heatmaps", "📋 Data"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Top 15 Routes by Shipments")
        if len(route_stats_by_shipments) > 0:
            chart_data = route_stats_by_shipments.sort_values('Shipments', ascending=False).head(15)
            fig = px.bar(chart_data, x='Shipments', y='Route', orientation='h',
                         color='Avg_Delay', color_continuous_scale='RdYlGn_r', text='Shipments',
                         labels={'Shipments': 'Shipments (B/L)', 'Avg_Delay': 'Avg Delay (days)'})
            fig.update_traces(textposition='outside')
            fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No routes match the current filters")
    
    with col2:
        st.markdown("#### Route Performance Scatter")
        st.caption("*Bubble size = Container volume*")
        if len(route_stats_by_shipments) > 0:
            scatter_data = route_stats_by_shipments.copy()
            # Use Containers for bubble size
            scatter_data['Bubble_Size'] = scatter_data['Containers'] / scatter_data['Containers'].max() * 50 + 5
            
            fig = px.scatter(scatter_data, x='Shipments', y='On_Time_Rate',
                             size='Bubble_Size', color='Severe_Late_Rate', color_continuous_scale='RdYlGn_r',
                             hover_name='Route',
                             hover_data={'Containers': True, 'Shipments': True, 'Avg_Delay': ':.1f'})
            fig.add_hline(y=50, line_dash="dash", line_color="gray")
            fig.update_layout(height=500, xaxis_title="Shipments (B/L)", yaxis_title="On-Time Rate (%)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data to display")
    
    # Worst routes (by performance)
    st.markdown("#### Routes with Highest Delays")
    if len(route_stats_by_shipments) > 0:
        worst = route_stats_by_shipments.nlargest(10, 'Avg_Delay')
        fig = px.bar(worst, x='Route', y='Avg_Delay', color='Severe_Late_Rate',
                     color_continuous_scale='Reds', text='Avg_Delay')
        fig.update_traces(texttemplate='%{text:.1f}d', textposition='outside')
        fig.update_layout(height=400, xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Containers by Origin Country")
        if len(origin_stats) > 0:
            fig = px.bar(origin_stats.head(12), x='Country', y='Containers',
                         color='Avg_Delay', color_continuous_scale='RdYlGn_r', text='Containers')
            fig.update_traces(textposition='outside')
            fig.update_layout(height=400, xaxis_tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data to display")
    
    with col2:
        st.markdown("#### Containers by Destination Country")
        if len(dest_stats) > 0:
            fig = px.bar(dest_stats.head(12), x='Country', y='Containers',
                         color='Avg_Delay', color_continuous_scale='RdYlGn_r', text='Containers')
            fig.update_traces(textposition='outside')
            fig.update_layout(height=400, xaxis_tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data to display")
    
    # World maps
    st.markdown("#### World Map")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Origin Volume (Containers)")
        if len(origin_stats) > 0:
            fig = px.choropleth(origin_stats, locations='Country', locationmode='country names',
                                color='Containers', color_continuous_scale='Blues',
                                hover_data={'Avg_Delay': ':.1f', 'Shipments': True})
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("##### Destination Volume (Containers)")
        if len(dest_stats) > 0:
            fig = px.choropleth(dest_stats, locations='Country', locationmode='country names',
                                color='Containers', color_continuous_scale='Greens',
                                hover_data={'Avg_Delay': ':.1f', 'Shipments': True})
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("#### Carrier x Route Performance Matrix")
    
    metric = st.radio("Metric:", ["Container Volume", "Avg Delay", "On-Time %"], horizontal=True)
    
    # Use filtered data for heatmap
    if len(filtered_df) > 0:
        top_carriers = filtered_df['Carrier_Name'].value_counts().head(8).index.tolist()
        top_routes = filtered_df['Route'].value_counts().head(10).index.tolist()
        df_sub = filtered_df[(filtered_df['Carrier_Name'].isin(top_carriers)) & 
                             (filtered_df['Route'].isin(top_routes))]
        
        if len(df_sub) > 0:
            if metric == "Container Volume":
                matrix = df_sub.pivot_table(values='Container_Number', index='Carrier_Name',
                                            columns='Route', aggfunc='count').fillna(0)
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
                st.warning("Not enough data for heatmap")
        else:
            st.warning("Not enough data for selected combination")
    else:
        st.warning("No data matching filters")

with tab4:
    st.markdown("#### Route Data")
    
    if len(route_stats_by_containers) > 0:
        display_cols = ['Route', 'Containers', 'Shipments', 'Avg_Delay', 'On_Time_Rate', 'Severe_Late_Rate']
        
        st.dataframe(
            route_stats_by_containers[display_cols].style.format({
                'Avg_Delay': '{:.1f}', 'On_Time_Rate': '{:.1f}%',
                'Severe_Late_Rate': '{:.1f}%', 'Shipments': '{:,}', 'Containers': '{:,}'
            }),
            use_container_width=True, height=500
        )
        
        csv = route_stats_by_containers.to_csv(index=False)
        st.download_button("📥 Download Route Data (CSV)", csv, "route_statistics.csv", "text/csv")
    else:
        st.warning("No routes matching filters")
