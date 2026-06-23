import streamlit as st
import json
import os
from google import genai
from google.genai import types

# ==========================================
# SECURE API KEY LOADING
# ==========================================
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("🚨 API Key not found! The app cannot run.")
    st.info("If deploying to Streamlit Cloud, add GEMINI_API_KEY to your Advanced Settings > Secrets.")
    st.stop()

client = genai.Client(api_key=API_KEY)

# ==========================================
# PAGE CONFIGURATION 
# ==========================================
st.set_page_config(page_title="Academic Auto-Pilot", page_icon="🎓", layout="wide")
st.title("🎓 Autonomous Academic Auto-Pilot")
st.subheader("Paste your chaos. Let the AI schedule your success.")
parser_instructions = """
You are an expert academic data extractor. Analyze the text and output a strictly structured JSON array of actionable tasks. 
Extract explicit deadlines, estimate required effort, and categorize the tasks. Assume the year is 2026.
"""

response_schema = {
    "type": "object",
    "properties": {
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "category": {"type": "string"},
                    "deadline": {"type": "string", "description": "ISO 8601 format"},
                    "estimated_hours": {"type": "integer"},
                    "priority": {"type": "string", "description": "High, Medium, or Low"}
                }
            }
        }
    }
}
# --- TOOL 1: The Calendar Scheduler ---
def create_calendar_event(task_title: str, start_time: str, duration_hours: int):
    """Autonomously blocks out a dedicated study window in the user's calendar."""
    message = f"✅ CALENDAR: Scheduled '{task_title}' for {duration_hours} hours starting at {start_time}"
    st.success(message)  # <--- THIS FORCES IT TO SHOW ON SCREEN!
    return message

# --- TOOL 2: The Workspace Architect ---
def create_google_doc(document_title: str, assignment_type: str):
    """Autonomously creates a Google Doc starter template for essays, projects, or papers."""
    header = "Name: Aditya Agarwal | Roll No: 2401640100068"
    message = f"📝 WORKSPACE: Created '{document_title}' template.\n*(Auto-filled header: {header})*"
    st.info(message)  # <--- THIS FORCES IT TO SHOW ON SCREEN!
    return message


planner_instructions = """
You are an autonomous execution agent. You receive a list of tasks. 
1. For EVERY task, use the calendar tool to schedule a 'Deep Work' block before the deadline.
2. IF the task category is a "Project", "Paper", or "Essay", ALSO use the Google Doc tool to create a starter workspace for the user.
Do not ask for permission, just execute the necessary tools intelligently.
"""

# ==========================================
# USER INTERFACE (The Dashboard)
# ==========================================
col1, col2 = st.columns([1, 1.5])

with col1:
    st.markdown("### 1. Input Data")
    user_input = st.text_area(
        "Paste syllabus text, professor emails, or brain dumps here:", 
        height=250,
        placeholder="e.g., My final ML paper is due on June 29th at 2 PM. It's 40% of my grade..."
    )
    start_agent = st.button("🚀 Activate Multi-Tool Agent", use_container_width=True)

with col2:
    st.markdown("### 2. AI Execution Feed")
    
    if start_agent and user_input:
        with st.status("🤖 Agent is processing your data...", expanded=True) as status:
            
            st.write("📄 Extracting task data...")
            extract_response = client.models.generate_content(
                model='gemini-3-flash-preview',
                contents=user_input,
                config=types.GenerateContentConfig(
                    system_instruction=parser_instructions,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.1
                )
            )
            
            parsed_data = extract_response.text
            parsed_json = json.loads(parsed_data)
            
            st.write("📊 **Identified Tasks:**")
            st.dataframe(parsed_json["tasks"], use_container_width=True)
            
            st.write("🧠 Triggering multi-tool orchestration...")
            chat = client.chats.create(
                model='gemini-3-flash-preview',
                config=types.GenerateContentConfig(
                    system_instruction=planner_instructions,
                    tools=[create_calendar_event, create_google_doc], # BOTH TOOLS GIVEN TO AI
                    temperature=0.2
                )
            )
            
            prompt = f"Here is my extracted syllabus data. Execute planning tools: {parsed_data}"
            plan_response = chat.send_message(prompt)
            
            status.update(label="✅ All tools executed successfully!", state="complete", expanded=True)
            
        st.success("**Agent Execution Summary:**")
        st.write(plan_response.text)
        
    elif start_agent and not user_input:
        st.warning("Please paste some text for the agent to analyze!")









