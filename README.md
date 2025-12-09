# Prysmian Ocean Logistics Dashboard

Interactive analytics dashboard for container shipment performance.
Built for the GEMOS Challenge Project at POLIMI Graduate School of Management.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Dashboard

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

## Project Structure

```
prysmian_dashboard/
├── app.py                              # Main dashboard (Executive Overview)
├── requirements.txt                    # Python dependencies
├── data/
│   └── Prysmian_Shipments_Nov23_Oct25.xlsx
├── pages/
│   ├── 1_Carrier_Analysis.py
│   ├── 2_Route_Analysis.py
│   ├── 3_Time_Trends.py
│   ├── 4_Risk_Analysis.py
│   └── 5_AI_Insights.py
└── utils/
    └── analysis_toolkit.py
```

## Dashboard Pages

| Page | Description |
|------|-------------|
| **Executive Dashboard** | KPIs, carrier volume, market share |
| **Carrier Analysis** | Carrier performance deep dive |
| **Route Analysis** | Geographic patterns, heatmaps |
| **Time Trends** | Monthly trends, seasonality |
| **Risk Analysis** | K-Means clustering, risk scoring |
| **AI Insights** | LLM prompt templates |

## Key Features

- **Shipment counting by Bill of Lading** (not container count)
- **K-Means clustering** for risk identification
- **Interactive filters** for carriers, routes, and dates
- **Export functionality** for all data tables
- **LLM prompt templates** for AI-powered analysis

## Data Requirements

The dashboard expects an Excel file with sheet `nov23 to oct25 POLIMI` containing:

- `Bill of Lading` - Unique shipment identifier
- `Carrier Name` - Shipping carrier
- `Origin Country` - 2-letter country code
- `POL LOCODE` / `POD LOCODE` - Port codes
- `Arrival Delay (Days)` - Delay in days
- `Transit (Days)` - Total transit time
- `Roll Count - POL` - Roll count at port of loading
- `Departure POL Date` - Departure date

## Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Set main file: `app.py`
5. Deploy!

## License

MIT License - GEMOS Project 2025
