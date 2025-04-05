# backend/main.py
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file (only affects local run)
load_dotenv(dotenv_path='../.env')

# --- Environment Variables & Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") # Use SERVICE_ROLE key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Validate essential variables
if not all([GOOGLE_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("Missing required environment variables (Google Key, Supabase URL/Key)")

# --- Initialize Clients ---
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Configure Gemini client (ensure transport='rest' if needed, usually not required)
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    raise RuntimeError(f"Failed to initialize clients: {e}")

# --- FastAPI App ---
app = FastAPI()

# --- CORS Configuration ---
origins = [
    "http://localhost",
    "http://localhost:8501",
    "https://new-employee-assistant.streamlit.app", # Your deployed frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class QuestionRequest(BaseModel):
    question: str

class ContextUpdateRequest(BaseModel):
    new_context: str

# --- API Endpoints ---
@app.get("/")
async def root():
    return {"message": "Onboarding Assistant API is running!"}

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    user_question = request.question
    print(f"Received question: {user_question}")

    if not user_question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    current_context = "Default context: No specific company context was loaded from the database." # Default

    try:
        # Fetch context reliably, targeting id=1 as set by upsert
        response = supabase.table('company_context').select('content').eq('id', 1).single().execute()
        print(f"DEBUG: Context fetch response object: {response}") # Debug print

        # Check response structure carefully
        if response.data and isinstance(response.data, dict) and 'content' in response.data:
            current_context = response.data['content']
            print("DEBUG: Successfully extracted context from DB.")
        else:
            print(f"WARN: Context data not found or in unexpected format in /ask. Data: {response.data if hasattr(response, 'data') else 'N/A'}")
    except Exception as db_error:
        print(f"ERROR: Exception fetching context for /ask: {db_error}. Using default.")

    try:
        # Construct the prompt using the fetched context
        prompt = f"""
        You are an AI onboarding assistant for a new employee.
        Answer the following question based *only* on the provided company context below.
        If the answer cannot be found in the context, clearly state that you don't have that information based on the provided documents.

        Company Context:
        ---
        {current_context}
        ---

        Question: {user_question}

        Answer:
        """
        # Choose the Gemini model (ensure this model name is available/correct)
        model = genai.GenerativeModel('gemini-1.5-pro') # Or 'gemini-1.0-pro'

        ai_response = model.generate_content(prompt)
        ai_answer = ai_response.text.strip()

        # Log question and answer to Supabase qa_log table
        try:
            log_res = supabase.table('qa_log').insert({
                "question": user_question,
                "answer": ai_answer
            }).execute()
            # Optional: Check log_res if needed
        except Exception as db_log_error:
            print(f"Error logging Q&A to Supabase: {db_log_error}")

        return {"answer": ai_answer}

    except Exception as e:
        # Catch errors during Gemini call or other processing
        print(f"Error processing question with AI: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred processing the question: {e}")

@app.get("/context")
async def get_context():
    try:
        # Fetch context reliably, targeting id=1
        response = supabase.table('company_context').select('content').eq('id', 1).single().execute()
        print(f"DEBUG (/context GET): Supabase context fetch response: {response}") # Debug print

        if response.data and isinstance(response.data, dict) and 'content' in response.data:
            return {"context": response.data['content']}
        else:
            print("WARN (/context GET): Context data not found or in unexpected format.")
            return {"context": "No company context has been set yet."}
    except Exception as e:
        print(f"ERROR (/context GET): Exception fetching context: {e}")
        raise HTTPException(status_code=500, detail=f"Could not fetch context: {e}")

@app.post("/context")
async def update_context(request: ContextUpdateRequest):
    new_content = request.new_context
    if not new_content:
        raise HTTPException(status_code=400, detail="New context cannot be empty")

    try:
        # Upsert ensures row with id=1 is created or updated
        response = supabase.table('company_context').upsert({'id': 1, 'content': new_content}).execute()
        print(f"Context update response: {response}") # Debug print

        # Optional: Add basic check for success, though upsert might not return useful count
        # if response.data: # Or check status code if available/needed
        print(f"Context updated/upserted successfully.")
        return {"message": "Context updated successfully"}
        # else:
        #     print(f"WARN: Context update might not have completed as expected. Response: {response}")
        #     raise HTTPException(status_code=500, detail="Failed to update context, response indicates issue.")

    except Exception as e:
        print(f"ERROR (/context POST): Exception updating context: {e}")
        raise HTTPException(status_code=500, detail=f"Could not update context: {e}")

# Note: Optional /history endpoint remains unchanged if you kept it.