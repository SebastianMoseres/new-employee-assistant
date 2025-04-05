# frontend/app.py
import streamlit as st
import requests
import os

# --- Page Configuration (MUST be the first Streamlit command) ---
st.set_page_config(
    page_title="AI Onboarding Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Configuration ---
# Use secrets for deployed URL, fallback to local for development
BACKEND_BASE_URL = st.secrets.get("BACKEND_API_URL_BASE", "http://127.0.0.1:8000")

# Construct specific endpoint URLs from the base URL
ASK_ENDPOINT = f"{BACKEND_BASE_URL}/ask"
CONTEXT_ENDPOINT = f"{BACKEND_BASE_URL}/context"

# --- Helper Function to Fetch Context (Returns string or error string) ---
def fetch_context_from_backend():
    """Fetches context from backend, returns context string or error message string."""
    try:
        response = requests.get(CONTEXT_ENDPOINT, timeout=15)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        return data.get("context", "Error: Backend response missing 'context' key.")
    except requests.exceptions.Timeout:
        print("ERROR fetching context: Request timed out")
        return "Error: Request to backend timed out."
    except requests.exceptions.RequestException as e:
        print(f"ERROR fetching context: {e}")
        return f"Error: Could not connect to backend ({e})"
    except Exception as e:
        print(f"ERROR fetching context (unexpected): {e}")
        return f"Error: Unexpected issue fetching context ({e})"

# --- Initialize Session State for Context (Fetch only once per session)---
if 'company_context' not in st.session_state:
    print("Initializing session state 'company_context', fetching...")
    st.session_state.company_context = fetch_context_from_backend()
    # Log first 100 chars or the error
    log_value = st.session_state.company_context
    print(f"Fetched context into session state: {log_value[:100]}{'...' if len(log_value) > 100 else ''}")

# --- Sidebar for Context Management ---
st.sidebar.title("⚙️ Manage Context")
st.sidebar.caption("Paste the full company context document here.")

# Determine value for text_area based on fetched state
context_error_message = None
if isinstance(st.session_state.company_context, str) and st.session_state.company_context.startswith("Error:"):
    context_error_message = st.session_state.company_context
    context_display_value = "" # Show empty text area if fetch failed
else:
    context_display_value = st.session_state.company_context # Use good context

# Display warning only if there was an error during the fetch
if context_error_message:
    st.sidebar.warning(context_error_message)

new_context_input = st.sidebar.text_area(
    "Company Context:",
    value=context_display_value,
    height=400,
    key="context_editor"
)

if st.sidebar.button("Update Context"):
    if new_context_input:
        try:
            st.sidebar.info("Updating context...")
            payload = {"new_context": new_context_input}
            response = requests.post(CONTEXT_ENDPOINT, json=payload, timeout=20)
            response.raise_for_status() # Check for HTTP errors
            # Assume success if no error raised
            st.sidebar.success("Context updated successfully!")
            # Update session state immediately
            st.session_state.company_context = new_context_input
            st.rerun() # Rerun to update text_area and potentially main chat if context changed
        except requests.exceptions.Timeout:
             st.sidebar.error("Error: Request to update context timed out.")
        except requests.exceptions.RequestException as e:
            st.sidebar.error(f"Error updating context: {e}")
        except Exception as e:
             st.sidebar.error(f"An unexpected error occurred during update: {e}")
    else:
        st.sidebar.warning("Context cannot be empty.")

st.sidebar.markdown("---")

# --- Custom CSS ---
st.markdown("""
    <style>
    /* Your fixed CSS here (ensure h1 gradient is removed) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); min-height: 100vh; }
    .stChatMessage { background-color: rgba(45, 45, 45, 0.8); backdrop-filter: blur(10px); border-radius: 15px; padding: 1.2rem; margin: 0.8rem 0; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); transition: transform 0.2s ease; }
    .stChatMessage:hover { transform: translateY(-2px); }
    .stChatMessage p, .stChatMessage div { color: #ffffff; line-height: 1.6; }
    .stButton>button { background: linear-gradient(135deg, #0d6efd 0%, #0b5ed7 100%); color: white; border-radius: 8px; padding: 0.7rem 1.5rem; border: none; font-weight: 500; transition: all 0.3s ease; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3); }
    h1, h2, h3 { color: #ffffff; font-weight: 700; margin-bottom: 1rem; }
    h1 { font-size: 2.5rem; color: #ffffff; margin-bottom: 0.5rem; } /* Fixed h1 for icons */
    h2 { font-size: 1.8rem; color: #e0e0e0; }
    .stTextInput>div>div>input { background-color: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 8px; color: white; padding: 0.8rem 1rem; }
    .stTextInput>div>div>input:focus { border-color: #0d6efd; box-shadow: 0 0 0 2px rgba(13, 110, 253, 0.25); }
    .stSpinner>div { border-color: #0d6efd; }
    .stMarkdown { margin-bottom: 1.5rem; }
    .stMarkdown p { color: #e0e0e0; line-height: 1.6; }
    .stMarkdown strong { color: #ffffff; }
    .stMarkdown em { color: #a0a0a0; }
    .stylish-divider { height: 2px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent); margin: 2rem 0; }
    </style>
    """, unsafe_allow_html=True)

# --- Streamlit App UI ---
st.markdown("# 🤖 AI Onboarding Assistant")
st.markdown("### Your Personal Guide to Company Policies")
st.markdown("Ask questions about **Company Policies** below.")
st.markdown("*Please be specific for best results.*")

st.markdown('<div class="stylish-divider"></div>', unsafe_allow_html=True)

# Initialize chat history if needed
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get user input
user_question = st.chat_input("What is your question?")

if user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    # Get AI answer from backend
    try:
        with st.spinner("Thinking..."):
            # Use the correct ASK_ENDPOINT variable
            response = requests.post(ASK_ENDPOINT, json={"question": user_question}, timeout=45)
            response.raise_for_status() # Check for 4xx/5xx errors

        ai_response = response.json()
        ai_answer = ai_response.get("answer", "Sorry, I couldn't get an answer.")

        st.session_state.messages.append({"role": "assistant", "content": ai_answer})
        with st.chat_message("assistant"):
            st.markdown(ai_answer)

    except requests.exceptions.Timeout:
         error_message = "Sorry, the request to the AI service timed out. Please try again."
         st.error(error_message)
         if not st.session_state.messages or st.session_state.messages[-1].get("content") != error_message:
            st.session_state.messages.append({"role": "assistant", "content": error_message})
            # We display the error directly with st.error, no need to add to chat message again here

    except requests.exceptions.RequestException as e:
        error_message = f"Sorry, I couldn't connect to the AI service. Error: {e}"
        st.error(error_message)
        if not st.session_state.messages or st.session_state.messages[-1].get("content") != error_message:
            st.session_state.messages.append({"role": "assistant", "content": error_message})

    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        st.error(error_message)
        if not st.session_state.messages or st.session_state.messages[-1].get("content") != error_message:
            st.session_state.messages.append({"role": "assistant", "content": error_message})

# Clear Chat History Button
if st.button("Clear Chat History"):
    st.session_state.messages = []
    st.rerun()