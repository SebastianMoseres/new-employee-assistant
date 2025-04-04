# frontend/app.py
import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load env vars if needed (e.g., for BACKEND_URL if deployed)
# load_dotenv(dotenv_path='../.env')

# --- Configuration ---
# Use localhost when running backend locally.
# IMPORTANT: Update this to your deployed backend URL for Day 3!


# BACKEND_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000/ask")


BACKEND_URL = "https://onboarding-assistant-backend.onrender.com"

# --- Custom Theme Configuration ---
st.set_page_config(
    page_title="AI Onboarding Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto"
)

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #1a1a1a;
    }
    .stChatMessage {
        background-color: #2d2d2d;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .stChatMessage p, .stChatMessage div {
        color: #ffffff;
    }
    .stButton>button {
        background-color: #0d6efd;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #0b5ed7;
    }
    h1, h2, h3 {
        color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Streamlit App UI ---
st.markdown("# 🤖 AI Onboarding Assistant")
st.markdown("### Your Personal Guide to Company Policies")
st.markdown("Ask questions about **Company Policies** below.")
st.markdown("*Please be specific for best results.*")

# Add a divider
st.markdown("---")

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