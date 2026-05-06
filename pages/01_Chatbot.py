import streamlit as st
import requests
import json
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

# ============================================================================
# CHATBOT FEATURE
# ============================================================================

def get_demo_response(user_message):
    """Generate demo responses without requiring an API key"""
    message_lower = user_message.lower()
    
    demo_responses = {
        "hello|hi|hey": "Hello! 👋 I'm your Campaign Analytics Assistant. How can I help you with your campaign data today?",
        "help|what can you do": "I can help you:\n• Analyze campaign performance\n• Answer questions about your data\n• Provide insights on metrics\n• Help with campaign optimization\n\nWhat would you like to know?",
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

def query_ai(messages, api_key):
    """Query Groq API with the given messages"""
    if not api_key or api_key == "":
        # Use demo mode
        user_message = messages[-1]["content"] if messages else ""
        return get_demo_response(user_message)
    
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
    
    api_key = st.secrets.get("groq_api_key", "")
    
    try:
        # Build context for the chatbot
        context = "You are a Campaign Analytics Assistant. Answer questions briefly and concisely. Be direct."
        
        messages = [
            {"role": "system", "content": context},
        ]
        
        # Add conversation history
        for msg in st.session_state.chat_messages[:-1]:  # Exclude the current message
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        with st.spinner("🔄 Thinking..."):
            response = query_ai(messages, api_key)
        
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
