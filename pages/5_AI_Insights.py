"""
AI Insights & LLM Prompts Page
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared import load_data, get_carrier_stats, get_route_stats, calculate_kpis

st.set_page_config(page_title="AI Insights", page_icon="🤖", layout="wide")
st.title("🤖 AI Insights & LLM Prompts")

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
carrier_stats = get_carrier_stats(df)
route_stats = get_route_stats(df)
kpis = calculate_kpis(df)

st.markdown("### Ready-to-Use LLM Prompt Templates")
st.markdown("Copy these prompts to use with Claude, ChatGPT, or other AI assistants.")

tab1, tab2, tab3, tab4 = st.tabs(["🎯 Risk Detection", "⚡ Optimization", "📊 Performance Review", "🌱 Sustainability"])

with tab1:
    st.markdown("#### Risk Detection Prompts")
    
    high_risk = carrier_stats[carrier_stats['Severe_Late_Rate'] > 30]['Carrier_Name'].tolist()
    high_delay = route_stats[route_stats['Avg_Delay'] > 5]['Route'].head(5).tolist()
    
    prompt1 = f"""**PROMPT 1: Shipment Risk Assessment**

Analyze this shipment for risk factors:
- Carrier: [CARRIER_NAME]
- Route: [ORIGIN] → [DESTINATION]
- Scheduled Transit: [X] days

Context from historical data:
- High-risk carriers (>30% severe delays): {', '.join(high_risk[:3]) if high_risk else 'None identified'}
- High-delay routes (>5 days avg): {', '.join(high_delay[:3]) if high_delay else 'None identified'}

Please provide:
1. Risk level assessment (Low/Medium/High)
2. Specific risk factors to monitor
3. Mitigation recommendations
4. Suggested monitoring frequency"""
    
    st.code(prompt1, language="markdown")
    
    prompt2 = """**PROMPT 2: Delay Root Cause Analysis**

A shipment has experienced a delay of [X] days.

Shipment Details:
- Carrier: [NAME]
- Route: [ORIGIN] → [DESTINATION]
- Expected transit: [Y] days
- Actual transit: [Z] days
- Roll count: [N]
- Season/Month: [MONTH]

Please analyze:
1. Most likely root causes for this delay
2. Whether this is an anomaly or part of a pattern
3. Recommended corrective actions
4. Prevention measures for future shipments"""
    
    st.code(prompt2, language="markdown")

with tab2:
    st.markdown("#### Carrier & Route Optimization Prompts")
    
    best = carrier_stats.nlargest(3, 'On_Time_Rate')[['Carrier_Name', 'On_Time_Rate', 'Shipments']].to_dict('records')
    
    prompt3 = f"""**PROMPT 3: Carrier Portfolio Optimization**

Current top performers:
{chr(10).join([f"- {c['Carrier_Name']}: {c['On_Time_Rate']:.1f}% on-time, {c['Shipments']:,} shipments" for c in best])}

Overall portfolio:
- Total carriers: {kpis['total_carriers']}
- Average on-time rate: {kpis['on_time_rate']:.1f}%

Please recommend:
1. Which carriers should receive increased volume allocation?
2. Which carriers need performance improvement plans?
3. Are there gaps in carrier coverage by region?
4. What negotiation leverage exists based on volume?
5. Potential savings from carrier consolidation"""
    
    st.code(prompt3, language="markdown")
    
    prompt4 = """**PROMPT 4: Route Optimization Analysis**

Current route performance:
- Total active routes: [N]
- Average delay across routes: [X] days
- Overall on-time rate: [Y]%

Please identify:
1. Routes that would benefit from alternative carriers
2. Potential transshipment optimizations
3. Routes suitable for direct service negotiation
4. Expected impact of 10% delay reduction
5. Priority routes for immediate attention"""
    
    st.code(prompt4, language="markdown")

with tab3:
    st.markdown("#### Performance Review Prompts")
    
    prompt5 = f"""**PROMPT 5: Executive Performance Summary**

Key Metrics (current period):
- Total shipments: {kpis['total_shipments']:,} (by Bill of Lading)
- Total containers: {kpis['total_containers']:,}
- Average delay: {kpis['avg_delay']:.1f} days
- On-time rate: {kpis['on_time_rate']:.1f}%
- Severe delay rate (>7 days): {kpis['severe_late_rate']:.1f}%
- Active carriers: {kpis['total_carriers']}
- Active routes: {kpis['total_routes']}

Please provide:
1. Executive summary (3-4 key sentences)
2. Top highlights (positive trends)
3. Areas of concern requiring attention
4. Recommended focus areas for next period
5. Industry benchmark comparison (if available)"""
    
    st.code(prompt5, language="markdown")
    
    prompt6 = """**PROMPT 6: Carrier Scorecard Generation**

Generate a comprehensive scorecard for [CARRIER_NAME]:

Performance Metrics:
- Total shipments: [N]
- On-time rate: [X]%
- Average delay: [Y] days
- Delay variability (std dev): [Z] days
- Severe delay rate (>7 days): [W]%
- Roll count incidents: [R]

Please include:
1. Overall performance grade (A through F)
2. Strengths analysis
3. Areas for improvement
4. Trend assessment (improving/stable/declining)
5. Recommended contract actions
6. Performance targets for next quarter"""
    
    st.code(prompt6, language="markdown")

with tab4:
    st.markdown("#### Sustainability Assessment Prompts")
    
    top_carriers = carrier_stats.head(5)['Carrier_Name'].tolist()
    
    prompt7 = f"""**PROMPT 7: Carrier Sustainability Research**

Research sustainability initiatives for our top carriers:
{chr(10).join([f"- {c}" for c in top_carriers])}

For each carrier, identify:
1. Carbon neutrality commitments and timeline
2. Fleet modernization initiatives (LNG, methanol, electric)
3. Green shipping corridor participation
4. Sustainability certifications held
5. Scope 3 emissions reporting capabilities
6. Biofuel or alternative fuel programs

Provide a comparison matrix and recommendations aligned with Prysmian's sustainability goals."""
    
    st.code(prompt7, language="markdown")
    
    prompt8 = """**PROMPT 8: Sustainability Action Plan**

Based on Prysmian's commitment to sustainability, develop an action plan:

Current logistics profile:
- Annual shipment volume: [X] TEUs
- Primary carriers: [LIST]
- Main trade lanes: [LIST]

Please develop:
1. Quick wins (0-6 months)
2. Medium-term initiatives (6-18 months)
3. Long-term transformation (18+ months)
4. KPIs and tracking mechanisms
5. Estimated emissions reduction potential
6. Cost implications and funding options
7. Stakeholder communication plan"""
    
    st.code(prompt8, language="markdown")

st.markdown("---")
st.markdown("### 📤 Data Export for AI Analysis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Carrier Summary Data")
    carrier_export = carrier_stats[['Carrier_Name', 'Shipments', 'On_Time_Rate', 'Avg_Delay', 'Severe_Late_Rate']].head(15)
    st.dataframe(carrier_export, use_container_width=True, height=300)
    csv = carrier_export.to_csv(index=False)
    st.download_button("📥 Download Carrier Data", csv, "carriers_for_ai.csv", "text/csv", key="c_dl")

with col2:
    st.markdown("#### Route Summary Data")
    route_export = route_stats[['Route', 'Shipments', 'On_Time_Rate', 'Avg_Delay', 'Severe_Late_Rate']].head(15)
    st.dataframe(route_export, use_container_width=True, height=300)
    csv = route_export.to_csv(index=False)
    st.download_button("📥 Download Route Data", csv, "routes_for_ai.csv", "text/csv", key="r_dl")

st.markdown("---")
st.markdown("### 🔧 Custom Prompt Generator")

col1, col2 = st.columns(2)

with col1:
    analysis_type = st.selectbox("Analysis Type", 
        ["Risk Assessment", "Performance Review", "Carrier Comparison", "Route Optimization"])
    carrier = st.selectbox("Select Carrier (optional)", ["All Carriers"] + carrier_stats['Carrier_Name'].tolist())

with col2:
    period = st.selectbox("Time Period", ["Last Month", "Last Quarter", "Last 6 Months", "Full Period"])
    output_format = st.selectbox("Output Format", ["Executive Summary", "Detailed Report", "Action Items", "Presentation"])

if st.button("🚀 Generate Custom Prompt", type="primary"):
    if carrier != "All Carriers":
        c_data = carrier_stats[carrier_stats['Carrier_Name'] == carrier].iloc[0]
        context = f"""
Carrier: {carrier}
- Shipments: {c_data['Shipments']:,}
- On-Time Rate: {c_data['On_Time_Rate']:.1f}%
- Average Delay: {c_data['Avg_Delay']:.1f} days
- Severe Late Rate: {c_data['Severe_Late_Rate']:.1f}%"""
    else:
        context = f"""
All Carriers:
- Total Shipments: {kpis['total_shipments']:,}
- On-Time Rate: {kpis['on_time_rate']:.1f}%
- Average Delay: {kpis['avg_delay']:.1f} days
- Number of Carriers: {kpis['total_carriers']}"""
    
    custom_prompt = f"""**CUSTOM ANALYSIS REQUEST**

Analysis Type: {analysis_type}
Time Period: {period}
Output Format: {output_format}

Context Data:
{context}

Please provide:
1. Key findings and insights
2. Performance trends
3. Risk factors identified
4. Recommended actions
5. Next steps

Format the response appropriately for a {output_format.lower()}."""
    
    st.code(custom_prompt, language="markdown")
    st.success("✅ Prompt generated! Copy and use with your preferred AI assistant.")

st.markdown("---")
st.info("""
**💡 Tip:** These prompts are designed to work with any modern LLM. 
For best results, combine the prompts with data exports from this dashboard.
""")
