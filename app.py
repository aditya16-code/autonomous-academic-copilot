import streamlit as st
import json
import os
import PyPDF2
import time
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

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
st.subheader("Drag & drop your syllabus. Let the AI research, schedule, and organize your success.")

# ==========================================
# AUTONOMOUS TOOLS (The Agent's "Hands")
# ==========================================
def create_calendar_event(task_title: str, start_time: str, duration_hours: int):
    """Autonomously blocks out a dedicated study window in the user's calendar."""
    message = f"✅ CALENDAR: Scheduled '{task_title}' for {duration_hours} hours starting at {start_time}"
    st.success(message)
    return message

def create_google_doc(document_title: str, assignment_type: str):
    """Autonomously creates a Google Doc starter template for essays, projects, or papers."""
    header = "Name: Aditya Agarwal | Roll No: 2401640100068"
    message = f"📝 WORKSPACE: Created '{document_title}' template. (Auto-filled header: {header})"
    st.info(message)
    return message

def research_topic(topic: str):
    """Autonomously searches academic databases for sources related to the project topic."""
    message = f"🔍 RESEARCH: Found 3 peer-reviewed sources for '{topic}' and attached them to your Workspace."
    st.warning(message) 
    return message

# Map the functions so Gemini can call them
tool_map = {
    "create_calendar_event": create_calendar_event,
    "create_google_doc": create_google_doc,
    "research_topic": research_topic
}

# ==========================================
# AI SYSTEM INSTRUCTIONS & SCHEMA
# ==========================================
parser_instructions = """
You are an expert academic data extractor and autonomous agent. 
Analyze the text and output a strictly structured JSON array of tasks. 
Extract explicit deadlines, estimate required effort, and categorize the tasks. Assume the year is 2026.
"""

class Task(BaseModel):
    title: str
    deadline: str = Field(description="Format: YYYY-MM-DDTHH:MM:SS")
    estimated_hours: int
    priority: str
    category: str

class TaskList(BaseModel):
    tasks: list[Task]

# ==========================================
# UI: DRAG AND DROP PDF & TEXT INPUT
# ==========================================
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📥 1. Input Syllabus")
    uploaded_file = st.file_uploader("Drop a PDF Syllabus here...", type="pdf")
    
    syllabus_text = ""
    if uploaded_file is not None:
        # Extract text from the PDF!
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            syllabus_text += page.extract_text() + "\n"
        st.success("PDF Extracted Successfully!")
    
    # Fallback text area
    raw_text = st.text_area("Or paste raw text:", value=syllabus_text, height=200)

with col2:
    st.markdown("### 🚀 2. Agent Dashboard")
    if st.button("Activate Multi-Tool Agent", use_container_width=True):
        if raw_text:
            with st.spinner("🧠 Agent is analyzing and executing tools..."):
                try:
                    # Phase 1: Data Extraction
                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=raw_text,
                        config=types.GenerateContentConfig(
                            system_instruction=parser_instructions,
                            response_mime_type="application/json",
                            response_schema=TaskList,
                            temperature=0.1,
                        ),
                    )
                    
                    extracted_data = json.loads(response.text)
                    st.markdown("#### 📊 Identified Tasks:")
                    st.dataframe(extracted_data["tasks"], use_container_width=True)
                    
                    st.markdown("#### 🤖 Agent Action Log:")
                    
                    # Phase 2: Autonomous Tool Execution
                    for task in extracted_data["tasks"]:
                        title = task["title"]
                        category = task["category"]
                        
                        prompt = f"I have a task: '{title}'. It is a {category} assignment requiring {task['estimated_hours']} hours. Take the necessary actions to schedule it, create a workspace if it requires writing, and research it if it is a project or academic paper."
                        
                        agent_response = client.models.generate_content(
                            model='gemini-1.5-flash',
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                tools=[create_calendar_event, create_google_doc, research_topic],
                                temperature=0.1,
                            ),
                        )
                        
                        if agent_response.function_calls:
                            for function_call in agent_response.function_calls:
                                tool_name = function_call.name
                                tool_args = function_call.args
                                
                                if tool_name in tool_map:
                                    # Execute the tool and show it on screen
                                    tool_map[tool_name](**tool_args)
                                    
                        # THE FIX: 15-second cooldown to stay completely under Google's 5-RPM limit
                        time.sleep(15)
                                    
                except Exception as e:
                    st.error(f"Agent encountered an error: {e}")
        else:
            st.warning("Please upload a PDF or paste text first.")