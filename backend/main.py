# backend/main.py
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware # Import CORS
from pydantic import BaseModel
# from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv
import google.generativeai as genai


# Load environment variables from .env file
load_dotenv(dotenv_path='../.env') # Adjust path if .env is elsewhere

# --- Environment Variables & Configuration ---
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# genai.configure(api_key=GOOGLE_API_KEY, transport='rest')

if not all([GOOGLE_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("Missing required environment variables (OpenAI Key, Supabase URL/Key)")

# --- Initialize Clients ---
try:
    # openai_client = OpenAI(api_key=OPENAI_API_KEY)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    genai.configure(api_key=GOOGLE_API_KEY, transport='rest')
except Exception as e:
    raise RuntimeError(f"Failed to initialize clients: {e}")

# --- FastAPI App ---
app = FastAPI()

# --- CORS Configuration ---
# Allow requests from Streamlit local dev and deployed app (adjust if needed)
origins = [
    "http://localhost",
    "http://localhost:8501", # Default Streamlit port
    # Add your Streamlit Cloud app URL here when deployed
    # e.g., "https://your-streamlit-app-name.streamlit.app" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specified origins
    allow_credentials=True,
    allow_methods=["*"],    # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],    # Allows all headers
)


# --- Hardcoded Company Context (Replace with your sample data) ---
COMPANY_CONTEXT = """
Welcome Aboard!

We’re thrilled to have you join the team! Here’s everything you need to know to get started:

Time Off & Vacation (PTO):
You get 20 days of Paid Time Off (PTO) annually. PTO starts building from day one, and you’ll see it accrue monthly. If you’re planning a trip, please submit your request for time off 2 weeks in advance via the HR portal. You can carry over up to 5 unused days to the next year.

Remote Work & Flexibility:
We’re all about work-life balance! Remote work is available for most roles, but please check in with your manager to confirm eligibility. To ensure success while working remotely, please maintain a quiet, dedicated workspace and a reliable internet connection. Our core collaboration hours are 10 AM to 4 PM in your local time zone. Please ensure availability for team sync-ups during these hours.

Tech Setup & IT Support:
You’ll receive a company laptop as your primary tool to get started. If you need assistance, our IT team is here to help. Simply submit a ticket via the IT Helpdesk Portal or email support@company.com. VPN setup instructions and other helpful tech guides are available on the Company Intranet (link provided during onboarding).

Our Mission & Values:
Our core mission is to “revolutionize the tech industry through innovation, transparency, and collaboration.”
We value:
	•	Customer Obsession: We are always focused on solving our customers’ problems.
	•	Bias for Action: We believe in making fast decisions and iterating quickly.
	•	Teamwork: We succeed when we collaborate and support one another.

Perks & Culture:
We work hard and have fun! Enjoy free snacks and coffee in the office, a monthly remote work stipend, and regular team lunches. Keep an eye out for announcements about our monthly virtual game nights, Friday team socials, and occasional wellness events to help balance work and relaxation.

Key Tools We Use:
	•	Communication: Slack is our primary platform for all team communication and daily updates.
	•	Project Management: We track most work in Jira and use Asana for individual task management.
	•	Documentation: Our knowledge base and documentation are stored in Confluence.

Remember: This AI assistant’s knowledge is based on this document. For specific personal questions or complex issues, please reach out to your manager or HR.
"""

# --- Pydantic Model for Request Body ---
class QuestionRequest(BaseModel):
    question: str

# --- API Endpoints ---
@app.get("/")
async def root():
    return {"message": "Onboarding Assistant API is running!"}

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    user_question = request.question
    print(f"Received question: {user_question}") # For debugging

    if not user_question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        # Construct the prompt for OpenAI
        prompt = f"""
        You are an AI onboarding assistant for a new employee.
        Answer the following question based *only* on the provided company context.
        If the answer cannot be found in the context, clearly state that you don't have that information based on the provided documents.

        Company Context:
        ---
        {COMPANY_CONTEXT}
        ---

        Question: {user_question}

        Answer:
        """
        # Choose the Gemini model
        model = genai.GenerativeModel('gemini-1.5-pro') # Updated model name

        # Construct prompt differently if needed, Gemini prefers direct instruction
        # Ensure your prompt structure works well with Gemini
        prompt = f"""Context: {COMPANY_CONTEXT}\n\nQuestion: {user_question}\n\nAnswer based only on context:"""

        response = model.generate_content(prompt)
        ai_answer = response.text.strip()


        # Call OpenAI API

        # response = openai_client.chat.completions.create(
        #     model="gpt-3.5-turbo", # Or "gpt-4" if you prefer
        #     messages=[
        #         {"role": "system", "content": "You are a helpful onboarding assistant."},
        #         {"role": "user", "content": prompt}
        #     ],
        #     max_tokens=150, # Limit response length
        #     temperature=0.5 # Adjust creativity vs factualness
        # )

        # ai_answer = response.choices[0].message.content.strip()
        # print(f"AI Answer: {ai_answer}") # For debugging

        # Log question and answer to Supabase (optional but good practice)
        try:
            data, count = supabase.table('qa_log').insert({
                "question": user_question,
                "answer": ai_answer
            }).execute()
            print(f"Logged to Supabase: {data}, {count}") # For debugging
        except Exception as db_error:
            print(f"Error logging to Supabase: {db_error}")
            # Don't fail the request if logging fails, just report it

        return {"answer": ai_answer}

    except Exception as e:
        print(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

# --- (Optional) Endpoint to view logs ---
@app.get("/history")
async def get_history():
    try:
        data, count = supabase.table('qa_log').select('*').order('created_at', desc=True).limit(10).execute()
        return {"history": data[1]} # data is a tuple (response_status, actual_data)
    except Exception as e:
        print(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=f"Could not fetch history: {e}")