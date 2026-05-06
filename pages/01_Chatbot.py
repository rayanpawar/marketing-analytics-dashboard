import streamlit as st
import requests
import json
import pandas as pd
from urllib.request import Request, urlopen
from urllib.error import URLError

# Page configuration
st.set_page_config(page_title="AI Chatbot", layout="wide")

st.title("🤖 Campaign AI Assistant")

# Password Protection (same as main dashboard)
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
        st.warning("🔐 This chatbot contains confidential data. Please enter the password to proceed.")
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

# Load data from uploaded file if available
def load_uploaded_file(uploaded_file, sheet_name="Analytics"):
    """Load a single uploaded Excel file"""
    try:
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
        return df
    except Exception as e:
        return None

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

def get_data_summary(df):
    """Generate a summary of the current data"""
    if df is None or len(df) == 0:
        return ""
    
    summary = f"""
**📊 Your Current Campaign Data:**
- Records: {len(df):,}
"""
    
    if 'Impressions' in df.columns:
        summary += f"- Total Impressions: {df['Impressions'].sum():,.0f}\n"
    
    if 'Requests' in df.columns:
        summary += f"- Total Requests: {df['Requests'].sum():,.0f}\n"
    
    if 'Revenue (INR)' in df.columns:
        summary += f"- Total Revenue: ₹{df['Revenue (INR)'].sum():,.0f}\n"
    
    if 'CTR%' in df.columns:
        summary += f"- Avg CTR: {df['CTR%'].mean():.2f}%\n"
    
    # Calculate Pacing (Impression Pacing)
    if 'Impressions' in df.columns and 'Schedule Impression' in df.columns:
        total_impressions = df['Impressions'].sum()
        total_scheduled = df['Schedule Impression'].sum()
        if total_scheduled > 0:
            pacing = (total_impressions / total_scheduled) * 100
            summary += f"- Impression Pacing: {pacing:.1f}%\n"
    
    # Calculate Budget Pacing if available
    if 'Campaign Budget' in df.columns and 'Revenue (INR)' in df.columns:
        total_budget = df['Campaign Budget'].sum()
        total_revenue = df['Revenue (INR)'].sum()
        if total_budget > 0:
            budget_pacing = (total_revenue / total_budget) * 100
            summary += f"- Budget Pacing (Revenue/Budget): {budget_pacing:.1f}%\n"
    
    if 'ReleaseOrderId' in df.columns:
        summary += f"- Unique Release Orders: {df['ReleaseOrderId'].nunique()}\n"
    
    if 'Campaigns' in df.columns:
        summary += f"- Unique Campaigns: {df['Campaigns'].nunique()}\n"
    
    if 'Publisher' in df.columns:
        summary += f"- Unique Publishers: {df['Publisher'].nunique()}\n"
    
    # Add pacing details by campaign
    if 'Campaigns' in df.columns and 'Impressions' in df.columns and 'Schedule Impression' in df.columns:
        pacing_by_campaign = df.groupby('Campaigns', as_index=False).agg({
            'Impressions': 'sum',
            'Schedule Impression': 'sum'
        })
        pacing_by_campaign['Pacing%'] = (pacing_by_campaign['Impressions'] / pacing_by_campaign['Schedule Impression'] * 100).round(1)
        
        summary += f"\n**Campaign Pacing Details:**\n"
        for _, row in pacing_by_campaign.head(5).iterrows():
            summary += f"  • {row['Campaigns']}: {row['Pacing%']:.1f}% ({int(row['Impressions']):,} / {int(row['Schedule Impression']):,})\n"
    
    return summary

def get_daily_goals_table(df):
    """Generate a table with per-day goals based on campaign dates and scheduled impressions"""
    if df is None or len(df) == 0:
        return None
    
    # Check for required columns
    required_cols = ['Campaigns', 'Schedule Impression']
    date_cols = ['Date Start', 'Date End', 'Date', 'Start Date', 'End Date']
    
    # Find which date columns exist
    start_col = None
    end_col = None
    
    for col in date_cols:
        if col in df.columns:
            if 'start' in col.lower():
                start_col = col
            elif 'end' in col.lower():
                end_col = col
    
    # If we don't have both date columns, return None
    if start_col is None or end_col is None:
        return None
    
    try:
        daily_goals = df[['Campaigns', start_col, end_col, 'Schedule Impression']].copy()
        daily_goals.columns = ['Campaign', 'Start Date', 'End Date', 'Scheduled Impressions']
        
        # Convert to datetime
        daily_goals['Start Date'] = pd.to_datetime(daily_goals['Start Date'], errors='coerce')
        daily_goals['End Date'] = pd.to_datetime(daily_goals['End Date'], errors='coerce')
        
        # Convert Scheduled Impressions to numeric
        daily_goals['Scheduled Impressions'] = pd.to_numeric(daily_goals['Scheduled Impressions'], errors='coerce')
        
        # Calculate days
        daily_goals['Days'] = (daily_goals['End Date'] - daily_goals['Start Date']).dt.days + 1
        
        # Remove rows with invalid data
        daily_goals = daily_goals[
            (daily_goals['Days'] > 0) & 
            (daily_goals['Start Date'].notna()) & 
            (daily_goals['End Date'].notna()) & 
            (daily_goals['Scheduled Impressions'].notna()) &
            (daily_goals['Scheduled Impressions'] > 0)
        ].copy()
        
        if len(daily_goals) == 0:
            return None
        
        # Calculate per day goal using nullable integer
        daily_goals['Per Day Goal'] = (daily_goals['Scheduled Impressions'] / daily_goals['Days']).round(0).astype('Int64')
        
        # Format for display
        daily_goals['Start Date'] = daily_goals['Start Date'].dt.strftime('%Y-%m-%d')
        daily_goals['End Date'] = daily_goals['End Date'].dt.strftime('%Y-%m-%d')
        daily_goals['Scheduled Impressions'] = daily_goals['Scheduled Impressions'].apply(lambda x: f"{int(x):,}")
        daily_goals['Per Day Goal'] = daily_goals['Per Day Goal'].apply(lambda x: f"{x:,}")
        
        return daily_goals
    except Exception as e:
        return None

# ============================================================================
# CHATBOT FEATURE
# ============================================================================

def get_demo_response(user_message):
    """Generate demo responses without requiring an API key"""
    message_lower = user_message.lower()
    
    demo_responses = {
        "pacing": "📊 **Pacing** measures how well your campaigns are delivering against their schedule:\n\n• **Impression Pacing** = (Actual Impressions / Scheduled Impressions) × 100%\n• **Budget Pacing** = (Actual Revenue / Total Budget) × 100%\n\nFor example:\n- 100% = On track ✅\n- >100% = Ahead of schedule 🚀\n- <100% = Behind schedule ⚠️",
        "daily goal|per day|day goals": "📅 **Per Day Goals** show how many impressions you need per day to meet your schedule:\n\n• **Per Day Goal** = Scheduled Impressions ÷ Campaign Duration (days)\n\nThis helps track if you're hitting daily targets to stay on schedule.",
        "hello|hi|hey": "Hello! 👋 I'm your Campaign Analytics Assistant. How can I help you with your campaign data today?",
        "help|what can you do": "I can help you:\n• Analyze campaign performance\n• Answer questions about your data\n• Provide insights on metrics\n• Calculate pacing and delivery metrics\n• Show per-day impression goals\n\nWhat would you like to know?",
        "performance|metrics|data": "To get insights on your campaign performance, please upload your Excel file in the main dashboard page first. Then I can help analyze your data! 📊",
        "budget|roi|revenue": "I can help you analyze budget allocation, ROI, and revenue metrics once you upload your campaign data.",
        "thank": "You're welcome! Feel free to ask me anything else about your campaigns! 😊",
    }
    
    # Check for keyword matches
    for keywords, response in demo_responses.items():
        for keyword in keywords.split("|"):
            if keyword in message_lower:
                return response
    
    # Default response
    return "I'm in demo mode right now. To get full AI-powered responses, please add a Groq API key to your Streamlit secrets. For now, I can help guide you through the dashboard features! 📊\n\nWhat would you like to know?"

def query_ai(messages, api_key, data_context=""):
    """Query Groq API with the given messages and data context"""
    # If no API key and no data context, use demo mode
    if (not api_key or api_key == "") and not data_context:
        user_message = messages[-1]["content"] if messages else ""
        return get_demo_response(user_message)
    
    # If no API key but we have data, inform user
    if not api_key or api_key == "":
        return "⚠️ No Groq API key configured. Please add your Groq API key to Streamlit secrets to enable AI-powered analysis. For now, please use the dashboard charts for analysis."
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return f"⚠️ Unexpected API response format"
        else:
            error_detail = response.json().get('error', {}).get('message', response.text)
            if response.status_code == 401:
                return "❌ Authentication failed: Invalid Groq API key. Please check your key in Streamlit secrets."
            elif response.status_code == 429:
                return "⚠️ Rate limited: Too many requests. Please try again in a moment."
            elif response.status_code == 400:
                return f"❌ Request error: {error_detail[:100]}"
            else:
                return f"⚠️ API returned error {response.status_code}. Please try again."
    
    except requests.exceptions.ConnectionError:
        return "⚠️ Connection failed: Unable to reach Groq. Check your internet connection or try again later."
    except requests.exceptions.Timeout:
        return "⚠️ Timeout: Groq took too long to respond. Please try again."
    except requests.exceptions.RequestException as e:
        return f"⚠️ Request error: {str(e)[:80]}"
    except json.JSONDecodeError:
        return "⚠️ Invalid response from Groq API. Service may be experiencing issues."
    except Exception as e:
        return f"⚠️ Unexpected error: {str(e)[:80]}"

# Initialize chatbot session state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "dashboard_data" not in st.session_state:
    st.session_state.dashboard_data = None

# Ensure uploaded_files reference from dashboard
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = None

st.markdown("---")

# Display instructions
st.info("💡 Ask me anything about your campaigns! I'm here to help you analyze campaign data and answer your questions.")

# Load data from dashboard if available
if st.session_state.uploaded_files is not None:
    try:
        sheet_name = st.session_state.get("sheet_name", "Analytics")
        df = load_uploaded_file(st.session_state.uploaded_files, sheet_name)
        
        if df is not None:
            # Process date and numeric columns
            date_cols = st.session_state.get("date_columns", [])
            numeric_cols = st.session_state.get("numeric_columns", [])
            df = process_data(df, date_cols, numeric_cols)
            st.session_state.dashboard_data = df
            
            # Show data summary in expander
            with st.expander("📊 Data Summary"):
                summary = get_data_summary(df)
                st.write(summary)
                st.success(f"✅ Using data from: {st.session_state.uploaded_files.name}")
                
                # Show daily goals table if available
                st.markdown("---")
                st.write("#### 📅 Per-Day Impression Goals")
                daily_goals_df = get_daily_goals_table(df)
                if daily_goals_df is not None and len(daily_goals_df) > 0:
                    st.dataframe(daily_goals_df, use_container_width=True)
                    st.info("💡 **Per Day Goal** = Scheduled Impressions ÷ Campaign Duration. This shows your daily impression target to stay on schedule.")
        else:
            st.warning("⚠️ Could not load data from the uploaded file. Check the sheet name and try again.")
    except Exception as e:
        st.warning(f"⚠️ Error loading data: {str(e)}")
else:
    st.info("📁 **No data uploaded yet.** Upload a file in the main **Dashboard** page first to enable data-aware AI responses.")
    st.write("Steps:")
    st.write("1. Go to the **Dashboard** page")
    st.write("2. Upload your Excel file")
    st.write("3. Configure the sheet and columns")
    st.write("4. Return to this **Chatbot** page")

# Display chat history
for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
user_input = st.chat_input("Ask me anything about your campaigns...")

if user_input:
    # Add user message to history
    st.session_state.chat_messages.append({"role": "user", "content": user_input})

# Generate response if last message is from user (unresponded)
if len(st.session_state.chat_messages) > 0 and st.session_state.chat_messages[-1]["role"] == "user":
    api_key = st.secrets.get("groq_api_key", "")
    
    try:
        # Build system context with actual data insights
        if st.session_state.dashboard_data is not None and len(st.session_state.dashboard_data) > 0:
            df = st.session_state.dashboard_data
            
            # Create detailed data context
            context = """You are a Campaign Analytics Expert. Analyze the provided campaign data and answer questions accurately and concisely.

**Your capabilities:**
- Analyze revenue, impressions, requests, CTR metrics
- Calculate and explain pacing metrics (Actual vs Scheduled)
- Show per-day impression goals (Scheduled Impressions ÷ Campaign Days)
- Compare publisher and campaign performance
- Identify trends and provide recommendations

**Important:** ONLY use the provided data to answer questions. If asked about data that doesn't exist in the dataset, clearly state that."""
            
            # Add data summary
            data_summary = get_data_summary(df)
            context += f"\n\n{data_summary}"
            
            # Add daily goals info if available
            daily_goals_df = get_daily_goals_table(df)
            if daily_goals_df is not None and len(daily_goals_df) > 0:
                context += f"\n\n**Per-Day Goals Available:**\nCampaigns have start/end dates and scheduled impressions. Per-day goals = Scheduled Impressions ÷ Campaign Days."
            
            # Add column info
            context += f"\n\n**Available Columns:** {', '.join(df.columns.tolist())}"
        else:
            context = "You are a Campaign Analytics Assistant. No data has been uploaded yet. Guide users to upload their Excel file in the Dashboard page first."
        
        messages = [
            {"role": "system", "content": context},
        ]
        
        # Add conversation history
        for msg in st.session_state.chat_messages:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        with st.spinner("🔄 Analyzing your data..."):
            response = query_ai(messages, api_key, data_summary if st.session_state.dashboard_data is not None else "")
        
        # Add assistant response to history
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        
        # Rerun to display the response
        st.rerun()
    
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})

# Add clear chat button in sidebar
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.chat_messages = []
    st.rerun()
