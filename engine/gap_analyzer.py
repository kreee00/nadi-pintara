import json
import os

def load_json(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

def calculate_skill_gap(employee, roles_data):
    target_role = employee["target_role"]
    
    if target_role not in roles_data:
        return None, f"Target role '{target_role}' not found"
    
    required_skills = roles_data[target_role]["required_skills"]
    current_skills = employee["current_skills"]
    
    gaps = {}
    for skill, required_level in required_skills.items():
        current_level = current_skills.get(skill, 0)
        if current_level < required_level:
            gaps[skill] = {
                "current": current_level,
                "required": required_level,
                "gap": required_level - current_level
            }
    
    # Sort by biggest gap first (highest priority)
    gaps = dict(sorted(gaps.items(), key=lambda x: x[1]["gap"], reverse=True))
    return gaps, None
