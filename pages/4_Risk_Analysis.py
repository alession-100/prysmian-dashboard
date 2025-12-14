"""
Risk Analysis & AI Clustering Page - All charts respond to filters
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared import (load_data, perform_clustering, identify_high_risk_routes,
                    identify_best_performers)

st.set_page_config(page_title="Risk Analysis", page_icon="⚠️", layout="wide")
st.title("⚠️ Risk Analysis & AI Clustering")

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

st.sidebar.markdown("---")
st.sidebar.header("🎯 Clustering Parameters")
n_clusters = st.sidebar.slider("Number of Risk Clusters", 2, 5, 3)
risk_threshold = st.sidebar.slider("High Risk Delay Threshold (days)", 3.0, 10.0, 5.0)

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
if len(filtered_df) < len(df):
    st.sidebar.success(f"✅ {len(filtered_df):,} of {len(df):,} containers")
else:
    st.sidebar.info(f"📊 All {len(df):,} containers")

# ============== CLUSTERING ON FILTERED DATA ==============
if len(filtered_df) > 10:  # Need minimum data for clustering
    route_clusters, cluster_stats = perform_clustering(filtered_df, n_clusters)
    high_risk_routes = identify_high_risk_routes(filtered_df, risk_threshold)
    best_performers = identify_best_performers(filtered_df, min_volume=10)
else:
    route_clusters = pd.DataFrame()
    high_risk_routes = pd.DataFrame()
    best_performers = pd.DataFrame()

# ============== KPIs ==============
st.markdown("### Risk Overview")
col1, col2, col3, col4 = st.columns(4)

if len(route_clusters) > 0:
    high_risk_count = (route_clusters['Risk_Level'] == 'High Risk').sum()
    total_routes = len(route_clusters)
    high_pct = (high_risk_count / total_routes * 100) if total_routes > 0 else 0
    col1.metric("High Risk Routes", f"{high_risk_count} ({high_pct:.0f}%)")
    
    col2.metric("Routes Above Threshold", len(high_risk_routes))
    
    high_risk_shipments = route_clusters[route_clusters['Risk_Level'] == 'High Risk']['Volume'].sum()
    col3.metric("High Risk Shipments", f"{int(high_risk_shipments):,}")
    
    high_risk_data = route_clusters[route_clusters['Risk_Level'] == 'High Risk']
    avg_high = high_risk_data['Avg_Delay'].mean() if len(high_risk_data) > 0 else 0
    col4.metric("Avg High Risk Delay", f"{avg_high:.1f} days")
else:
    col1.metric("Routes", "0")
    col2.metric("High Risk", "N/A")
    col3.metric("Shipments", "0")
    col4.metric("Avg Delay", "N/A")

st.markdown("---")

# ============== TABS ==============
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Clustering Results", "🔥 Risk Heatmaps", "📋 Risk Tables", "💡 Recommendations"])

with tab1:
    if len(route_clusters) > 0:
        col1, col2 = st.columns([1.2, 1])
        
        with col1:
            st.markdown("#### K-Means Risk Clustering")
            fig = px.scatter(route_clusters, x='Avg_Delay', y='Late_Rate', color='Risk_Level',
                             size='Volume', hover_name='Route',
                             color_discrete_map={'Low Risk': '#28a745', 'Medium Risk': '#ffc107', 'High Risk': '#dc3545'})
            fig.update_layout(height=500, xaxis_title="Average Delay (days)", yaxis_title="Late Rate")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Cluster Distribution")
            cluster_dist = route_clusters.groupby('Risk_Level').agg({
                'Route': 'count', 'Volume': 'sum'
            }).reset_index()
            cluster_dist.columns = ['Risk Level', 'Routes', 'Shipments']
            
            fig = px.pie(cluster_dist, values='Shipments', names='Risk Level',
                         color='Risk Level', hole=0.4,
                         color_discrete_map={'Low Risk': '#28a745', 'Medium Risk': '#ffc107', 'High Risk': '#dc3545'})
            fig.update_traces(textposition='outside', textinfo='percent+label')
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("#### Cluster Summary")
            st.dataframe(cluster_dist.style.format({'Shipments': '{:,}', 'Routes': '{:,}'}),
                         use_container_width=True)
        
        st.markdown("#### 3D Risk Visualization")
        fig = px.scatter_3d(route_clusters, x='Avg_Delay', y='Late_Rate', z='Std_Delay',
                            color='Risk_Level', size='Volume', hover_name='Route',
                            color_discrete_map={'Low Risk': '#28a745', 'Medium Risk': '#ffc107', 'High Risk': '#dc3545'})
        fig.update_layout(height=600, scene=dict(
            xaxis_title='Avg Delay (days)', yaxis_title='Late Rate', zaxis_title='Delay Variability'))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Not enough data for clustering. Try adjusting filters.")

with tab2:
    st.markdown("#### Carrier x Route Delay Heatmap")
    
    if len(filtered_df) > 0:
        top_carriers = filtered_df['Carrier_Name'].value_counts().head(8).index.tolist()
        top_routes = filtered_df['Route'].value_counts().head(10).index.tolist()
        df_sub = filtered_df[(filtered_df['Carrier_Name'].isin(top_carriers)) & 
                             (filtered_df['Route'].isin(top_routes))]
        
        if len(df_sub) > 0:
            delay_matrix = df_sub.pivot_table(values='Arrival_Delay', index='Carrier_Name',
                                               columns='Route', aggfunc='mean').round(1)
            
            if not delay_matrix.empty:
                fig = px.imshow(delay_matrix, color_continuous_scale='RdYlGn_r', aspect='auto',
                                labels=dict(color="Avg Delay (days)"))
                fig.update_layout(height=450)
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("#### Severe Delay Rate Heatmap")
            severe_matrix = df_sub.pivot_table(values='Is_Severely_Late', index='Carrier_Name',
                                                columns='Route', aggfunc='mean').round(2) * 100
            
            if not severe_matrix.empty:
                fig = px.imshow(severe_matrix, color_continuous_scale='Reds', aspect='auto',
                                labels=dict(color="Severe Delay %"))
                fig.update_layout(height=450)
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Not enough data for heatmap")
    else:
        st.warning("No data matching filters")

with tab3:
    st.markdown("#### High Risk Routes")
    
    if len(high_risk_routes) > 0:
        display = ['Route', 'Shipments', 'Containers', 'Avg_Delay', 'On_Time_Rate', 'Severe_Late_Rate', 'Risk_Score']
        available_cols = [c for c in display if c in high_risk_routes.columns]
        
        st.dataframe(
            high_risk_routes[available_cols].head(20).style.format({
                'Avg_Delay': '{:.1f}', 'On_Time_Rate': '{:.1f}%',
                'Severe_Late_Rate': '{:.1f}%', 'Risk_Score': '{:.0f}',
                'Shipments': '{:,}', 'Containers': '{:,}'
            }),
            use_container_width=True, height=400
        )
        
        fig = px.bar(high_risk_routes.head(15), x='Route', y='Avg_Delay', color='Risk_Score',
                     color_continuous_scale='Reds', text='Avg_Delay')
        fig.update_traces(texttemplate='%{text:.1f}d', textposition='outside')
        fig.update_layout(height=400, xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success(f"✅ No routes found above {risk_threshold} days delay threshold!")
    
    st.markdown("---")
    st.markdown("#### Best Performing Carriers")
    
    if len(best_performers) > 0:
        display_cols = ['Carrier_Name', 'Shipments', 'On_Time_Rate', 'Avg_Delay', 'Severe_Late_Rate']
        st.dataframe(
            best_performers[display_cols].head(10).style.format({
                'On_Time_Rate': '{:.1f}%', 'Avg_Delay': '{:.1f}',
                'Severe_Late_Rate': '{:.1f}%', 'Shipments': '{:,}'
            }),
            use_container_width=True
        )
    else:
        st.info("No carriers with sufficient volume in filtered data")
    
    if len(route_clusters) > 0:
        csv = route_clusters.to_csv(index=False)
        st.download_button("📥 Download Cluster Data (CSV)", csv, "route_clusters.csv", "text/csv")

with tab4:
    st.markdown("#### AI-Generated Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🚨 Immediate Actions Required")
        
        if len(filtered_df) > 0:
            risk_carriers = filtered_df.groupby('Carrier_Name').agg({
                'Arrival_Delay': 'mean', 'Is_Severely_Late': 'mean', 'Bill_of_Lading': 'nunique'
            }).reset_index()
            risk_carriers.columns = ['Carrier', 'Avg_Delay', 'Severe_Rate', 'Volume']
            risk_carriers = risk_carriers[risk_carriers['Volume'] >= 10].sort_values('Severe_Rate', ascending=False)
            
            if len(risk_carriers) > 0:
                worst = risk_carriers.iloc[0]
                st.error(f"""
                **Review: {worst['Carrier']}**
                - Severe delay rate: {worst['Severe_Rate']*100:.1f}%
                - Average delay: {worst['Avg_Delay']:.1f} days
                - Shipments: {int(worst['Volume']):,}
                
                *Recommended: Schedule performance review meeting*
                """)
            
            if len(high_risk_routes) > 0:
                worst_route = high_risk_routes.iloc[0]
                st.warning(f"""
                **Investigate: {worst_route['Route']}**
                - Average delay: {worst_route['Avg_Delay']:.1f} days
                - On-time rate: {worst_route['On_Time_Rate']:.1f}%
                
                *Recommended: Analyze root cause, consider alternative carriers*
                """)
    
    with col2:
        st.markdown("##### ✅ Optimization Opportunities")
        
        if len(best_performers) > 0:
            best = best_performers.iloc[0]
            st.success(f"""
            **Increase volume with: {best['Carrier_Name']}**
            - On-time rate: {best['On_Time_Rate']:.1f}%
            - Current shipments: {int(best['Shipments']):,}
            
            *Recommended: Negotiate volume-based rates*
            """)
        
        if len(route_clusters) > 0:
            low_risk = route_clusters[route_clusters['Risk_Level'] == 'Low Risk'].nlargest(3, 'Volume')
            if len(low_risk) > 0:
                st.info("**Best performing routes to prioritize:**")
                for _, r in low_risk.iterrows():
                    st.write(f"- {r['Route']}: {r['Late_Rate']*100:.1f}% late rate")
    
    st.markdown("---")
    st.markdown("#### Strategy Matrix by Risk Level")
    
    strategies = [
        ("Low Risk", "Maintain & Optimize: Focus on cost optimization, benchmark best practices", "#28a745"),
        ("Medium Risk", "Monitor & Improve: Increase tracking frequency, review carrier SLAs monthly", "#ffc107"),
        ("High Risk", "Intervene & Transform: Performance reviews, carrier replacement evaluation, add buffer time", "#dc3545")
    ]
    
    for level, strategy, color in strategies:
        st.markdown(f"""<div style='padding: 12px; margin: 8px 0; border-left: 5px solid {color}; 
                    background-color: {color}15; border-radius: 0 5px 5px 0;'>
                    <strong style='color: {color};'>{level}</strong><br>{strategy}</div>""", 
                    unsafe_allow_html=True)
