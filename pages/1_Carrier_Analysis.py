"""
Carrier Analysis Page
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared import load_data, get_carrier_stats

st.set_page_config(page_title="Carrier Analysis", page_icon="🏢", layout="wide")
st.title("🏢 Carrier Performance Analysis")

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
min_shipments = st.sidebar.slider("Minimum Shipments", 0, 200, 20)
selected_carriers = st.sidebar.multiselect("Compare Carriers",
    options=sorted(df['Carrier_Name'].unique().tolist()),
    default=df['Carrier_Name'].value_counts().head(5).index.tolist())

# Stats
carrier_stats = get_carrier_stats(df)
carrier_stats_filtered = carrier_stats[carrier_stats['Shipments'] >= min_shipments]

# Metrics
st.markdown("### Carrier Comparison Summary")
col1, col2, col3 = st.columns(3)

if len(carrier_stats_filtered) > 0:
    best = carrier_stats_filtered.loc[carrier_stats_filtered['On_Time_Rate'].idxmax()]
    col1.metric("Best On-Time Rate", f"{best['On_Time_Rate']:.1f}%", best['Carrier_Name'])
    
    lowest = carrier_stats_filtered.loc[carrier_stats_filtered['Avg_Delay'].idxmin()]
    col2.metric("Lowest Avg Delay", f"{lowest['Avg_Delay']:.1f} days", lowest['Carrier_Name'])
    
    consistent = carrier_stats_filtered.loc[carrier_stats_filtered['Std_Delay'].idxmin()]
    col3.metric("Most Consistent", f"σ = {consistent['Std_Delay']:.1f}", consistent['Carrier_Name'])

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Volume", "⏱️ Delays", "📈 Performance", "📋 Data"])

with tab1:
    col_v, col_s = st.columns(2)
    
    with col_v:
        st.markdown("#### Shipment Volume by Carrier")
        fig = px.bar(carrier_stats_filtered.head(15), x='Carrier_Name', y='Shipments',
                     color='On_Time_Rate', color_continuous_scale='RdYlGn', text='Shipments')
        fig.update_layout(height=450, xaxis_tickangle=45)
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    with col_s:
        st.markdown("#### Market Share")
        fig = px.pie(carrier_stats_filtered.head(10), values='Shipments', names='Carrier_Name',
                     hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_traces(textposition='outside', textinfo='percent+label')
        fig.update_layout(height=450, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    col_d1, col_d2 = st.columns(2)
    
    with col_d1:
        st.markdown("#### Average Delay by Carrier")
        sorted_stats = carrier_stats_filtered.sort_values('Avg_Delay').head(15)
        fig = px.bar(sorted_stats, x='Avg_Delay', y='Carrier_Name', orientation='h',
                     color='Avg_Delay', color_continuous_scale='RdYlGn_r', text='Avg_Delay')
        fig.add_vline(x=0, line_dash="dash", line_color="green")
        fig.update_traces(texttemplate='%{text:.1f}d', textposition='outside')
        fig.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_d2:
        st.markdown("#### Delay Distribution (Box Plot)")
        if selected_carriers:
            df_filt = df[df['Carrier_Name'].isin(selected_carriers)]
        else:
            df_filt = df[df['Carrier_Name'].isin(carrier_stats.head(5)['Carrier_Name'])]
        
        fig = px.box(df_filt, x='Carrier_Name', y='Arrival_Delay', color='Carrier_Name', points='outliers')
        fig.add_hline(y=0, line_dash="dash", line_color="green", annotation_text="On Time")
        fig.add_hline(y=7, line_dash="dash", line_color="red", annotation_text="Severe")
        fig.update_layout(height=500, showlegend=False, xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Delay Categories by Carrier")
    delay_by_carrier = df.groupby(['Carrier_Name', 'Delay_Category']).size().reset_index(name='Count')
    top_carriers = carrier_stats.head(10)['Carrier_Name'].tolist()
    delay_by_carrier = delay_by_carrier[delay_by_carrier['Carrier_Name'].isin(top_carriers)]
    
    fig = px.bar(delay_by_carrier, x='Carrier_Name', y='Count', color='Delay_Category', barmode='stack',
                 color_discrete_map={'On Time/Early': '#28a745', '1-3 Days Late': '#ffc107',
                                     '4-7 Days Late': '#fd7e14', '7+ Days Late': '#dc3545'})
    fig.update_layout(height=400, xaxis_tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("#### Performance Quadrant: Volume vs Reliability")
    
    perf_data = carrier_stats_filtered.copy()
    perf_data['Bubble_Size'] = perf_data['Avg_Delay'].abs() + 5
    
    fig = px.scatter(perf_data, x='Shipments', y='On_Time_Rate',
                     size='Bubble_Size', color='Severe_Late_Rate', color_continuous_scale='RdYlGn_r',
                     hover_name='Carrier_Name', text='Carrier_Name')
    fig.update_traces(textposition='top center', textfont_size=10)
    fig.add_hline(y=50, line_dash="dash", line_color="gray")
    fig.add_vline(x=perf_data['Shipments'].median(), line_dash="dash", line_color="gray")
    fig.update_layout(height=600, xaxis_title="Volume (Shipments)", yaxis_title="On-Time Rate (%)")
    
    fig.add_annotation(x=0.95, y=0.95, xref="paper", yref="paper",
                       text="High Vol + High Perf", showarrow=False, font=dict(color="green"))
    fig.add_annotation(x=0.95, y=0.05, xref="paper", yref="paper",
                       text="High Vol + Low Perf", showarrow=False, font=dict(color="red"))
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.markdown("#### Detailed Statistics")
    
    display_cols = ['Carrier_Name', 'Shipments', 'Containers', 'Market_Share', 'On_Time_Rate',
                    'Avg_Delay', 'Median_Delay', 'Std_Delay', 'Severe_Late_Rate', 'Total_Rolls']
    
    st.dataframe(
        carrier_stats_filtered[display_cols].style.format({
            'Market_Share': '{:.1f}%', 'On_Time_Rate': '{:.1f}%',
            'Avg_Delay': '{:.1f}', 'Median_Delay': '{:.1f}', 'Std_Delay': '{:.1f}',
            'Severe_Late_Rate': '{:.1f}%', 'Shipments': '{:,}', 'Containers': '{:,}'
        }),
        use_container_width=True, height=400
    )
    
    csv = carrier_stats_filtered.to_csv(index=False)
    st.download_button("📥 Download Carrier Data (CSV)", csv, "carrier_statistics.csv", "text/csv")
