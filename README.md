# 📊 Campaign Analytics Dashboard

An interactive Streamlit dashboard for analyzing campaign performance with hierarchical drill-down capabilities.

## Features

✅ **Hierarchical Drill-down**: Release Order → Line Item → Campaign
✅ **Day-wise Consumption**: Track impressions and revenue by day
✅ **Delivery Tracking**: Monitor % delivery vs scheduled impressions
✅ **Performance Metrics**: CTR%, CPM, revenue analysis
✅ **Multiple Reports**: Release Order, Line Item, Campaign, Raw Data
✅ **Export Reports**: Download data as CSV

## Installation

### Local Setup

```bash
# Clone repository
git clone <your-repo-url>
cd Dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run dashboard.py
```

Dashboard will open at `http://localhost:8501`

## Requirements

- Python 3.8+
- pandas
- streamlit
- plotly
- openpyxl
- xlrd

## Usage

1. **Select Filters** from the left sidebar:
   - Release Order
   - Line Item
   - Campaign
   - Status

2. **Navigate Tabs**:
   - **Hierarchical Drill-down**: Complete RO → LI → Campaign breakdown
   - **Overview**: Top campaigns and performance charts
   - **Release Order Report**: Revenue summary by RO
   - **Line Item Report**: Detailed line item metrics
   - **Campaign Report**: Day-wise impressions, revenue, and delivery %
   - **Raw Data**: Full dataset view

3. **Download Reports**: Available on each tab

## File Structure

```
Dashboard/
├── dashboard.py          # Main application
├── requirements.txt      # Python dependencies
├── .gitignore           # Git ignore file
└── README.md            # This file
```

## Data Input

Place your Analytics.xls file at: `/Users/rayanpawar/Downloads/Analytics.xls`

## Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
3. Connect your GitHub repository
4. Select this app to deploy
5. It will be live automatically!

## Features

- **Real-time filtering** with cascading dropdowns
- **Interactive charts** with Plotly
- **Delivery % tracking** based on scheduled impressions
- **Day-wise analytics** for revenue and impressions
- **CSV export** for all reports

## Support

For issues or questions, check the dashboard locally first.

---

**Dashboard Version**: 1.0  
**Last Updated**: April 29, 2026
