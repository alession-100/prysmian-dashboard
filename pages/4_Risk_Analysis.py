"""
Risk Analysis & AI Clustering Page
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared import (load_data, perform_clustering, identify_high_risk_routes,
                    identify_best_performers, get_carrier_route_matrix)

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

# Sidebar
st.sidebar.header("Parameters")
n_clusters = st.sidebar.slider("Number of Risk Clusters", 2, 5, 3)
risk_threshold = st.sidebar.slider("High Risk Delay Threshold (days)", 3.0, 10.0, 5.0)

# Clustering
@st.cache_data
def get_clustering(data_hash, n):
    return perform_clustering(df, n)

route_clusters, cluster_stats = get_clustering(str(len(df)), n_clusters)

# KPIs
st.markdown("### Risk Overview")
col1, col2, col3, col4 = st.columns(4)

high_risk_count = (route_clusters['Risk_Level'] == 'High Risk').sum()
total_routes = len(route_clusters)
high_pct = (high_risk_count / total_routes * 100) if total_routes > 0 else 0
col1.metric("High Risk Routes", f"{high_risk_count} ({high_pct:.0f}%)")

high_risk_routes = identify_high_risk_routes(df, risk_threshold)
col2.metric("Routes Above Threshold", len(high_risk_routes))

high_risk_shipments = route_clusters[route_clusters['Risk_Level'] == 'High Risk']['Volume'].sum()
col3.metric("High Risk Shipments", f"{int(high_risk_shipments):,}")

high_risk_data = route_clusters[route_clusters['Risk_Level'] == 'High Risk']
avg_high = high_risk_data['Avg_Delay'].mean() if len(high_risk_data) > 0 else 0
col4.metric("Avg High Risk Delay", f"{avg_high:.1f} days")

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Clustering Results", "🔥 Risk Heatmaps", "📋 Risk Tables", "💡 Recommendations"])

with tab1:
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

with tab2:
    st.markdown("#### Carrier x Route Delay Heatmap")
    
    top_carriers = df['Carrier_Name'].value_counts().head(8).index.tolist()
    top_routes = df['Route'].value_counts().head(10).index.tolist()
    df_sub = df[(df['Carrier_Name'].isin(top_carriers)) & (df['Route'].isin(top_routes))]
    
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

with tab3:
    st.markdown("#### High Risk Routes")
    
    if not high_risk_routes.empty:
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
        st.success(f"No routes found above {risk_threshold} days delay threshold!")
    
    st.markdown("---")
    st.markdown("#### Best Performing Carriers (min 20 shipments)")
    best_performers = identify_best_performers(df, min_volume=20)
    
    if not best_performers.empty:
        display_cols = ['Carrier_Name', 'Shipments', 'On_Time_Rate', 'Avg_Delay', 'Severe_Late_Rate']
        st.dataframe(
            best_performers[display_cols].head(10).style.format({
                'On_Time_Rate': '{:.1f}%', 'Avg_Delay': '{:.1f}',
                'Severe_Late_Rate': '{:.1f}%', 'Shipments': '{:,}'
            }),
            use_container_width=True
        )
    
    csv = route_clusters.to_csv(index=False)
    st.download_button("📥 Download Cluster Data (CSV)", csv, "route_clusters.csv", "text/csv")

with tab4:
    st.markdown("#### AI-Generated Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🚨 Immediate Actions Required")
        
        risk_carriers = df.groupby('Carrier_Name').agg({
            'Arrival_Delay': 'mean', 'Is_Severely_Late': 'mean', 'Bill_of_Lading': 'nunique'
        }).reset_index()
        risk_carriers.columns = ['Carrier', 'Avg_Delay', 'Severe_Rate', 'Volume']
        risk_carriers = risk_carriers[risk_carriers['Volume'] >= 50].sort_values('Severe_Rate', ascending=False)
        
        if not risk_carriers.empty:
            worst = risk_carriers.iloc[0]
            st.error(f"""
            **Review: {worst['Carrier']}**
            - Severe delay rate: {worst['Severe_Rate']*100:.1f}%
            - Average delay: {worst['Avg_Delay']:.1f} days
            - Shipments: {int(worst['Volume']):,}
            
            *Recommended: Schedule performance review meeting*
            """)
        
        if not high_risk_routes.empty:
            worst_route = high_risk_routes.iloc[0]
            st.warning(f"""
            **Investigate: {worst_route['Route']}**
            - Average delay: {worst_route['Avg_Delay']:.1f} days
            - On-time rate: {worst_route['On_Time_Rate']:.1f}%
            
            *Recommended: Analyze root cause, consider alternative carriers*
            """)
    
    with col2:
        st.markdown("##### ✅ Optimization Opportunities")
        
        if not best_performers.empty:
            best = best_performers.iloc[0]
            st.success(f"""
            **Increase volume with: {best['Carrier_Name']}**
            - On-time rate: {best['On_Time_Rate']:.1f}%
            - Current shipments: {int(best['Shipments']):,}
            
            *Recommended: Negotiate volume-based rates*
            """)
        
        low_risk = route_clusters[route_clusters['Risk_Level'] == 'Low Risk'].nlargest(3, 'Volume')
        if not low_risk.empty:
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
