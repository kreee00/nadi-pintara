from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from engine.path_generator import generate_path_for_employee
import json, os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder=".")
CORS(app)

def load_json(path):
    with open(path) as f:
        return json.load(f)

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory(".", path)

@app.route("/employees", methods=["GET"])
def get_employees():
    employees = load_json("data/employees.json")
    return jsonify(employees)

@app.route("/employee/<employee_id>", methods=["GET"])
def get_employee(employee_id):
    employees = load_json("data/employees.json")
    employee = next((e for e in employees if e["id"] == employee_id), None)
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify(employee)

@app.route("/roles", methods=["GET"])
def get_roles():
    roles = load_json("data/roles_skills.json")
    return jsonify(roles)

@app.route("/recommend/<employee_id>", methods=["GET"])
def recommend(employee_id):
    result = generate_path_for_employee(employee_id)
    return jsonify(result)

@app.route("/recommend/custom", methods=["POST"])
def recommend_custom():
    """Accept a custom employee profile from the frontend form"""
    data = request.json
    # data should match employee structure
    from engine.gap_analyzer import load_json as lj, calculate_skill_gap
    from engine.llm_recommender import get_recommendations

    roles = lj("data/roles_skills.json")
    courses = lj("data/courses.json")

    gaps, error = calculate_skill_gap(data, roles)
    if error:
        return jsonify({"error": error}), 400

    recommendations = get_recommendations(data, gaps, courses)
    return jsonify({
        "employee": data,
        "skill_gaps": gaps,
        "learning_path": recommendations
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)