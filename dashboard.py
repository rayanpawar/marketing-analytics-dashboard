import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Page configuration
st.set_page_config(page_title="Marketing Analytics Dashboard", layout="wide")

# Title
st.title("📊 Marketing Analytics Dashboard")
st.markdown("---")

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel("Analytics.xls", sheet_name="Analytics")
    # Convert date columns properly
    for col in ['Date', 'Date Start', 'Date End']:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except:
                pass
    
    # Convert Schedule Impression and Schedule Click to numeric
    for col in ['Schedule Impression', 'Schedule Click']:
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except:
                pass
    
    return df

df = load_data()

# Display basic stats
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Records", len(df))

with col2:
    try:
        total_impressions = df['Impressions'].sum()
        st.metric("Total Impressions", f"{int(total_impressions):,}")
    except:
        st.metric("Total Impressions", "N/A")

with col3:
    try:
        total_requests = df['Requests'].sum()
        st.metric("Total Requests", f"{int(total_requests):,}")
    except:
        st.metric("Total Requests", "N/A")

with col4:
    try:
        total_revenue = df['Revenue (INR)'].sum()
        st.metric("Total Revenue", f"₹{total_revenue:,.0f}")
    except:
        st.metric("Total Revenue", "N/A")

with col5:
    try:
        avg_ctr = df['CTR%'].mean()
        st.metric("Avg CTR%", f"{avg_ctr:.2f}%")
    except:
        st.metric("Avg CTR%", "N/A")

st.markdown("---")

# Cascading Filters
st.sidebar.title("🔍 Hierarchical Filters")

# Release Order Filter
release_orders = sorted(df['Release Order'].unique())
selected_ro = st.sidebar.selectbox("📌 Release Order", ["All"] + release_orders)

# Line Item Filter (filtered by Release Order)
if selected_ro == "All":
    line_items = sorted(df['Line Item'].unique())
else:
    line_items = sorted(df[df['Release Order'] == selected_ro]['Line Item'].unique())
selected_li = st.sidebar.selectbox("📌 Line Item", ["All"] + list(line_items))

# Campaign Filter (filtered by Line Item)
if selected_li == "All":
    if selected_ro == "All":
        campaigns = sorted(df['Campaigns'].unique())
    else:
        campaigns = sorted(df[df['Release Order'] == selected_ro]['Campaigns'].unique())
else:
    campaigns = sorted(df[df['Line Item'] == selected_li]['Campaigns'].unique())
selected_campaign = st.sidebar.selectbox("📌 Campaign", ["All"] + list(campaigns))

# Status Filter
if 'Campaign Status' in df.columns:
    statuses = sorted(df['Campaign Status'].unique())
    selected_status = st.sidebar.multiselect("Status", statuses, default=statuses)
else:
    selected_status = None

# Apply filters
filtered_df = df.copy()

if selected_ro != "All":
    filtered_df = filtered_df[filtered_df['Release Order'] == selected_ro]

if selected_li != "All":
    filtered_df = filtered_df[filtered_df['Line Item'] == selected_li]

if selected_campaign != "All":
    filtered_df = filtered_df[filtered_df['Campaigns'] == selected_campaign]

if selected_status:
    filtered_df = filtered_df[filtered_df['Campaign Status'].isin(selected_status)]

# Tab navigation
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Hierarchical Drill-down", "Overview", "Release Order Report", "Line Item Report", "Campaign Report", "Raw Data"])

with tab1:
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
            st.metric("Line Items", ro_data['Line Item'].nunique())
        with col2:
            st.metric("Campaigns", ro_data['Campaigns'].nunique())
        with col3:
            st.metric("Total Impressions", f"{ro_data['Impressions'].sum():,}")
        with col4:
            st.metric("Total Revenue", f"₹{ro_data['Revenue (INR)'].sum():,.0f}")
        with col5:
            st.metric("Avg CTR%", f"{ro_data['CTR%'].mean():.2f}%")
        
        st.markdown("---")
        
        # Line Item Level Breakdown
        st.write("### 📋 Line Items in this Release Order")
        li_breakdown = ro_data.groupby('Line Item').agg({
            'Campaigns': 'nunique',
            'Impressions': 'sum',
            'Requests': 'sum',
            'Revenue (INR)': 'sum',
            'CTR%': 'mean'
        }).reset_index().sort_values('Impressions', ascending=False)
        
        li_breakdown.columns = ['Line Item', 'Campaigns Count', 'Impressions', 'Requests', 'Revenue (₹)', 'Avg CTR%']
        li_breakdown['Revenue (₹)'] = li_breakdown['Revenue (₹)'].apply(lambda x: f"₹{x:,.0f}")
        li_breakdown['Avg CTR%'] = li_breakdown['Avg CTR%'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(li_breakdown, use_container_width=True)
        
        st.markdown("---")
        
        # Campaign Level Breakdown (if Line Item selected)
        if selected_li != "All":
            st.write(f"### 🎯 Campaigns in {selected_li}")
            campaign_breakdown = ro_data[ro_data['Line Item'] == selected_li].groupby('Campaigns').agg({
                'Impressions': 'sum',
                'Requests': 'sum',
                'Revenue (INR)': 'sum',
                'CTR%': 'mean',
                'Schedule Impression': 'first'
            }).reset_index().sort_values('Impressions', ascending=False)
            
            campaign_breakdown['Delivery %'] = (campaign_breakdown['Impressions'] / campaign_breakdown['Schedule Impression'].replace(0, 1) * 100).round(2)
            campaign_breakdown.columns = ['Campaign', 'Impressions', 'Requests', 'Revenue (₹)', 'Avg CTR%', 'Scheduled', 'Delivery %']
            campaign_breakdown['Revenue (₹)'] = campaign_breakdown['Revenue (₹)'].apply(lambda x: f"₹{x:,.0f}")
            campaign_breakdown['Avg CTR%'] = campaign_breakdown['Avg CTR%'].apply(lambda x: f"{x:.2f}%")
            campaign_breakdown['Delivery %'] = campaign_breakdown['Delivery %'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(campaign_breakdown, use_container_width=True)
        else:
            st.write("### 🎯 Select a Line Item to see Campaign Details")
            # Show all campaigns under RO grouped by Line Item
            all_campaigns = ro_data.groupby(['Line Item', 'Campaigns']).agg({
                'Impressions': 'sum',
                'Revenue (INR)': 'sum',
                'CTR%': 'mean'
            }).reset_index().sort_values(['Line Item', 'Impressions'], ascending=[True, False])
            
            all_campaigns.columns = ['Line Item', 'Campaign', 'Impressions', 'Revenue (₹)', 'Avg CTR%']
            all_campaigns['Revenue (₹)'] = all_campaigns['Revenue (₹)'].apply(lambda x: f"₹{x:,.0f}")
            all_campaigns['Avg CTR%'] = all_campaigns['Avg CTR%'].apply(lambda x: f"{x:.2f}%")
            
            st.dataframe(all_campaigns, use_container_width=True)

with tab2:
    st.subheader("� Performance Metrics")
    
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
            revenue_pivot_display = revenue_pivot_table.applymap(lambda x: f"₹{x:,.0f}")
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
    
    # Show summary stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Unique Campaigns:** {filtered_df['Campaigns'].nunique()}")
    with col2:
        st.write(f"**Unique Release Orders:** {filtered_df['Release Order'].nunique()}")
    with col3:
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