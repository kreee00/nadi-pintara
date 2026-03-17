import os
import json
from dotenv import load_dotenv

load_dotenv(override=True)

PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
BASE = os.path.dirname(os.path.dirname(__file__))

if PROVIDER == "ollama":
    from engine.llm_ollama import get_recommendations as _get_raw_recommendations
    print(f"[LLM] Using Ollama ({os.getenv('OLLAMA_MODEL', 'llama3.2:3b')})")
else:
    from engine.llm_gemini import get_recommendations as _get_raw_recommendations
    print("[LLM] Using Gemini 2.5 Flash")

def get_recommendations(employee, skill_gaps, courses):
    """
    Wrapper that calls the selected LLM and then hydrates the results
    with full course metadata to ensure callers (like test_engine.py)
    always receive complete JSON objects.
    """
    # 1. Get the slim/raw response from the LLM
    result = _get_raw_recommendations(employee, skill_gaps, courses)
    
    # 2. If it's an error or already hydrated, return as is
    if not result or "error" in result or "recommended_path" not in result:
        return result

    # 3. Hydrate with full course data
    # (Note: In a larger app, we'd avoid re-loading courses.json here, 
    # but for this script it ensures consistency for all callers)
    all_courses_path = os.path.join(BASE, "data/courses.json")
    try:
        with open(all_courses_path, "r") as f:
            all_courses = json.load(f)
    except:
        all_courses = courses # Fallback to the filtered list provided

    return hydrate_recommendations(result, all_courses)

def hydrate_recommendations(slim_recom, all_courses):
    """Re-attaches course metadata to minimal LLM output"""
    course_map = {c["id"]: c for c in all_courses}
    
    hydrated_path = []
    for item in slim_recom["recommended_path"]:
        cid = item.get("course_id")
        if cid in course_map:
            course = course_map[cid]
            hydrated_path.append({
                "order": item.get("order"),
                "course_id": cid,
                "course_title": course["title"],
                "provider": course["provider"],
                "url": course["url"],
                "duration": course["duration"],
                "skills_addressed": course["skills_covered"],
                "why_relevant": item.get("why_relevant")
            })
    
    return {
        "recommended_path": hydrated_path,
        "total_timeline": slim_recom.get("total_timeline", "N/A"),
        "summary": slim_recom.get("summary", "")
    }
