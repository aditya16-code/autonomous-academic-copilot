import os
import json
from google import genai
from google.genai import types

# 🚨 PASTE YOUR API KEY HERE
API_KEY = 'AQ.Ab8RN6KE_m0Ifh80kCJ8LIS2VreilgyKhg_B9hTg7_JggGIouw'
client = genai.Client(api_key=API_KEY)

# ==========================================
# 1. THE TOOL (The action the AI can take)
# ==========================================
def create_calendar_event(task_title: str, start_time: str, duration_hours: int):
    """Autonomously blocks out a dedicated study window in the user's calendar."""
    # In a real app, this connects to the actual Google Calendar API. 
    # For now, we simulate the action for the hackathon prototype.
    print(f"\n🗓️  [SYSTEM ACTION TRIGGERED BY AI]")
    print(f"✅  Successfully scheduled: '{task_title}'")
    print(f"⏰  When: {start_time} (Duration: {duration_hours} hours)")
    return f"Event for {task_title} created successfully."

# ==========================================
# 2. THE PLANNER AGENT
# ==========================================
planner_instructions = """
You are an autonomous execution agent. You receive a list of urgent tasks. 
Your job is to proactively schedule 'Deep Work' blocks for these tasks using the calendar tool provided.
Do not ask the user for permission, just schedule the events intelligently before the deadline.
Assume today's date is June 23, 2026.
"""

def plan_schedule(parsed_tasks_json):
    print("\n🧠 Planner Agent is evaluating priorities and calling tools...")
    
    # We use a chat session so the AI can automatically trigger our tool
    chat = client.chats.create(
        model='gemini-3-flash-preview',
        config=types.GenerateContentConfig(
            system_instruction=planner_instructions,
            tools=[create_calendar_event], # WE GIVE THE AI THE TOOL HERE!
            temperature=0.2
        )
    )
    
    # Send the parsed JSON to the planner agent
    prompt = f"Here is my extracted syllabus data. Please schedule study blocks for me: {parsed_tasks_json}"
    response = chat.send_message(prompt)
    
    print("\n--- Agent Final Message ---")
    print(response.text)

# ==========================================
# 3. EXECUTION FLOW
# ==========================================
if __name__ == "__main__":
    # 1. We pretend the Parser Agent already ran and gave us this JSON
    extracted_data = """
    {
      "tasks": [
        {"title": "Intro to ML Final Paper", "deadline": "2026-06-29T14:00:00", "estimated_hours": 15, "priority": "High"},
        {"title": "Math Quiz Prep", "deadline": "2026-06-26T23:59:59", "estimated_hours": 1, "priority": "Medium"}
      ]
    }
    """
    
    # 2. Pass the data to the Planner Agent to take action
    plan_schedule(extracted_data)