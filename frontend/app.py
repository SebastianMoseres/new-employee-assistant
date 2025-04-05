# frontend/app.py
import streamlit as st
import requests
import os
# from dotenv import load_dotenv

# Load env vars if needed (e.g., for BACKEND_URL if deployed)
# load_dotenv(dotenv_path='../.env')

# --- Configuration ---
# Use localhost when running backend locally.

st.set_page_config(
    page_title="AI Onboarding Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto"
)

# BACKEND_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000/ask")
BACKEND_BASE_URL = st.secrets.get("BACKEND_API_URL_BASE", "http://127.0.0.1:8000")

# Construct *all* specific endpoints from the base URL
ASK_ENDPOINT = f"{BACKEND_BASE_URL}/ask"
CONTEXT_ENDPOINT = f"{BACKEND_BASE_URL}/context"

# --- Helper Function to Get Context ---
def get_current_context():
    try:
        # Use the correctly constructed CONTEXT_ENDPOINT
        response = requests.get(CONTEXT_ENDPOINT, timeout=10)
        response.raise_for_status()
        return response.json().get("context", "Error fetching context.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching current context: {e}")
        return "Could not fetch context from server."
    except Exception as e:
        st.error(f"An unexpected error occurred fetching context: {e}")
        return "Error fetching context."


# --- Sidebar for Context Management ---
st.sidebar.title("⚙️ Manage Context")
st.sidebar.caption("Paste the full company context document here.")

current_context_from_db = get_current_context() # Fetch context on load/reload

if current_context_from_db.startswith("Error:"):
    st.sidebar.warning(current_context_from_db) # Display warning in sidebar
    context_value_for_textarea = "" # Provide empty default for text area
else:
    context_value_for_textarea = current_context_from_db

new_context_input = st.sidebar.text_area(
    "Company Context:",
    value=context_value_for_textarea,
    height=400,
    key="context_editor" # Use a key to maintain state if needed
)

if st.sidebar.button("Update Context"):
    if new_context_input:
        try:
            payload = {"new_context": new_context_input}
            response = requests.post(CONTEXT_ENDPOINT, json=payload, timeout=20)
            response.raise_for_status()
            st.sidebar.success("Context updated successfully!")
            # Optional: Rerun to refresh the text area immediately, though Streamlit might do it
            # st.experimental_rerun() # Use st.rerun() in newer Streamlit versions
            st.rerun()
        except requests.exceptions.RequestException as e:
            st.sidebar.error(f"Error updating context: {e}")
        except Exception as e:
             st.sidebar.error(f"An unexpected error occurred: {e}")
    else:
        st.sidebar.warning("Context cannot be empty.")

st.sidebar.markdown("---") # Separator

# --- Custom Theme Configuration ---


# Custom CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        min-height: 100vh;
    }
    
    .stChatMessage {
        background-color: rgba(45, 45, 45, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease;
    }
    
    .stChatMessage:hover {
        transform: translateY(-2px);
    }
    
    .stChatMessage p, .stChatMessage div {
        color: #ffffff;
        line-height: 1.6;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #0d6efd 0%, #0b5ed7 100%);
        color: white;
        border-radius: 8px;
        padding: 0.7rem 1.5rem;
        border: none;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    }
    
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    h1 {
        font-size: 2.5rem;
        background: linear-gradient(135deg, #ffffff 0%, #a0a0a0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    h2 {
        font-size: 1.8rem;
        color: #e0e0e0;
    }
    
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        color: white;
        padding: 0.8rem 1rem;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #0d6efd;
        box-shadow: 0 0 0 2px rgba(13, 110, 253, 0.25);
    }
    
    .stSpinner>div {
        border-color: #0d6efd;
    }
    
    .stMarkdown {
        margin-bottom: 1.5rem;
    }
    
    .stMarkdown p {
        color: #e0e0e0;
        line-height: 1.6;
    }
    
    .stMarkdown strong {
        color: #ffffff;
    }
    
    .stMarkdown em {
        color: #a0a0a0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Streamlit App UI ---
st.markdown("# 🤖 AI Onboarding Assistant")
st.markdown("### Your Personal Guide to Company Policies")
st.markdown("Ask questions about **Company Policies** below.")
st.markdown("*Please be specific for best results.*")

# Add a stylish divider
st.markdown("""
    <div style="height: 2px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent); margin: 2rem 0;"></div>
    """, unsafe_allow_html=True)

# Initialize chat history in session state if it doesn't exist
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get user input
user_question = st.chat_input("What is your question?")

if user_question:
    # Add user message to chat history and display it
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    # Get AI answer from backend
    try:
        with st.spinner("Thinking..."):
            response = requests.post(BACKEND_URL, json={"question": user_question}, timeout=45) # Increased timeout
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        ai_response = response.json()
        ai_answer = ai_response.get("answer", "Sorry, I couldn't get an answer.")

        # Add AI message to chat history and display it
        st.session_state.messages.append({"role": "assistant", "content": ai_answer})
        with st.chat_message("assistant"):
            st.markdown(ai_answer)

    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the backend: {e}")
        st.session_state.messages.append({"role": "assistant", "content": f"Sorry, I couldn't connect to the AI service. Error: {e}"})
        with st.chat_message("assistant"):
             st.markdown(f"Sorry, I couldn't connect to the AI service. Error: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        st.session_state.messages.append({"role": "assistant", "content": f"An unexpected error occurred: {e}"})
        with st.chat_message("assistant"):
             st.markdown(f"An unexpected error occurred: {e}")

# Optional: Add a button to clear history
if st.button("Clear Chat History"):
    st.session_state.messages = []
    st.rerun() # Rerun the app to reflect the change