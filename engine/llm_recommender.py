import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:latest"

def ask_qwen(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,   # Lower = more consistent JSON output
                "top_p": 0.9
            }
        },
        timeout=120  # Qwen can take up to 2 minutes on your hardware
    )
    return response.json()["response"]

def parse_json_response(text):
    # Strip markdown code fences if Qwen adds them
    text = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON object from the response
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return {"error": "Could not parse response", "raw": text}

def get_recommendations(employee, skill_gaps, courses):
    prompt = f"""You are a corporate learning advisor. Your job is to recommend the best online courses for an employee based on their skill gaps.

EMPLOYEE:
Name: {employee['name']}
Current Role: {employee['current_role']}
Target Role: {employee['target_role']}
Years of Experience: {employee['years_experience']}

SKILL GAPS (skill: current level → required level, scale 1-5):
{json.dumps(skill_gaps, indent=2)}

AVAILABLE COURSES:
{json.dumps(courses, indent=2)}

INSTRUCTIONS:
- Select only the most relevant 3 to 5 courses from the list above
- Prioritise courses that address the biggest skill gaps first
- Only recommend courses that exist in the list above
- Respond ONLY with a valid JSON object, no explanation, no markdown

Use this exact JSON format:
{{
  "recommended_path": [
    {{
      "order": 1,
      "course_id": "C001",
      "course_title": "Course title here",
      "provider": "Provider here",
      "url": "URL here",
      "duration": "Duration here",
      "skills_addressed": ["Skill1", "Skill2"],
      "why_relevant": "One sentence explanation specific to this employee"
    }}
  ],
  "total_timeline": "Estimated total duration e.g. 4-5 months",
  "summary": "Two sentence personalised summary for the employee"
}}"""

    raw_response = ask_qwen(prompt)
    return parse_json_response(raw_response)
