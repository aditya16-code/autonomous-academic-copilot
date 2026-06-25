import streamlit as st
import json
import os
import PyPDF2
from datetime import datetime, timedelta
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# ==========================================
# PAGE CONFIGURATION & CSS
# ==========================================
st.set_page_config(page_title="Academic Auto-Pilot", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp { background-color: #000000; color: #ffffff; }
    h1, h2, h3, h4, h5, h6, p, label, span { color: #ffffff !important; }
    
    .stButton>button {
        border-radius: 12px; background-color: #6366f1; color: white !important;
        font-weight: 600; border: none; padding: 0.5rem 1rem;
        transition: all 0.3s ease; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
    .stButton>button:hover { background-color: #4f46e5; transform: translateY(-2px); }
    
    .stTextArea textarea {
        border-radius: 12px; border: 1px solid #333333;
        background-color: #111111; color: #ffffff !important;
    }
    
    [data-testid="stFileUploadDropzone"] {
        border-radius: 16px; border: 2px dashed #444444;
        background-color: #111111; transition: all 0.3s ease;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: #6366f1; background-color: #1a1b26;
    }
    
    [data-testid="stExpander"] {
        background-color: #0a0a0a; border: 1px solid #333333; border-radius: 8px;
    }
    [data-testid="stMetricValue"] { color: #6366f1 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# API LOADING
# ==========================================
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    st.error("🚨 API Key not found!")
    st.stop()

client = genai.Client(api_key=API_KEY)

st.title("🎓 Autonomous Academic Auto-Pilot")
st.subheader("Drag & drop your syllabus. Let the AI research, schedule, and organize your success.")

# ==========================================
# FEATURE 2: CALENDAR GENERATOR (.ICS)
# ==========================================
def generate_ics(tasks):
    """Generates an iCalendar file content from the task list."""
    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Academic Auto-Pilot//EN\n"
    for task in tasks:
        try:
            # We assume the AI returns deadline in YYYY-MM-DDTHH:MM:SS
            end_time = datetime.strptime(task['deadline'], "%Y-%m-%dT%H:%M:%S")
            # Schedule start time based on estimated hours
            start_time = end_time - timedelta(hours=task['estimated_hours'])
            
            dtstart = start_time.strftime("%Y%m%dT%H%M%S")
            dtend = end_time.strftime("%Y%m%dT%H%M%S")
            
            ics_content += "BEGIN:VEVENT\n"
            ics_content += f"SUMMARY:{task['title']} [{task['priority']} Priority]\n"
            ics_content += f"DESCRIPTION:Category: {task['category']}\n"
            ics_content += f"DTSTART:{dtstart}\n"
            ics_content += f"DTEND:{dtend}\n"
            ics_content += "END:VEVENT\n"
        except Exception:
            pass # Skip if date parsing fails
    ics_content += "END:VCALENDAR"
    return ics_content

# ==========================================
# TOOLS
# ==========================================
def create_calendar_event(task_title: str, start_time: str, duration_hours: int):
    message = f"✅ CALENDAR: Scheduled '{task_title}' for {duration_hours} hours starting at {start_time}"
    st.success(message)
    return message

def create_google_doc(document_title: str, assignment_type: str):
    header = "Name: Aditya Agarwal | Roll No: 2401640100068"
    message = f"📝 WORKSPACE: Created '{document_title}' template. (Auto-filled header: {header})"
    st.info(message)
    return message

def research_topic(topic: str):
    message = f"🔍 RESEARCH: Found 3 peer-reviewed sources for '{topic}' and attached them to your Workspace."
    st.warning(message) 
    return message

tool_map = {
    "create_calendar_event": create_calendar_event,
    "create_google_doc": create_google_doc,
    "research_topic": research_topic
}

# ==========================================
# FEATURE 1: SMART SUB-TASKING INSTRUCTIONS
# ==========================================
parser_instructions = """
You are an expert academic data extractor and autonomous agent. 
Analyze the text and output a strictly structured JSON array of tasks. 
Extract explicit deadlines, estimate required effort, and categorize the tasks. Assume the year is 2026.

CRITICAL RULE FOR SMART SUB-TASKING: If any single task requires more than 3 hours of effort, you MUST break it down into smaller, logical sub-tasks (e.g., "Phase 1: Research", "Phase 2: Drafting"). No single task in the output should have an estimated_hours value greater than 3.
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
# UI LAYOUT
# ==========================================
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📥 1. Input Syllabus")
    uploaded_file = st.file_uploader("Drop a PDF Syllabus here...", type="pdf")
    syllabus_text = ""
    if uploaded_file is not None:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            syllabus_text += page.extract_text() + "\n"
        st.success("PDF Extracted Successfully!")
    raw_text = st.text_area("Or paste raw text:", value=syllabus_text, height=200)

with col2:
    st.markdown("### 🚀 2. Agent Dashboard")
    dash_col1, dash_col2, dash_col3 = st.columns(3)
    with dash_col1: st.metric(label="Agent Status", value="Online", delta="Ready")
    with dash_col2: st.metric(label="Tasks Scheduled", value="0", delta="Awaiting Input")
    with dash_col3: st.metric(label="Time Saved", value="0 hrs", delta="Let's go!")
    st.divider()

    if st.button("Activate Multi-Tool Agent", use_container_width=True):
        if raw_text.strip():
            with st.spinner("🧠 Agent is analyzing and executing tools..."):
                try:
                    # Phase 1: Data Extraction
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=raw_text,
                        config=types.GenerateContentConfig(
                            system_instruction=parser_instructions,
                            response_mime_type="application/json",
                            response_schema=TaskList,
                            temperature=0.1,
                        ),
                    )
                    
                    if not response.text or response.text.strip() == "":
                        st.error("🛑 Empty response. Please submit a smaller text section.")
                        st.stop()
                        
                    extracted_data = json.loads(response.text)
                    st.markdown("#### 📊 Identified Tasks:")
                    st.dataframe(extracted_data["tasks"], use_container_width=True)
                    
                    # TRIGGER ICS GENERATOR
                    ics_data = generate_ics(extracted_data["tasks"])
                    st.download_button(
                        label="📅 Download .ics Calendar File",
                        data=ics_data,
                        file_name="academic_calendar.ics",
                        mime="text/calendar",
                    )
                    
                    with st.expander("🤖 View Agent Action Log", expanded=True):
                        # Phase 2: Batch Processing Tool Execution
                        tasks_string = json.dumps(extracted_data["tasks"], indent=2)
                        batch_prompt = f"""
                        I have extracted the following academic tasks from my syllabus:
                        {tasks_string}
                        
                        Please analyze this list and execute the necessary tools for ALL of them at once:
                        1. Schedule a calendar event for every task based on its estimated hours.
                        2. Create a google doc workspace for any task categorized as an Assignment or Project.
                        3. Research the topic for any task categorized as a Project.
                        """
                        
                        agent_response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=batch_prompt,
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
                                    tool_map[tool_name](**tool_args)
                                    
                except Exception as e:
                    st.error(f"Agent encountered a system error: {e}")
        else:
            st.warning("Please upload a PDF or paste text first.")

# ==========================================
# FEATURE 3: CHAT WITH SYLLABUS (RAG)
# ==========================================
st.divider()
st.markdown("### 💬 Chat with your Syllabus")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a question about grading, rules, or late policies..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI response
    with st.chat_message("assistant"):
        if raw_text.strip():
            rag_prompt = f"Use the following syllabus document to answer the student's question accurately.\n\nSyllabus Data:\n{raw_text}\n\nStudent Question: {prompt}"
            try:
                chat_response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=rag_prompt
                )
                st.markdown(chat_response.text)
                st.session_state.messages.append({"role": "assistant", "content": chat_response.text})
            except Exception as e:
                st.error("Cannot connect to AI. Check API limits.")
        else:
            st.warning("⚠️ Please upload a syllabus or paste text at the top first, so I can read it to answer your question!")