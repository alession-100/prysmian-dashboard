"""
Shared functions for Prysmian Dashboard
All pages import from this file
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Country code mapping
COUNTRY_CODES = {
    'CN': 'China', 'CL': 'Chile', 'OM': 'Oman', 'DE': 'Germany', 'BR': 'Brazil',
    'US': 'United States', 'MZ': 'Mozambique', 'SA': 'Saudi Arabia', 'BH': 'Bahrain',
    'ES': 'Spain', 'IT': 'Italy', 'AE': 'UAE', 'MX': 'Mexico', 'PE': 'Peru',
    'MY': 'Malaysia', 'TH': 'Thailand', 'IN': 'India', 'TR': 'Turkey', 'FR': 'France',
    'NL': 'Netherlands', 'BE': 'Belgium', 'GB': 'United Kingdom', 'PT': 'Portugal',
    'AU': 'Australia', 'NZ': 'New Zealand', 'JP': 'Japan', 'KR': 'South Korea',
    'SG': 'Singapore', 'ID': 'Indonesia', 'PH': 'Philippines', 'VN': 'Vietnam',
    'EG': 'Egypt', 'ZA': 'South Africa', 'AR': 'Argentina', 'CO': 'Colombia',
    'EC': 'Ecuador', 'VE': 'Venezuela', 'PA': 'Panama', 'CR': 'Costa Rica',
    'FI': 'Finland', 'SE': 'Sweden', 'NO': 'Norway', 'DK': 'Denmark',
    'PL': 'Poland', 'CZ': 'Czech Republic', 'AT': 'Austria', 'CH': 'Switzerland',
    'GR': 'Greece', 'RO': 'Romania', 'HU': 'Hungary', 'BG': 'Bulgaria',
    'EE': 'Estonia', 'LV': 'Latvia', 'LT': 'Lithuania', 'SI': 'Slovenia',
    'HR': 'Croatia', 'SK': 'Slovakia', 'IE': 'Ireland', 'HK': 'Hong Kong',
    'TW': 'Taiwan', 'MA': 'Morocco', 'TN': 'Tunisia', 'KE': 'Kenya',
    'CA': 'Canada', 'RU': 'Russia', 'UA': 'Ukraine'
}

LOCODE_MAPPING = {
    'COCTG': ('Cartagena', 'Colombia'), 'CRPMN': ('Puerto Moín', 'Costa Rica'),
    'CRCAL': ('Puerto Caldera', 'Costa Rica'), 'ROCND': ('Constanta', 'Romania'),
    'EETLL': ('Tallinn', 'Estonia'), 'AUSYD': ('Sydney', 'Australia'),
    'AUFRE': ('Fremantle', 'Australia'), 'FIHEL': ('Helsinki', 'Finland'),
    'SIKOP': ('Koper', 'Slovenia'), 'SEGOT': ('Gothenburg', 'Sweden'),
    'ESBCN': ('Barcelona', 'Spain'), 'BRSSZ': ('Santos', 'Brazil'),
    'GBSOU': ('Southampton', 'United Kingdom'), 'NZAKL': ('Auckland', 'New Zealand'),
    'HKHKG': ('Hong Kong', 'Hong Kong'), 'CNSHA': ('Shanghai', 'China'),
    'CNNBO': ('Ningbo', 'China'), 'DEHAM': ('Hamburg', 'Germany'),
    'NLRTM': ('Rotterdam', 'Netherlands'), 'BEANR': ('Antwerp', 'Belgium'),
    'ITGOA': ('Genoa', 'Italy'), 'FRLEH': ('Le Havre', 'France'),
    'USLAX': ('Los Angeles', 'United States'), 'USHOU': ('Houston', 'United States'),
    'CLSAI': ('San Antonio', 'Chile'), 'OMSOH': ('Sohar', 'Oman'),
    'SGSIN': ('Singapore', 'Singapore'), 'AEJEA': ('Jebel Ali', 'UAE'),
}


def get_country_name(code):
    if pd.isna(code):
        return 'Unknown'
    return COUNTRY_CODES.get(str(code).upper(), str(code))


def get_port_info(locode):
    if pd.isna(locode):
        return ('Unknown', 'Unknown')
    locode = str(locode).upper()
    if locode in LOCODE_MAPPING:
        return LOCODE_MAPPING[locode]
    country_code = locode[:2]
    return (locode, get_country_name(country_code))


def load_data(filepath):
    """Load and preprocess Prysmian shipment data."""
    filepath = Path(filepath)
    
    if filepath.suffix.lower() == '.xlsx':
        df = pd.read_excel(filepath, sheet_name='nov23 to oct25 POLIMI')
    else:
        df = pd.read_csv(filepath)
    
    column_mapping = {
        'Arrival Delay (Days)': 'Arrival_Delay',
        'Departure Delay (Days)': 'Departure_Delay',
        'Transit (Days)': 'Transit_Days',
        'Roll Count - POL': 'Roll_Count',
        'Shipment Completed': 'Completed',
        'Origin Country': 'Origin_Country_Code',
        'POL LOCODE': 'POL_Code',
        'POD LOCODE': 'POD_Code',
        'Departure POL Date': 'Departure_Date',
        'Arrival POD Date': 'Arrival_Date',
        'Carrier Name': 'Carrier_Name',
        'Shipment ID': 'Shipment_ID',
        'Bill of Lading': 'Bill_of_Lading',
        'Container Number': 'Container_Number'
    }
    
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})
    
    if 'Origin_Country_Name' not in df.columns and 'Origin_Country_Code' in df.columns:
        df['Origin_Country_Name'] = df['Origin_Country_Code'].apply(get_country_name)
    
    if 'POL_City' not in df.columns and 'POL_Code' in df.columns:
        df['POL_City'] = df['POL_Code'].apply(lambda x: get_port_info(x)[0])
    
    if 'POD_City' not in df.columns and 'POD_Code' in df.columns:
        df['POD_City'] = df['POD_Code'].apply(lambda x: get_port_info(x)[0])
        df['POD_Country_Name'] = df['POD_Code'].apply(lambda x: get_port_info(x)[1])
    
    if 'Route' not in df.columns:
        df['Route'] = df['Origin_Country_Name'] + ' → ' + df['POD_Country_Name']
    
    for col in ['Departure_Date', 'Arrival_Date']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    if 'Month_Year' not in df.columns and 'Departure_Date' in df.columns:
        df['Month_Year'] = df['Departure_Date'].dt.to_period('M').astype(str)
    
    df['Is_Late'] = (df['Arrival_Delay'] > 0).astype(int)
    df['Is_Severely_Late'] = (df['Arrival_Delay'] > 7).astype(int)
    
    df['Delay_Category'] = pd.cut(
        df['Arrival_Delay'],
        bins=[-float('inf'), 0, 3, 7, float('inf')],
        labels=['On Time/Early', '1-3 Days Late', '4-7 Days Late', '7+ Days Late']
    )
    
    if 'Status' not in df.columns and 'Completed' in df.columns:
        df['Status'] = df['Completed'].apply(lambda x: 'Completed' if x else 'In Transit')
    
    return df


def calculate_kpis(df):
    """Calculate KPIs using Bill of Lading for unique shipment counts."""
    unique_shipments = df['Bill_of_Lading'].nunique()
    total_containers = len(df)
    
    return {
        'total_shipments': unique_shipments,
        'total_containers': total_containers,
        'total_carriers': df['Carrier_Name'].nunique(),
        'total_routes': df['Route'].nunique(),
        'avg_delay': df['Arrival_Delay'].mean(),
        'median_delay': df['Arrival_Delay'].median(),
        'std_delay': df['Arrival_Delay'].std(),
        'on_time_rate': (df['Arrival_Delay'] <= 0).mean() * 100,
        'late_rate': (df['Arrival_Delay'] > 0).mean() * 100,
        'severe_late_rate': (df['Arrival_Delay'] > 7).mean() * 100,
        'avg_transit_time': df['Transit_Days'].mean(),
        'total_rolls': df['Roll_Count'].sum(),
        'roll_rate': (df['Roll_Count'] > 0).mean() * 100,
    }


def get_carrier_stats(df):
    """Calculate statistics per carrier using Bill of Lading for shipment counts."""
    stats = df.groupby('Carrier_Name').agg({
        'Bill_of_Lading': 'nunique',
        'Container_Number': 'count',
        'Arrival_Delay': ['mean', 'median', 'std'],
        'Transit_Days': 'mean',
        'Is_Late': 'mean',
        'Is_Severely_Late': 'mean',
        'Roll_Count': 'sum'
    }).round(2)
    
    stats.columns = ['Shipments', 'Containers', 'Avg_Delay', 'Median_Delay', 'Std_Delay', 
                     'Avg_Transit', 'Late_Rate', 'Severe_Late_Rate', 'Total_Rolls']
    
    stats['Std_Delay'] = stats['Std_Delay'].fillna(0)
    stats['Market_Share'] = (stats['Shipments'] / stats['Shipments'].sum() * 100).round(1)
    stats['On_Time_Rate'] = ((1 - stats['Late_Rate']) * 100).round(1)
    stats['Late_Rate'] = (stats['Late_Rate'] * 100).round(1)
    stats['Severe_Late_Rate'] = (stats['Severe_Late_Rate'] * 100).round(1)
    
    return stats.sort_values('Shipments', ascending=False).reset_index()


def get_route_stats(df):
    """Calculate statistics per route using Bill of Lading for shipment counts."""
    stats = df.groupby('Route').agg({
        'Bill_of_Lading': 'nunique',
        'Container_Number': 'count',
        'Arrival_Delay': ['mean', 'median', 'std'],
        'Transit_Days': 'mean',
        'Is_Late': 'mean',
        'Is_Severely_Late': 'mean'
    }).round(2)
    
    stats.columns = ['Shipments', 'Containers', 'Avg_Delay', 'Median_Delay', 'Std_Delay', 
                     'Avg_Transit', 'Late_Rate', 'Severe_Late_Rate']
    
    stats['Std_Delay'] = stats['Std_Delay'].fillna(0)
    stats['On_Time_Rate'] = ((1 - stats['Late_Rate']) * 100).round(1)
    stats['Late_Rate'] = (stats['Late_Rate'] * 100).round(1)
    stats['Severe_Late_Rate'] = (stats['Severe_Late_Rate'] * 100).round(1)
    
    return stats.sort_values('Shipments', ascending=False).reset_index()


def get_monthly_trends(df):
    """Calculate monthly trends using Bill of Lading for shipment counts."""
    monthly = df.groupby('Month_Year').agg({
        'Bill_of_Lading': 'nunique',
        'Container_Number': 'count',
        'Arrival_Delay': 'mean',
        'Transit_Days': 'mean',
        'Is_Late': 'mean',
        'Is_Severely_Late': 'mean',
        'Roll_Count': 'sum'
    }).round(2)
    
    monthly.columns = ['Shipments', 'Containers', 'Avg_Delay', 'Avg_Transit', 
                       'Late_Rate', 'Severe_Late_Rate', 'Total_Rolls']
    monthly['Late_Rate'] = (monthly['Late_Rate'] * 100).round(1)
    monthly['Severe_Late_Rate'] = (monthly['Severe_Late_Rate'] * 100).round(1)
    
    return monthly.reset_index()


def perform_clustering(df, n_clusters=3):
    """Perform K-Means clustering on route-level data."""
    route_agg = df.groupby('Route').agg({
        'Bill_of_Lading': 'nunique',
        'Arrival_Delay': ['mean', 'std'],
        'Transit_Days': 'mean',
        'Is_Late': 'mean',
        'Is_Severely_Late': 'mean',
        'Roll_Count': 'mean'
    }).reset_index()
    
    route_agg.columns = ['Route', 'Volume', 'Avg_Delay', 'Std_Delay', 
                         'Avg_Transit', 'Late_Rate', 'Severe_Late_Rate', 'Avg_Rolls']
    
    route_agg['Std_Delay'] = route_agg['Std_Delay'].fillna(0)
    
    features = ['Avg_Delay', 'Std_Delay', 'Late_Rate', 'Severe_Late_Rate']
    X = route_agg[features].values
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    route_agg['Cluster'] = kmeans.fit_predict(X_scaled)
    
    cluster_delays = route_agg.groupby('Cluster')['Avg_Delay'].mean().sort_values()
    risk_labels = {}
    for i, cluster_id in enumerate(cluster_delays.index):
        if i == 0:
            risk_labels[cluster_id] = 'Low Risk'
        elif i == n_clusters - 1:
            risk_labels[cluster_id] = 'High Risk'
        else:
            risk_labels[cluster_id] = 'Medium Risk'
    
    route_agg['Risk_Level'] = route_agg['Cluster'].map(risk_labels)
    
    cluster_stats = route_agg.groupby('Risk_Level').agg({
        'Route': 'count', 'Volume': 'sum', 'Avg_Delay': 'mean',
        'Late_Rate': 'mean', 'Severe_Late_Rate': 'mean'
    }).round(2)
    cluster_stats.columns = ['Routes', 'Shipments', 'Avg_Delay', 'Late_Rate', 'Severe_Late_Rate']
    
    return route_agg, cluster_stats.to_dict()


def calculate_risk_score(row):
    """Calculate composite risk score."""
    score = 0
    delay = row.get('Avg_Delay', row.get('Arrival_Delay', 0))
    if delay <= 0:
        score += 0
    elif delay <= 3:
        score += 10
    elif delay <= 7:
        score += 25
    else:
        score += 40
    
    std_delay = row.get('Std_Delay', 0)
    if std_delay <= 2:
        score += 0
    elif std_delay <= 5:
        score += 15
    else:
        score += 30
    
    late_rate = row.get('Late_Rate', row.get('Severe_Late_Rate', 0))
    if isinstance(late_rate, (int, float)):
        if late_rate <= 0.3:
            score += 0
        elif late_rate <= 0.5:
            score += 15
        else:
            score += 30
    
    return score


def get_carrier_route_matrix(df, metric='count'):
    """Create carrier-route matrix using Bill of Lading for counts."""
    if metric == 'count':
        matrix = df.groupby(['Carrier_Name', 'Route'])['Bill_of_Lading'].nunique().unstack(fill_value=0)
    elif metric == 'delay':
        matrix = df.pivot_table(values='Arrival_Delay', index='Carrier_Name',
                                columns='Route', aggfunc='mean').round(1)
    elif metric == 'on_time':
        df_temp = df.copy()
        df_temp['On_Time'] = (df_temp['Arrival_Delay'] <= 0).astype(int)
        matrix = df_temp.pivot_table(values='On_Time', index='Carrier_Name',
                                     columns='Route', aggfunc='mean').round(2) * 100
    return matrix


def identify_high_risk_routes(df, threshold_delay=5.0):
    """Identify high-risk routes."""
    route_stats = get_route_stats(df)
    high_risk = route_stats[route_stats['Avg_Delay'] >= threshold_delay].copy()
    high_risk['Risk_Score'] = high_risk.apply(calculate_risk_score, axis=1)
    return high_risk.sort_values('Risk_Score', ascending=False)


def identify_best_performers(df, min_volume=50):
    """Identify best performing carriers."""
    carrier_stats = get_carrier_stats(df)
    qualified = carrier_stats[carrier_stats['Shipments'] >= min_volume].copy()
    return qualified.sort_values('On_Time_Rate', ascending=False)
