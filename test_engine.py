import json
import time
import sys
import threading
from engine.gap_analyzer import load_json, calculate_skill_gap, prefilter_courses

# ── Spinner animation ──────────────────────────────────────────────────────────

class Spinner:
    def __init__(self, message):
        self.message = message
        self.spinning = False
        self.thread = None

    def _spin(self):
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        i = 0
        while self.spinning:
            sys.stdout.write(f"\r  {frames[i % len(frames)]}  {self.message}...")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

    def start(self):
        self.spinning = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()

    def stop(self, success=True):
        self.spinning = False
        self.thread.join()
        icon = "✅" if success else "❌"
        sys.stdout.write(f"\r  {icon}  {self.message}... done\n")
        sys.stdout.flush()


# ── Helpers ────────────────────────────────────────────────────────────────────

def print_header():
    print("\n" + "═" * 55)
    print("   🛢️  NADI PINTARA — AI Engine Test")
    print("═" * 55)

def print_section(title):
    print(f"\n{'─' * 55}")
    print(f"  {title}")
    print(f"{'─' * 55}")

def print_step(step, text):
    print(f"\n  [{step}] {text}")

def print_gap_bar(skill, current, required):
    filled = "█" * current
    empty  = "░" * (required - current)
    gap    = required - current
    print(f"      {skill:<30} {filled}{empty}  {current}/{required}  (gap: {gap})")

def print_course_card(i, course):
    print(f"\n      {'─' * 45}")
    print(f"      #{course['order']}  {course['course_title']}")
    print(f"          Provider : {course['provider']}")
    print(f"          Duration : {course['duration']}")
    print(f"          Skills   : {', '.join(course['skills_addressed'])}")
    print(f"          Why      : {course['why_relevant']}")


# ── Main test ──────────────────────────────────────────────────────────────────

def run_test(employee_id="E003"):
    print_header()

    import os
    BASE = os.path.dirname(__file__)

    # Step 1 — Load data
    print_step("1/5", "Loading data files")
    spinner = Spinner("Reading employees, roles and courses")
    spinner.start()
    time.sleep(0.5)  # small pause so it's visible
    employees = load_json(os.path.join(BASE, "data/employees.json"))
    roles     = load_json(os.path.join(BASE, "data/roles_skills.json"))
    courses   = load_json(os.path.join(BASE, "data/courses.json"))
    spinner.stop()

    # Step 2 — Find employee
    print_step("2/5", "Loading employee profile")
    employee = next((e for e in employees if e["id"] == employee_id), None)
    if not employee:
        print(f"  ❌  Employee {employee_id} not found.")
        return

    print_section("👤 Employee Profile")
    print(f"      Name        : {employee['name']}")
    print(f"      Department  : {employee['department']}")
    print(f"      Current     : {employee['current_role']}")
    print(f"      Target      : {employee['target_role']}")
    print(f"      Experience  : {employee['years_experience']} years")
    print(f"      Education   : {employee.get('education', 'N/A')}")

    # Step 3 — Calculate gaps
    print_step("3/5", "Calculating skill gaps")
    spinner = Spinner("Comparing current skills against target role requirements")
    spinner.start()
    time.sleep(0.8)
    gaps, error = calculate_skill_gap(employee, roles)
    spinner.stop()

    if error:
        print(f"  ❌  {error}")
        return

    if not gaps:
        print("\n  ✅  No skill gaps found! Employee already meets all requirements.")
        return

    print_section(f"📊 Skill Gap Analysis  ({len(gaps)} gaps found)")
    for skill, data in gaps.items():
        print_gap_bar(skill, data["current"], data["required"])

    # Step 4 — Pre-filter courses
    print_step("4/5", "Pre-filtering course catalogue")
    spinner = Spinner("Matching gaps to relevant courses")
    spinner.start()
    time.sleep(0.5)
    relevant_courses = prefilter_courses(gaps, courses, max_courses=8)
    spinner.stop()
    print(f"      → {len(relevant_courses)} of {len(courses)} courses selected for AI review")

    # Step 5 — Ask LLM
    print_step("5/5", "Sending to AI engine")

    from dotenv import load_dotenv
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "gemini").upper()

    spinner = Spinner(f"Waiting for {provider} to generate personalised recommendations")
    spinner.start()

    start = time.time()
    from engine.llm_recommender import get_recommendations
    result = get_recommendations(employee, gaps, relevant_courses)
    elapsed = time.time() - start

    spinner.stop()
    print(f"      → Response received in {elapsed:.1f}s")

    # ── Results ────────────────────────────────────────────────────────────────

    if "error" in result:
        print(f"\n  ❌  AI Error: {result['error']}")
        if "raw" in result:
            print(f"\n  Raw response:\n{result['raw']}")
        return

    path = result.get("recommended_path", [])

    print_section(f"🎓 Recommended Learning Path  ({len(path)} courses)")
    for course in path:
        print_course_card(len(path), course)

    print(f"\n  ⏱️   Total Timeline : {result.get('total_timeline', 'N/A')}")

    print_section("💬 AI Summary")
    summary = result.get("summary", "No summary provided.")
    # Word-wrap at 50 chars
    words = summary.split()
    line = "      "
    for word in words:
        if len(line) + len(word) > 54:
            print(line)
            line = "      " + word + " "
        else:
            line += word + " "
    if line.strip():
        print(line)

    print("\n" + "═" * 55)
    print("   ✅  Test complete")
    print("═" * 55 + "\n")


if __name__ == "__main__":
    # Pass employee ID as argument e.g: python test_engine.py E001
    import sys
    emp_id = sys.argv[1] if len(sys.argv) > 1 else "E003"
    run_test(emp_id)