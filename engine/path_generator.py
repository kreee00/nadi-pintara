import json
import os
from engine.gap_analyzer import load_json, calculate_skill_gap
from engine.llm_recommender import get_recommendations

BASE = os.path.dirname(os.path.dirname(__file__))

def generate_path_for_employee(employee_id):
    # Load all data
    employees = load_json(os.path.join(BASE, "data/employees.json"))
    roles = load_json(os.path.join(BASE, "data/roles_skills.json"))
    courses = load_json(os.path.join(BASE, "data/courses.json"))

    # Find the employee
    employee = next((e for e in employees if e["id"] == employee_id), None)
    if not employee:
        return {"error": f"Employee {employee_id} not found"}

    # Calculate skill gaps
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

    # Get AI recommendations
    recommendations = get_recommendations(employee, gaps, courses)

    return {
        "employee": employee,
        "target_role": employee["target_role"],
        "skill_gaps": gaps,
        "learning_path": recommendations
    }
