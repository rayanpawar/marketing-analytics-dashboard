import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from io import BytesIO

# Page configuration
st.set_page_config(page_title="Campaign Analytics Dashboard", layout="wide")

# Title
st.title("� Campaign Analytics Dashboard")

# Password Protection
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets.get("dashboard_password", ""):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.warning("🔐 This dashboard contains confidential data. Please enter the password to proceed.")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.error("😕 Password incorrect")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    else:
        # Password correct.
        return True

if not check_password():
    st.stop()

st.markdown("---")

# Initialize session state for workflow
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = None
if 'excel_details_submitted' not in st.session_state:
    st.session_state.excel_details_submitted = False
if 'sheet_name' not in st.session_state:
    st.session_state.sheet_name = "Analytics"

# STEP 1: FILE UPLOAD
st.write("### 📁 STEP 1: Upload Excel File")
uploaded_files = st.file_uploader("Upload Excel file for analysis", type=["xls", "xlsx"], accept_multiple_files=False, key="daily_reports")

if uploaded_files:
    st.session_state.uploaded_files = uploaded_files
    st.success(f"✅ File uploaded: {uploaded_files.name}")
    
    # Get available sheet names
    try:
        xls = pd.ExcelFile(uploaded_files)
        available_sheets = xls.sheet_names
    except Exception as e:
        st.error(f"Error reading Excel file: {str(e)}")
        available_sheets = []
    
    # STEP 2: EXCEL DETAILS
    st.markdown("---")
    st.write("### 📊 STEP 2: Configure Excel Details")
    
    with st.form("excel_config_form"):
        st.write("Please provide details about your Excel file:")
        
        # Show available sheets for selection
        if available_sheets:
            st.write(f"**Available sheets:** {', '.join(available_sheets)}")
            sheet_name_input = st.selectbox(
                "Select Sheet Name",
                options=available_sheets,
                help="Select the sheet in the Excel file to read"
            )
        else:
            sheet_name_input = st.text_input(
                "Sheet Name",
                value=st.session_state.sheet_name,
                help="Enter the name of the sheet in the Excel file to read"
            )
        
        date_columns = st.multiselect(
            "Date Columns (select all that apply)",
            options=["Date", "Date Start", "Date End"],
            default=["Date"],
            help="Select which columns should be treated as dates"
        )
        
        numeric_columns = st.multiselect(
            "Numeric Columns (select all that apply)",
            options=["Impressions", "Requests", "Revenue (INR)", "Schedule Impression", "Schedule Click", "CTR%"],
            default=["Impressions", "Requests", "Revenue (INR)", "Schedule Impression", "CTR%"],
            help="Select which columns should be treated as numeric values"
        )
        
        groupby_columns = st.multiselect(
            "Grouping Columns (for analysis)",
            options=["Release Order", "Line Item", "Campaigns", "Publisher", "Campaign Status"],
            default=["Release Order", "Line Item", "Campaigns"],
            help="Select columns to group data by for analysis"
        )
        
        submit_config = st.form_submit_button("✅ Submit Configuration")
    
    if submit_config:
        st.session_state.sheet_name = sheet_name_input if sheet_name_input else "Analytics"
        st.session_state.date_columns = date_columns
        st.session_state.numeric_columns = numeric_columns
        st.session_state.groupby_columns = groupby_columns
        st.session_state.excel_details_submitted = True
        st.success("Configuration saved! Processing data...")
        st.rerun()

# If file upload and configuration not done, stop here
if not st.session_state.excel_details_submitted:
    st.info("👆 Please upload a file and configure Excel details to continue")
    st.stop()

# Load data
@st.cache_data
def load_data(file_path=None, sheet_name_param="Analytics"):
    """Load Excel file with specified sheet"""
    try:
        df = pd.read_excel(file_path or "Analytics.xls", sheet_name=sheet_name_param)
    except:
        # Try without sheet_name if it fails
        try:
            df = pd.read_excel(file_path or "Analytics.xls")
        except:
            return None
    
    return df

def process_data(df, date_cols, numeric_cols):
    """Process dataframe with specified column types"""
    if df is None:
        return None
    
    df = df.copy()
    
    # Convert date columns
    for col in date_cols:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except:
                pass
    
    # Convert numeric columns
    for col in numeric_cols:
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except:
                pass
    
    return df

def load_uploaded_file(uploaded_file, sheet_name_param="Analytics"):
    """Load a single uploaded Excel file"""
    try:
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name_param)
        return df
    except Exception as e:
        st.warning(f"Error loading {uploaded_file.name}: {str(e)}")
        return None

# Load data source
if st.session_state.uploaded_files:
    df = load_uploaded_file(st.session_state.uploaded_files, st.session_state.sheet_name)
    df = process_data(df, st.session_state.date_columns, st.session_state.numeric_columns)
    if df is not None:
        st.success(f"✅ Data loaded successfully! {len(df)} records found.")
    else:
        st.error("Failed to load data from the uploaded file.")
        st.stop()
else:
    st.error("No file loaded. Please upload a file first.")
    st.stop()

if df is None or len(df) == 0:
    st.error("No data loaded. Please ensure the Excel file has valid data.")
    st.stop()

# Show available columns for user reference
with st.expander("📋 Available Columns in Your Data"):
    st.write("The following columns were detected in your Excel file:")
    st.write(", ".join(sorted(df.columns.tolist())))

# Display basic stats
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Records", len(df))

with col2:
    if 'Impressions' in df.columns:
        total_impressions = df['Impressions'].sum()
        st.metric("Total Impressions", f"{int(total_impressions):,}")
    else:
        st.metric("Total Impressions", "N/A")

with col3:
    if 'Requests' in df.columns:
        total_requests = df['Requests'].sum()
        st.metric("Total Requests", f"{int(total_requests):,}")
    else:
        st.metric("Total Requests", "N/A")

with col4:
    if 'Revenue (INR)' in df.columns:
        total_revenue = df['Revenue (INR)'].sum()
        st.metric("Total Revenue", f"₹{total_revenue:,.0f}")
    else:
        st.metric("Total Revenue", "N/A")

with col5:
    if 'CTR%' in df.columns:
        avg_ctr = df['CTR%'].mean()
        st.metric("Avg CTR%", f"{avg_ctr:.2f}%")
    else:
        st.metric("Avg CTR%", "N/A")

st.markdown("---")

# Cascading Filters - Dynamic based on selected groupby columns
st.sidebar.title("🔍 Hierarchical Filters")

# Create filters based on groupby_columns selection
available_groupby = st.session_state.groupby_columns
selected_filters = {}

# Filter 1: Release Order
if "Release Order" in available_groupby:
    if 'Release Order' in df.columns:
        release_orders = sorted(df['Release Order'].unique())
        selected_filters['Release Order'] = st.sidebar.selectbox("📌 Release Order", ["All"] + release_orders)
    
# Filter 2: Line Item (filtered by Release Order)
if "Line Item" in available_groupby:
    if 'Line Item' in df.columns:
        if selected_filters.get('Release Order') and selected_filters['Release Order'] != "All":
            line_items = sorted(df[df['Release Order'] == selected_filters['Release Order']]['Line Item'].unique())
        else:
            line_items = sorted(df['Line Item'].unique())
        selected_filters['Line Item'] = st.sidebar.selectbox("📌 Line Item", ["All"] + list(line_items))

# Filter 3: Campaigns (filtered by Line Item)
if "Campaigns" in available_groupby:
    if 'Campaigns' in df.columns:
        if selected_filters.get('Line Item') and selected_filters['Line Item'] != "All":
            campaigns = sorted(df[df['Line Item'] == selected_filters['Line Item']]['Campaigns'].unique())
        else:
            campaigns = sorted(df['Campaigns'].unique())
        selected_filters['Campaigns'] = st.sidebar.selectbox("📌 Campaign", ["All"] + list(campaigns))

# Filter 4: Publisher
if "Publisher" in available_groupby:
    if 'Publisher' in df.columns:
        publishers = sorted(df['Publisher'].unique())
        selected_filters['Publisher'] = st.sidebar.selectbox("📌 Publisher", ["All"] + list(publishers))

# Filter 5: Campaign Status
if "Campaign Status" in available_groupby:
    if 'Campaign Status' in df.columns:
        statuses = sorted(df['Campaign Status'].unique())
        selected_filters['Campaign Status'] = st.sidebar.multiselect("Status", statuses, default=statuses)

# Apply filters
filtered_df = df.copy()

for filter_name, filter_value in selected_filters.items():
    if filter_name == 'Campaign Status' and filter_value:
        filtered_df = filtered_df[filtered_df[filter_name].isin(filter_value)]
    elif filter_value and filter_value != "All":
        filtered_df = filtered_df[filtered_df[filter_name] == filter_value]

# Tab navigation
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Hierarchical Drill-down", "Overview", "Release Order Report", "Line Item Report", "Campaign Report", "Raw Data"])

with tab1:
    if 'Release Order' not in df.columns:
        st.warning("⚠️ This tab requires 'Release Order' column which is not in your data.")
        st.info("Please upload a file with Release Order data, or select it from the configuration form.")
    else:
        selected_ro = selected_filters.get('Release Order', 'All')
        selected_li = selected_filters.get('Line Item', 'All')
        
        st.subheader(f"📊 Hierarchical Breakdown - {selected_ro if selected_ro != 'All' else 'All Release Orders'}")
        
        if selected_ro == "All":
            st.info("Select a Release Order from the left panel to view hierarchical breakdown")
        else:
            # Get data for selected RO
            ro_data = df[df['Release Order'] == selected_ro]
            
            # RO Level Metrics
            st.write(f"### 📌 Release Order: {selected_ro}")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                if 'Line Item' in df.columns:
                    st.metric("Line Items", ro_data['Line Item'].nunique())
            with col2:
                if 'Campaigns' in df.columns:
                    st.metric("Campaigns", ro_data['Campaigns'].nunique())
            with col3:
                if 'Impressions' in df.columns:
                    st.metric("Total Impressions", f"{ro_data['Impressions'].sum():,}")
            with col4:
                if 'Revenue (INR)' in df.columns:
                    st.metric("Total Revenue", f"₹{ro_data['Revenue (INR)'].sum():,.0f}")
            with col5:
                if 'CTR%' in df.columns:
                    st.metric("Avg CTR%", f"{ro_data['CTR%'].mean():.2f}%")
            
            st.markdown("---")
            
            # Line Item Level Breakdown
            if 'Line Item' in df.columns and 'Campaigns' in df.columns:
                st.write("### 📋 Line Items in this Release Order")
                li_breakdown = ro_data.groupby('Line Item').agg({
                    'Campaigns': 'nunique',
                    'Impressions': 'sum' if 'Impressions' in df.columns else 'count',
                    'Requests': 'sum' if 'Requests' in df.columns else 'count',
                    'Revenue (INR)': 'sum' if 'Revenue (INR)' in df.columns else 'count',
                    'CTR%': 'mean' if 'CTR%' in df.columns else 'count'
                }).reset_index().sort_values('Impressions', ascending=False)
                
                li_breakdown.columns = ['Line Item', 'Campaigns Count', 'Impressions', 'Requests', 'Revenue (₹)', 'Avg CTR%']
                li_breakdown['Revenue (₹)'] = li_breakdown['Revenue (₹)'].apply(lambda x: f"₹{x:,.0f}")
                li_breakdown['Avg CTR%'] = li_breakdown['Avg CTR%'].apply(lambda x: f"{x:.2f}%")
                
                st.dataframe(li_breakdown, use_container_width=True)
                
                st.markdown("---")
            
            # Campaign Level Breakdown (if Line Item selected)
            if selected_li != "All" and 'Line Item' in df.columns and 'Campaigns' in df.columns:
                st.write(f"### 🎯 Campaigns in {selected_li}")
                campaign_breakdown = ro_data[ro_data['Line Item'] == selected_li].groupby('Campaigns').agg({
                    'Impressions': 'sum' if 'Impressions' in df.columns else 'count',
                    'Requests': 'sum' if 'Requests' in df.columns else 'count',
                    'Revenue (INR)': 'sum' if 'Revenue (INR)' in df.columns else 'count',
                    'CTR%': 'mean' if 'CTR%' in df.columns else 'count',
                    'Schedule Impression': 'first' if 'Schedule Impression' in df.columns else 'count'
                }).reset_index().sort_values('Impressions', ascending=False)
                
                if 'Schedule Impression' in df.columns:
                    campaign_breakdown['Delivery %'] = (campaign_breakdown['Impressions'] / campaign_breakdown['Schedule Impression'].replace(0, 1) * 100).round(2)
                    campaign_breakdown.columns = ['Campaign', 'Impressions', 'Requests', 'Revenue (₹)', 'Avg CTR%', 'Scheduled', 'Delivery %']
                else:
                    campaign_breakdown.columns = ['Campaign', 'Impressions', 'Requests', 'Revenue (₹)', 'Avg CTR%', 'Scheduled']
                
                campaign_breakdown['Revenue (₹)'] = campaign_breakdown['Revenue (₹)'].apply(lambda x: f"₹{x:,.0f}")
                campaign_breakdown['Avg CTR%'] = campaign_breakdown['Avg CTR%'].apply(lambda x: f"{x:.2f}%")
                if 'Delivery %' in campaign_breakdown.columns:
                    campaign_breakdown['Delivery %'] = campaign_breakdown['Delivery %'].apply(lambda x: f"{x:.1f}%")
                
                st.dataframe(campaign_breakdown, use_container_width=True)
            elif 'Line Item' in df.columns and 'Campaigns' in df.columns:
                st.write("### 🎯 Select a Line Item to see Campaign Details")
                # Show all campaigns under RO grouped by Line Item
                all_campaigns = ro_data.groupby(['Line Item', 'Campaigns']).agg({
                    'Impressions': 'sum' if 'Impressions' in df.columns else 'count',
                    'Revenue (INR)': 'sum' if 'Revenue (INR)' in df.columns else 'count',
                    'CTR%': 'mean' if 'CTR%' in df.columns else 'count'
                }).reset_index().sort_values(['Line Item', 'Impressions'], ascending=[True, False])
                
                all_campaigns.columns = ['Line Item', 'Campaign', 'Impressions', 'Revenue (₹)', 'Avg CTR%']
                all_campaigns['Revenue (₹)'] = all_campaigns['Revenue (₹)'].apply(lambda x: f"₹{x:,.0f}")
                all_campaigns['Avg CTR%'] = all_campaigns['Avg CTR%'].apply(lambda x: f"{x:.2f}%")
                
                st.dataframe(all_campaigns, use_container_width=True)

with tab2:
    st.subheader("📊 Performance Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            # Top campaigns by impressions
            campaign_impressions = filtered_df.groupby('Campaigns')['Impressions'].sum().sort_values(ascending=False).head(10).reset_index()
            fig = px.bar(campaign_impressions, x='Campaigns', y='Impressions', 
                        title="Top 10 Campaigns by Impressions", color='Impressions',
                        color_continuous_scale='Blues')
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating impressions chart: {str(e)}")
    
    with col2:
        try:
            # Top campaigns by CTR
            campaign_ctr = filtered_df.groupby('Campaigns')['CTR%'].mean().sort_values(ascending=False).head(10).reset_index()
            fig = px.bar(campaign_ctr, x='Campaigns', y='CTR%', 
                        title="Top 10 Campaigns by CTR%", color='CTR%',
                        color_continuous_scale='Greens')
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating CTR chart: {str(e)}")

with tab3:
    st.subheader("� Release Order Report - Total Revenue from Campaign Budget")
    
    try:
        # Group by Release Order
        release_order_df = filtered_df.groupby('Release Order').agg({
            'Campaigns': 'count',
            'Impressions': 'sum',
            'Requests': 'sum',
            'Revenue (INR)': 'sum',
            'Campaign Budget': 'first'
        }).reset_index()
        
        release_order_df.columns = ['Release Order', 'Line Items', 'Total Impressions', 'Total Requests', 'Total Revenue', 'Budget']
        release_order_df = release_order_df.sort_values('Total Revenue', ascending=False)
        
        # Calculate metrics
        release_order_df['CPM'] = (release_order_df['Total Revenue'] / release_order_df['Total Impressions'] * 1000).round(2)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Revenue", f"₹{release_order_df['Total Revenue'].sum():,.0f}")
        with col2:
            st.metric("Release Orders", len(release_order_df))
        with col3:
            st.metric("Avg Revenue per RO", f"₹{release_order_df['Total Revenue'].mean():,.0f}")
        
        st.write("### Release Order Revenue Details")
        st.dataframe(release_order_df, use_container_width=True)
        
        # Visualization
        fig = px.pie(release_order_df.head(15), values='Total Revenue', names='Release Order', 
                    title="Revenue Distribution by Release Order")
        st.plotly_chart(fig, use_container_width=True)
        
        # Download Report
        csv = release_order_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Release Order Report",
            data=csv,
            file_name="release_order_report.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Error generating Release Order Report: {str(e)}")

with tab4:
    st.subheader("� Line Item Report")
    
    try:
        line_item_df = filtered_df[['Date', 'Release Order', 'Line Item', 'Campaigns', 'Impressions', 
                                     'Requests', 'Revenue (INR)', 'CTR%', 'Campaign Status', 'Campaign Budget']].copy()
        
        st.write(f"### Showing {len(line_item_df)} Line Items")
        st.dataframe(line_item_df, use_container_width=True)
        
        # Summary by Line Item
        st.write("### Line Items Summary")
        summary_df = line_item_df.groupby('Line Item').agg({
            'Impressions': 'sum',
            'Requests': 'sum',
            'Revenue (INR)': 'sum',
            'CTR%': 'mean'
        }).reset_index().sort_values('Revenue (INR)', ascending=False)
        
        summary_df.columns = ['Line Item', 'Total Impressions', 'Total Requests', 'Total Revenue', 'Avg CTR%']
        st.dataframe(summary_df, use_container_width=True)
        
        # Download Report
        csv = line_item_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Line Item Report",
            data=csv,
            file_name="line_item_report.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Error generating Line Item Report: {str(e)}")

with tab5:
    st.subheader("📊 Campaign Report - Day-wise Impressions Consumption & Delivery %")
    
    try:
        # Prepare daily campaign data
        daily_campaign_data = filtered_df.copy()
        
        # Clean Date column - remove NaT values
        daily_campaign_data = daily_campaign_data.dropna(subset=['Date'])
        
        if len(daily_campaign_data) == 0:
            st.warning("No valid date data available for this selection")
        else:
            # Group by Date and Campaign
            daily_data = daily_campaign_data.groupby(['Date', 'Campaigns']).agg({
                'Impressions': 'sum',
                'Requests': 'sum',
                'Revenue (INR)': 'sum',
                'CTR%': 'mean',
                'Schedule Impression': 'first'
            }).reset_index().sort_values('Date')
            
            # Calculate delivery percentage
            daily_data['Delivery %'] = (daily_data['Impressions'] / daily_data['Schedule Impression'].replace(0, 1) * 100).round(2)
            daily_data['Delivery %'] = daily_data['Delivery %'].clip(upper=100)  # Cap at 100%
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Impressions", f"{daily_data['Impressions'].sum():,}")
            with col2:
                st.metric("Avg Daily Impressions", f"{daily_data['Impressions'].mean():,.0f}")
            with col3:
                st.metric("Avg Delivery %", f"{daily_data['Delivery %'].mean():.1f}%")
            
            # Daily impressions trend by campaign
            fig = px.line(daily_data, x='Date', y='Impressions', color='Campaigns',
                         title="Daily Impressions Consumption by Campaign", markers=True)
            st.plotly_chart(fig, use_container_width=True)
            
            # Delivery percentage trend
            fig2 = px.line(daily_data, x='Date', y='Delivery %', color='Campaigns',
                          title="Daily Delivery % by Campaign", markers=True)
            fig2.update_yaxes(range=[0, 105])
            st.plotly_chart(fig2, use_container_width=True)
            
            st.markdown("---")
            st.write("## 💰 Day-wise Revenue & Impressions Consumption")
            
            # Day-wise summary (overall, not by campaign)
            daily_summary = daily_campaign_data.groupby('Date').agg({
                'Impressions': 'sum',
                'Revenue (INR)': 'sum',
                'Requests': 'sum',
                'CTR%': 'mean'
            }).reset_index().sort_values('Date')
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Revenue", f"₹{daily_summary['Revenue (INR)'].sum():,.0f}")
            with col2:
                st.metric("Avg Daily Revenue", f"₹{daily_summary['Revenue (INR)'].mean():,.0f}")
            with col3:
                st.metric("Peak Daily Revenue", f"₹{daily_summary['Revenue (INR)'].max():,.0f}")
            with col4:
                st.metric("Total Days", len(daily_summary))
            
            # Day-wise breakdown in column format
            st.write("### 📅 Day-wise Breakdown")
            day_wise_df = daily_summary.copy()
            day_wise_df['Day'] = [f"Day {i+1}" for i in range(len(day_wise_df))]
            day_wise_df['Date'] = day_wise_df['Date'].dt.strftime("%d-%b-%Y")
            day_wise_df['Impressions'] = day_wise_df['Impressions'].astype(int)
            day_wise_df['Revenue (₹)'] = day_wise_df['Revenue (INR)'].apply(lambda x: f"₹{x:,.0f}")
            day_wise_df['Requests'] = day_wise_df['Requests'].astype(int)
            day_wise_df['CTR%'] = day_wise_df['CTR%'].apply(lambda x: f"{x:.2f}%")
            
            display_daywise = day_wise_df[['Day', 'Date', 'Impressions', 'Revenue (₹)', 'Requests', 'CTR%']]
            st.dataframe(display_daywise, use_container_width=True)
            
            # Day-wise revenue trend
            fig3 = px.line(daily_summary, x='Date', y='Revenue (INR)',
                          title="Daily Revenue Consumption Trend", markers=True, 
                          labels={'Revenue (INR)': 'Revenue (₹)', 'Date': 'Date'})
            fig3.update_traces(line=dict(color='#1f77b4', width=3))
            st.plotly_chart(fig3, use_container_width=True)
            
            # Combined Revenue & Impressions chart
            fig4 = go.Figure()
            fig4.add_trace(go.Bar(x=daily_summary['Date'], y=daily_summary['Impressions'],
                                 name='Impressions', marker_color='lightblue', yaxis='y'))
            fig4.add_trace(go.Scatter(x=daily_summary['Date'], y=daily_summary['Revenue (INR)'],
                                     name='Revenue (₹)', mode='lines+markers', 
                                     line=dict(color='red', width=3), yaxis='y2'))
            fig4.update_layout(
                title="Daily Impressions vs Revenue",
                xaxis=dict(title='Date'),
                yaxis=dict(title='Impressions', side='left'),
                yaxis2=dict(title='Revenue (₹)', overlaying='y', side='right'),
                hovermode='x unified',
                height=500
            )
            st.plotly_chart(fig4, use_container_width=True)
            
            # Detailed day-wise table
            st.write("### Detailed Day-wise Consumption Summary")
            daily_summary['Avg Impressions'] = (daily_summary['Impressions'] / daily_summary['Requests']).round(0)
            daily_summary_display = daily_summary[['Date', 'Impressions', 'Revenue (INR)', 'Requests', 'CTR%']].copy()
            daily_summary_display.columns = ['Date', 'Impressions', 'Revenue (₹)', 'Requests', 'Avg CTR%']
            daily_summary_display['Revenue (₹)'] = daily_summary_display['Revenue (₹)'].apply(lambda x: f"₹{x:,.0f}")
            daily_summary_display['Avg CTR%'] = daily_summary_display['Avg CTR%'].apply(lambda x: f"{x:.2f}%")
            st.dataframe(daily_summary_display, use_container_width=True)
            
            st.markdown("---")
            
            # Day-wise breakdown by campaign - PIVOT FORMAT (Campaigns in rows, Dates in columns)
            st.write("### Day-wise Impressions by Campaign")
            
            # Create pivot for impressions
            impressions_pivot = daily_campaign_data.groupby(['Campaigns', 'Date'])['Impressions'].sum().reset_index()
            impressions_pivot['Date'] = impressions_pivot['Date'].dt.strftime("%d-%b-%Y")
            impressions_pivot = impressions_pivot.pivot(index='Campaigns', columns='Date', values='Impressions').fillna(0).astype(int)
            
            st.dataframe(impressions_pivot, use_container_width=True)
            
            # Download impressions pivot
            csv = impressions_pivot.reset_index().to_csv(index=False)
            st.download_button(
                label="📥 Download Impressions Pivot",
                data=csv,
                file_name="impressions_pivot.csv",
                mime="text/csv"
            )
            
            st.markdown("---")
            st.write("### Day-wise Revenue by Campaign")
            
            # Create pivot for revenue
            revenue_pivot = daily_campaign_data.groupby(['Campaigns', 'Date'])['Revenue (INR)'].sum().reset_index()
            revenue_pivot['Date'] = revenue_pivot['Date'].dt.strftime("%d-%b-%Y")
            revenue_pivot_table = revenue_pivot.pivot(index='Campaigns', columns='Date', values='Revenue (INR)').fillna(0)
            
            # Format as currency
            revenue_pivot_display = revenue_pivot_table.map(lambda x: f"₹{x:,.0f}")
            st.dataframe(revenue_pivot_display, use_container_width=True)
            
            # Download revenue pivot
            csv = revenue_pivot_table.reset_index().to_csv(index=False)
            st.download_button(
                label="📥 Download Revenue Pivot",
                data=csv,
                file_name="revenue_pivot.csv",
                mime="text/csv"
            )
            
            st.markdown("---")
            st.write("### 📢 Campaign Impressions by Publisher")
            
            # Create pivot for impressions by campaign and publisher
            campaign_publisher = filtered_df.groupby(['Campaigns', 'Publisher'])['Impressions'].sum().reset_index()
            campaign_publisher_pivot = campaign_publisher.pivot(index='Campaigns', columns='Publisher', values='Impressions').fillna(0).astype(int)
            
            st.dataframe(campaign_publisher_pivot, use_container_width=True)
            
            # Download campaign-publisher breakdown
            csv = campaign_publisher_pivot.reset_index().to_csv(index=False)
            st.download_button(
                label="📥 Download Campaign-Publisher Breakdown",
                data=csv,
                file_name="campaign_publisher_breakdown.csv",
                mime="text/csv"
            )
            
            st.markdown("---")
            st.write("### 📊 Publisher Share by Campaign (%)")
            
            # Calculate percentage share of each publisher for each campaign
            campaign_publisher_pct = campaign_publisher.copy()
            campaign_publisher_pct['Total'] = campaign_publisher_pct.groupby('Campaigns')['Impressions'].transform('sum')
            campaign_publisher_pct['Share %'] = (campaign_publisher_pct['Impressions'] / campaign_publisher_pct['Total'] * 100).round(2)
            
            pct_display = campaign_publisher_pct[['Campaigns', 'Publisher', 'Impressions', 'Share %']].sort_values(['Campaigns', 'Share %'], ascending=[True, False])
            pct_display.columns = ['Campaign', 'Publisher', 'Impressions', 'Share %']
            pct_display['Share %'] = pct_display['Share %'].apply(lambda x: f"{x:.2f}%")
            st.dataframe(pct_display, use_container_width=True)
            
            # Download publisher share percentage
            csv = campaign_publisher_pct[['Campaigns', 'Publisher', 'Impressions', 'Share %']].to_csv(index=False)
            st.download_button(
                label="📥 Download Publisher Share %",
                data=csv,
                file_name="publisher_share_percentage.csv",
                mime="text/csv"
            )
            
            # Chart: Publisher distribution by campaign
            fig_pub = px.bar(campaign_publisher_pct, x='Campaigns', y='Impressions', color='Publisher',
                            title="Campaign Impressions by Publisher", barmode='stack')
            st.plotly_chart(fig_pub, use_container_width=True)
            
            st.markdown("---")
            st.write("### 📋 Publisher Share % by Campaign (Column Format)")
            
            # Create pivot table with Publisher Share % (Campaigns in rows, Publishers in columns)
            share_pivot_data = campaign_publisher_pct[['Campaigns', 'Publisher', 'Share %']].copy()
            share_pivot = share_pivot_data.pivot(index='Campaigns', columns='Publisher', values='Share %').fillna(0)
            
            # Format as percentages
            share_pivot_display = share_pivot.map(lambda x: f"{x:.2f}%")
            st.dataframe(share_pivot_display, use_container_width=True)
            
            # Download publisher share pivot
            csv = share_pivot.reset_index().to_csv(index=False)
            st.download_button(
                label="📥 Download Publisher Share % Pivot",
                data=csv,
                file_name="publisher_share_pivot.csv",
                mime="text/csv"
            )
            
            st.markdown("---")
            
            # Pie charts for each campaign's publisher distribution
            if 'Campaigns' in filtered_df.columns and 'Publisher' in filtered_df.columns:
                st.write("### Publisher Distribution per Campaign")
                unique_campaigns_list = sorted(filtered_df['Campaigns'].unique())
                for campaign in unique_campaigns_list:
                    campaign_pub_data = campaign_publisher_pct[campaign_publisher_pct['Campaigns'] == campaign]
                    if len(campaign_pub_data) > 0:
                        fig_pie = px.pie(campaign_pub_data, values='Impressions', names='Publisher',
                                        title=f"{campaign} - Publisher Distribution")
                        st.plotly_chart(fig_pie, use_container_width=True)
            
            st.markdown("---")
            
            # Alternative view: Campaign-wise daily summary with expanders
            st.write("### Campaign-wise Daily Details")
            unique_campaigns = sorted(daily_campaign_data['Campaigns'].unique())
            for campaign in unique_campaigns:
                campaign_daily_data = daily_campaign_data[daily_campaign_data['Campaigns'] == campaign].copy()
                campaign_daily_data = campaign_daily_data.dropna(subset=['Date']).sort_values('Date')
                
                if len(campaign_daily_data) > 0:
                    with st.expander(f"📊 {campaign}"):
                        campaign_summary = campaign_daily_data.groupby('Date').agg({
                            'Impressions': 'sum',
                            'Revenue (INR)': 'sum',
                            'Requests': 'sum',
                            'Schedule Impression': 'first'
                        }).reset_index()
                        campaign_summary['Date'] = campaign_summary['Date'].dt.strftime("%d-%b-%Y")
                        campaign_summary['Impressions'] = campaign_summary['Impressions'].astype(int)
                        campaign_summary['Revenue (₹)'] = campaign_summary['Revenue (INR)'].apply(lambda x: f"₹{x:,.0f}")
                        campaign_summary['Requests'] = campaign_summary['Requests'].astype(int)
                        campaign_summary['Delivery %'] = (campaign_summary['Impressions'] / campaign_summary['Schedule Impression'].replace(0, 1) * 100).round(2).clip(upper=100)
                        
                        display_cols = campaign_summary[['Date', 'Impressions', 'Revenue (₹)', 'Requests', 'Delivery %']]
                        st.dataframe(display_cols, use_container_width=True)
            
            st.markdown("---")
    except Exception as e:
        st.error(f"Error generating Campaign Report: {str(e)}")

with tab6:
    st.subheader("📊 Raw Data Overview")
    
    st.write(f"Showing {len(filtered_df)} records out of {len(df)} total")
    
    # Show summary stats - only for columns that exist
    col1, col2, col3 = st.columns(3)
    with col1:
        if 'Campaigns' in filtered_df.columns:
            st.write(f"**Unique Campaigns:** {filtered_df['Campaigns'].nunique()}")
    with col2:
        if 'Release Order' in filtered_df.columns:
            st.write(f"**Unique Release Orders:** {filtered_df['Release Order'].nunique()}")
    with col3:
        if 'Line Item' in filtered_df.columns:
            st.write(f"**Unique Line Items:** {filtered_df['Line Item'].nunique()}")
    
    st.dataframe(filtered_df, use_container_width=True)
    
    # Download button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv,
        file_name="analytics_data.csv",
        mime="text/csv"
    )