# Autonomous Academic Auto-Pilot
**Built with Gemini 2.5 Flash for the Google AI Hackathon**

## The Problem
College students are drowning in unstructured data (syllabi, reading lists, rubrics) and spending countless hours manually organizing their schedules, creating docs, and finding research.

## The Solution
A multi-stage, autonomous AI agent that ingests raw syllabus PDFs and takes over the heavy lifting.

### How it Works (Agentic Depth):
1. **Phase 1 (Data Ingestion & Structured Output):** A Gemini agent reads the uploaded PDF and uses `response_schema` to strictly enforce data extraction into JSON format (Deadlines, Estimates, Categories).
2. **Phase 2 (Multi-Tool Orchestration):** A secondary agent uses **Function Calling** to dynamically select tools based on the task type:
   - 📅 **Calendar Tool:** Automatically schedules "Deep Work" blocks based on estimated effort.
   - 📝 **Workspace Tool:** Autonomously provisions a Google Doc starter template pre-filled with student ID headers.
   - 🔍 **Research Tool:** Autonomously searches academic databases and attaches peer-reviewed sources for heavy project tasks.

## 🛠 Tech Stack
- **AI Core:** Google Gemini 2.5 Flash SDK
- **Frontend:** Streamlit
- **PDF Processing:** PyPDF2
- **Deployment:** Streamlit Community Cloud

*Developed by Aditya Agarwal*