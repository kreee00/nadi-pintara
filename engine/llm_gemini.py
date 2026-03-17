import os
import json
import re
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(override=True)

# Gemini 2.0 Flash is generally the best for this task
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def ask_gemini(prompt, retries=3, delay=5):
    """Sends prompt to Gemini with JSON mode enforced."""
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Low temperature for consistency
                    response_mime_type="application/json", # AREA: Enforce JSON mode
                    max_output_tokens=1024
                )
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if "503" in error_str or "UNAVAILABLE" in error_str:
                if attempt < retries - 1:
                    print(f"Gemini busy, retrying in {delay}s... (attempt {attempt + 1}/{retries})")
                    time.sleep(delay)
                else:
                    return None
            else:
                print(f"Gemini API Error: {error_str}")
                return None

def get_recommendations(employee, skill_gaps, courses):
    prompt = _build_prompt(employee, skill_gaps, courses)
    raw = ask_gemini(prompt)
    
    if raw is None:
        # Fallback is handled by the wrapper in llm_recommender.py if we return error
        return {"error": "Gemini API failed or timed out"}
        
    return _parse(raw)

def _build_prompt(employee, skill_gaps, courses):
    """
    Optimized Lean Prompt for Gemini.
    Reduces token count and focuses on course IDs.
    """
    # 1. Shrink course payload (id, title, skills_covered only)
    slim_courses = [
        {"id": c["id"], "title": c["title"], "skills": c["skills_covered"]}
        for c in courses
    ]

    # 2. Compress skill gaps ("HAZOP: 2->5")
    # Only top 3 gaps to save tokens
    top_3_gaps = list(skill_gaps.items())[:3]
    gap_strings = [f"{skill}: {data['current']}->{data['required']}" for skill, data in top_3_gaps]

    # 3. Minimal tokens & Few-shot example
    return f"""Task: Pick 3 courses for this PETRONAS employee.
Employee: {employee['current_role']} -> {employee['target_role']}
Gaps: {", ".join(gap_strings)}

Courses:
{json.dumps(slim_courses)}

Output JSON structure:
{{
  "recommended_path": [
    {{
      "order": 1,
      "course_id": "C001",
      "why_relevant": "One sentence reason matching specific gaps."
    }}
  ],
  "total_timeline": "...",
  "summary": "Two sentence personalized summary."
}}

Respond ONLY in valid JSON. Use only course_id and why_relevant in the path."""

def _parse(text):
    """Parses JSON response, handling markdown blocks if present."""
    if not text:
        return {"error": "Empty response from Gemini"}
        
    text = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Attempt to find JSON object in text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return {"error": "Could not parse response", "raw": text}
