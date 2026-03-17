import os
import json
import re
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

def ask_ollama(prompt, retries=2):
    """Sends prompt to Ollama with optimized runtime settings (Area 4)"""
    for attempt in range(retries):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0,       # Area 4: Deterministic output
                        "top_p": 0.1,           # Area 4: Fast & consistent
                        "num_thread": 4,        # Area 4: Optimal for i5-1135G7 (4 cores)
                        "num_ctx": 1024,        # Area 4: Minimum needed context
                        "num_predict": 256,     # Area 4: Limit output length
                        "repeat_penalty": 1.2,
                        "use_mmap": True        # Area 4: Efficient RAM usage
                    }
                },
                timeout=45 # Area 1: Fast response goal
            )
            response.raise_for_status()
            return response.json()["response"]
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            if attempt < retries - 1:
                print(f"[Ollama] Attempt {attempt + 1} failed, retrying...")
                continue
            print(f"[Ollama] Error: {str(e)}. Triggering fallback.")
            return None

def get_recommendations(employee, skill_gaps, courses):
    prompt = _build_prompt(employee, skill_gaps, courses)
    raw = ask_ollama(prompt)
    
    if raw is None:
        # Area 6: Fallback to pure Python logic
        return _fallback_recommendation(skill_gaps, courses)
        
    parsed = _parse(raw)
    if "error" in parsed:
        return _fallback_recommendation(skill_gaps, courses)
    return parsed

def _build_prompt(employee, skill_gaps, courses):
    """Area 2: Optimized Lean Prompt"""
    # 2.2 Shrink course payload (id, title, skills_covered only)
    slim_courses = [
        {"id": c["id"], "title": c["title"], "skills": c["skills_covered"]}
        for c in courses
    ]

    # 2.3 Compress skill gaps ("HAZOP: 2->5")
    # Only top 3 gaps to save tokens
    top_3_gaps = list(skill_gaps.items())[:3]
    gap_strings = [f"{skill}: {data['current']}->{data['required']}" for skill, data in top_3_gaps]

    # 2.1 Reduce token count & 2.5 Few-shot example
    return f"""Task: Pick 3 courses for this PETRONAS employee.
Employee: {employee['current_role']} -> {employee['target_role']}
Gaps: {", ".join(gap_strings)}

Courses:
{json.dumps(slim_courses)}

Example Output:
{{"recommended_path": [{{"order": 1, "course_id": "C001", "why_relevant": "Covers Advanced Reservoir Simulation gap."}}], "total_timeline": "3 months", "summary": "Focus on technical gaps."}}

Respond ONLY in JSON. Use only course_id and why_relevant."""

def _parse(text):
    text = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return {"error": "Could not parse response", "raw": text}

def _fallback_recommendation(skill_gaps, courses):
    """Area 6: Graceful Fallback (Pure Python)"""
    print("[FALLBACK] Using skill-overlap logic (LLM Unavailable)")
    
    # Sort courses by overlap with all gaps
    gap_skills = set(skill_gaps.keys())
    scored_courses = []
    
    for c in courses:
        overlap = len(set(c["skills_covered"]) & gap_skills)
        scored_courses.append((overlap, c))
    
    # Take top 3
    scored_courses.sort(key=lambda x: x[0], reverse=True)
    top_3 = scored_courses[:3]
    
    path = []
    for i, (score, c) in enumerate(top_3):
        path.append({
            "order": i + 1,
            "course_id": c["id"],
            "why_relevant": "Recommended based on skill gap match (AI engine unavailable)"
        })
    
    return {
        "recommended_path": path,
        "total_timeline": "Flexible",
        "summary": "AI engine is currently unavailable. Recommendations are based on direct skill gap matching."
    }
