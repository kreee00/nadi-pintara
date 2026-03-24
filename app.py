from flask import Flask, jsonify, request, send_from_directory, render_template, redirect
from flask_cors import CORS
from engine.path_generator import generate_path_for_employee
from engine.gap_analyzer import load_json as lj, calculate_skill_gap
from engine.llm_recommender import get_recommendations
import json
import os
from dotenv import load_dotenv

import threading

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)


def _prewarm_analytics():
    """Pre-compute analytics cache in background so the HR dashboard loads instantly."""
    try:
        from engine.analytics import get_or_compute_analytics
        get_or_compute_analytics()
    except Exception:
        pass  # Non-critical; dashboard will compute on first request if needed

threading.Thread(target=_prewarm_analytics, daemon=True).start()


def load_json(path):
    with open(path) as f:
        return json.load(f)


# ── Page Routes ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect("/login")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/courses-page")
def courses_page():
    return render_template("courses.html")


@app.route("/hr-dashboard")
def hr_dashboard():
    return render_template("hr_dashboard.html")


# ── Data API Routes ───────────────────────────────────────────────────────────

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


@app.route("/courses", methods=["GET"])
def get_courses():
    courses = load_json("data/courses.json")
    return jsonify(courses)


# ── Recommendation API Routes ─────────────────────────────────────────────────

@app.route("/recommend/<employee_id>", methods=["GET"])
def recommend(employee_id):
    result = generate_path_for_employee(employee_id)
    return jsonify(result)


@app.route("/recommend/custom", methods=["POST"])
def recommend_custom():
    data = request.json

    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = ["current_role", "target_role", "current_skills"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    roles   = lj("data/roles_skills.json")
    courses = lj("data/courses.json")

    gaps, error = calculate_skill_gap(data, roles)
    if error:
        return jsonify({"error": error}), 400

    if not gaps:
        return jsonify({
            "employee": data,
            "skill_gaps": {},
            "message": "No skill gaps found. Employee already meets all requirements!",
            "learning_path": None
        })

    recommendations = get_recommendations(data, gaps, courses)

    return jsonify({
        "employee": data,
        "skill_gaps": gaps,
        "learning_path": recommendations
    })


# ── Fast Gap Endpoint (no LLM) ────────────────────────────────────────────────

@app.route("/employee/<employee_id>/gap", methods=["GET"])
def get_employee_gap(employee_id):
    employees = load_json("data/employees.json")
    roles = load_json("data/roles_skills.json")
    employee = next((e for e in employees if e["id"] == employee_id), None)
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    gaps, error = calculate_skill_gap(employee, roles)
    return jsonify({"employee": employee, "skill_gaps": gaps or {}, "error": error})


# ── Chatbot Endpoints ─────────────────────────────────────────────────────────

@app.route("/chatbot/message", methods=["POST"])
def chatbot_message():
    from engine.chatbot_engine import process_chatbot_message
    return jsonify(process_chatbot_message(request.json))


@app.route("/chatbot/summarize", methods=["POST"])
def chatbot_summarize():
    from engine.chatbot_engine import generate_assessment_summary
    return jsonify(generate_assessment_summary(request.json))


# ── HR Analytics API ──────────────────────────────────────────────────────────

@app.route("/api/analytics/workforce", methods=["GET"])
def workforce_analytics():
    from engine.analytics import get_or_compute_analytics
    try:
        data, _ = get_or_compute_analytics()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/refresh", methods=["POST"])
def refresh_analytics():
    from engine.analytics import refresh_analytics_cache
    try:
        data = refresh_analytics_cache()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Health Check ──────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider == "openai":
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        base  = os.getenv("OPENAI_BASE_URL", "").strip() or "https://api.openai.com/v1"
    elif provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        base  = "http://localhost:11434"
    else:
        provider = "gemini"
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        base  = "https://generativelanguage.googleapis.com"
    return jsonify({
        "status":       "ok",
        "message":      "Nadi Pintara API is running",
        "llm_provider": provider.upper(),
        "llm_model":    model,
        "llm_endpoint": base,
    })


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)