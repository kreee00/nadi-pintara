import json
import os
import hashlib
import time
from engine.gap_analyzer import load_json, calculate_skill_gap, prefilter_courses
from engine.llm_recommender import get_recommendations

BASE = os.path.dirname(os.path.dirname(__file__))
CACHE_FILE = os.path.join(BASE, "data/cache.json")

def generate_path_for_employee(employee_id):
    employees = load_json(os.path.join(BASE, "data/employees.json"))
    roles = load_json(os.path.join(BASE, "data/roles_skills.json"))
    courses = load_json(os.path.join(BASE, "data/courses.json"))

    employee = next((e for e in employees if e["id"] == employee_id), None)
    if not employee:
        return {"error": f"Employee {employee_id} not found"}

    gaps, error = calculate_skill_gap(employee, roles)
    if error:
        return {"error": error}

    if not gaps:
        return {
            "employee": employee,
            "skill_gaps": {},
            "message": "No skill gaps found. Employee meets all requirements!",
            "learning_path": None
        }

    # Area 5: Caching Layer
    cache_key = _get_cache_key(employee, gaps)
    cached_result = _get_from_cache(cache_key)
    if cached_result:
        print(f"[CACHE HIT] Returning cached recommendations for {employee['id']}")
        return {
            "employee": employee,
            "target_role": employee["target_role"],
            "skill_gaps": gaps,
            "learning_path": cached_result,
            "cached": True
        }

    print(f"[CACHE MISS] Calling LLM for {employee['id']}")

    # Pre-filter BEFORE sending to LLM
    relevant_courses = prefilter_courses(gaps, courses, max_courses=8)
    print(f"[Engine] Gaps found: {len(gaps)} | Courses pre-filtered: {len(relevant_courses)} / {len(courses)}")

    # Area 3: LLM will now return hydrated recommendations thanks to the llm_recommender wrapper
    recommendations = get_recommendations(employee, gaps, relevant_courses)
    
    # Area 5: Save to cache
    _save_to_cache(cache_key, recommendations)

    return {
        "employee": employee,
        "target_role": employee["target_role"],
        "skill_gaps": gaps,
        "learning_path": recommendations,
        "cached": False
    }

def _get_cache_key(employee, gaps):
    """Area 5: Create unique hash based on employee role and skill gaps"""
    key_str = f"{employee['current_role']}|{employee['target_role']}|{json.dumps(gaps, sort_keys=True)}"
    return hashlib.sha256(key_str.encode()).hexdigest()

def _get_from_cache(key):
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
            if key in cache:
                item = cache[key]
                # Check expiry (24 hours = 86400 seconds)
                if time.time() - item['timestamp'] < 86400:
                    return item['data']
    except:
        pass
    return None

def _save_to_cache(key, data):
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
        except:
            pass
    
    cache[key] = {
        "timestamp": time.time(),
        "data": data
    }
    
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)
