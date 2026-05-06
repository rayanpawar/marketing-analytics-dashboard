import streamlit as st
import requests

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

# ============================================================================
# CHATBOT FEATURE
# ============================================================================

def query_openrouter(messages, api_key):
    """Query OpenRouter API with the given messages"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://campaign-analytics-dashboard.streamlit.app",
        "X-Title": "Campaign Analytics Dashboard - Chatbot",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(
            "https://openrouter.io/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30,
            verify=True
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return f"API Error {response.status_code}: {response.text}"
    
    except requests.exceptions.ConnectionError as e:
        return "⚠️ Connection error: Unable to reach OpenRouter API. Please check your internet connection or try again later."
    except requests.exceptions.Timeout:
        return "⚠️ Request timeout: The API took too long to respond. Please try again."
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# Initialize chatbot session state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

st.markdown("---")

# Display instructions
st.info("💡 Ask me anything about your campaigns! I'm here to help you analyze campaign data and answer your questions.")

# Display chat history
for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
user_input = st.chat_input("Ask me anything about your campaigns...")

if user_input:
    # Add user message to history
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Prepare context and messages for API
    api_key = st.secrets.get("openrouter_api_key", "")
    
    if not api_key:
        error_msg = "❌ OpenRouter API key not configured. Please add `openrouter_api_key` to your Streamlit secrets."
        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
        with st.chat_message("assistant"):
            st.error(error_msg)
    else:
        try:
            # Build context for the chatbot
            context = "You are a Campaign Analytics Assistant. Help answer questions about campaign performance data, metrics, trends, and insights. Be concise and professional."
            
            messages = [
                {"role": "system", "content": context},
            ]
            
            # Add conversation history
            for msg in st.session_state.chat_messages[:-1]:  # Exclude the current message
                messages.append({"role": msg["role"], "content": msg["content"]})
            
            with st.spinner("🔄 Thinking..."):
                response = query_openrouter(messages, api_key)
            
            # Add assistant response to history
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            
            with st.chat_message("assistant"):
                st.markdown(response)
        
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
            with st.chat_message("assistant"):
                st.error(error_msg)

# Add clear chat button in sidebar
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.chat_messages = []
    st.rerun()
