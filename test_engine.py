#!/usr/bin/env python3
"""
Nadi Pintara — Live AI Engine Demo
UTP TTP Project Presentation

Usage:
    python test_engine.py           # interactive employee picker
    python test_engine.py E001      # run a specific employee directly
    python test_engine.py --all     # run all employees back-to-back
"""

import json, time, sys, threading, os, textwrap
from engine.gap_analyzer import load_json, calculate_skill_gap, prefilter_courses
from dotenv import load_dotenv
load_dotenv()

# ═══════════════════════════════════════════════
#  ANSI COLOR HELPERS
# ═══════════════════════════════════════════════

class C:
    RESET  = "\033[0m";  BOLD   = "\033[1m";  DIM    = "\033[2m"
    TEAL   = "\033[38;5;37m";  NAVY   = "\033[38;5;18m"
    GREEN  = "\033[38;5;40m";  RED    = "\033[38;5;196m"
    GOLD   = "\033[38;5;214m"; GREY   = "\033[38;5;245m"
    WHITE  = "\033[97m";       ORANGE = "\033[38;5;208m"
    BG_T   = "\033[48;5;23m";  BG_N   = "\033[48;5;17m"

def teal(s):   return f"{C.TEAL}{s}{C.RESET}"
def bold(s):   return f"{C.BOLD}{s}{C.RESET}"
def green(s):  return f"{C.GREEN}{s}{C.RESET}"
def red(s):    return f"{C.RED}{s}{C.RESET}"
def gold(s):   return f"{C.GOLD}{s}{C.RESET}"
def dim(s):    return f"{C.DIM}{s}{C.RESET}"
def grey(s):   return f"{C.GREY}{s}{C.RESET}"
def orange(s): return f"{C.ORANGE}{s}{C.RESET}"

def strip_ansi(s):
    import re
    return len(re.sub(r'\033\[[0-9;]*m', '', s))

# ═══════════════════════════════════════════════
#  PROVIDER DETECTION  (reads from .env)
# ═══════════════════════════════════════════════

def detect_provider():
    """
    Reads LLM_PROVIDER from .env and returns a display info dict.

    Supported values for LLM_PROVIDER:
      gemini  — Google Gemini  (GEMINI_API_KEY or AI_API_KEY, GEMINI_MODEL)
      openai  — OpenAI or any OpenAI-compatible API
                (OPENAI_API_KEY, OPENAI_MODEL, optional OPENAI_BASE_URL)
      ollama  — Local Ollama server  (OLLAMA_MODEL, no key needed)
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()

    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        return {
            "provider": "ollama",
            "label":    f"Ollama  ({model})",
            "model":    model,
            "endpoint": "http://localhost:11434/api/generate",
            "key_set":  True,   # no key needed for local
            "color_fn": teal,
        }

    if provider == "openai":
        model    = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        api_key  = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", "").strip() or "https://api.openai.com/v1"
        return {
            "provider": "openai",
            "label":    f"OpenAI-compatible  ({model})",
            "model":    model,
            "endpoint": base_url,
            "key_set":  bool(api_key),
            "color_fn": green,
        }

    # Default: Gemini
    model   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("AI_API_KEY", "")
    return {
        "provider": "gemini",
        "label":    f"Google Gemini  ({model})",
        "model":    model,
        "endpoint": f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "key_set":  bool(api_key),
        "color_fn": gold,
    }

# ═══════════════════════════════════════════════
#  SPINNER
# ═══════════════════════════════════════════════

class Spinner:
    FRAMES = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    def __init__(self, msg):
        self.msg  = msg
        self._on  = False
        self._t   = None
        self._s   = 0

    def _spin(self):
        i = 0
        while self._on:
            e = time.time() - self._s
            sys.stdout.write(f"\r  {teal(self.FRAMES[i % 10])}  {self.msg}  {dim(f'({e:.1f}s)')}   ")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

    def start(self):
        self._s  = time.time()
        self._on = True
        self._t  = threading.Thread(target=self._spin, daemon=True)
        self._t.start()

    def stop(self, ok=True):
        self._on = False
        self._t.join()
        e    = time.time() - self._s
        icon = green("✔") if ok else red("✘")
        sys.stdout.write(f"\r  {icon}  {self.msg}  {dim(f'({e:.1f}s)')}          \n")
        sys.stdout.flush()
        return e

# ═══════════════════════════════════════════════
#  LAYOUT
# ═══════════════════════════════════════════════

W  = 64
BW = W - 6

def hr(ch="═"):   print(teal(ch * W))
def thr(ch="─"):  print(dim(ch * W))
def blank():      print()

def section(title):
    blank(); thr()
    print(f"  {bold(teal(title))}")
    thr()

def step_tag(n, total, title):
    blank()
    tag = f" STEP {n}/{total} "
    print(f"  {C.BOLD}{C.BG_T}{C.WHITE}{tag}{C.RESET}  {bold(title)}")

def lbl(key, val, pad=4):
    print(f"{'':>{pad}}{grey(f'{key:<14}')} {val}")

def note(msg, indent=2):
    print(f"{'  ' * indent}{msg}")

# ═══════════════════════════════════════════════
#  SKILL BARS
# ═══════════════════════════════════════════════

BAR = 20

def skill_bar(skill, current, required=None):
    name   = f"{skill[:30]:<30}"
    filled = int((current / 5) * BAR)

    if required and current < required:
        gap      = required - current
        req_fill = int((required / 5) * BAR)
        bar  = (green("█" * filled)
              + red("▒" * (req_fill - filled))
              + dim("░" * (BAR - req_fill)))
        stat = red(f" {current}/{required}  gap:{gap}")
    elif required:
        bar  = green("█" * filled) + dim("░" * (BAR - filled))
        stat = green(f" {current}/{required}  ✔")
    else:
        bar  = teal("█" * filled) + dim("░" * (BAR - filled))
        stat = f" {current}/5"

    print(f"    {grey(name)} {bar}{stat}")

# ═══════════════════════════════════════════════
#  BOX DRAWING
# ═══════════════════════════════════════════════

def box_top(): print(f"  {dim('┌' + '─' * BW + '┐')}")
def box_bot(): print(f"  {dim('└' + '─' * BW + '┘')}")
def box_sep(): print(f"  {dim('├' + '─' * BW + '┤')}")

def box_row(text, color_fn=None):
    inner = BW - 2
    lines = textwrap.wrap(str(text), width=inner) or [""]
    for line in lines:
        display = color_fn(line) if color_fn else line
        pad = inner - len(line)
        print(f"  {dim('│')} {display}{' ' * pad} {dim('│')}")

# ═══════════════════════════════════════════════
#  TYPEWRITER
# ═══════════════════════════════════════════════

def typewrite(text, delay=0.016, indent=4, width=W - 8):
    pad = " " * indent
    for chunk in textwrap.wrap(text, width=width):
        sys.stdout.write(pad)
        for ch in chunk:
            sys.stdout.write(teal(ch) if ch not in (" ", ",", ".") else ch)
            sys.stdout.flush()
            time.sleep(delay)
        print()
        time.sleep(0.04)

# ═══════════════════════════════════════════════
#  PIPELINE DIAGRAM  (dynamic provider label)
# ═══════════════════════════════════════════════

def show_pipeline(pinfo):
    blank()
    print(f"  {bold('How the engine works:')}")
    blank()
    stages = [
        ("📂  Data Layer",    ["employees.json", "roles_skills.json", "courses.json"]),
        ("⚙️   Gap Analyser",  ["calculate_skill_gap()", "prefilter_courses()"]),
        ("🤖  AI Engine",     ["llm_recommender.py", pinfo["label"]]),
        ("🎓  Learning Path", ["ranked course list", "total timeline", "AI narrative"]),
    ]
    for i, (title, items) in enumerate(stages):
        if i > 0:
            print(f"         {dim('│')}")
            print(f"         {dim('▼')}")
        print(f"  {bold(title)}")
        for item in items:
            color = pinfo["color_fn"] if "AI Engine" in title and i == 2 else grey
            print(f"       {dim('·')} {color(item)}")
    blank()

# ═══════════════════════════════════════════════
#  PROVIDER INFO BOX
# ═══════════════════════════════════════════════

def show_provider_box(pinfo):
    blank()
    hr()
    print(f"  {bold('AI ENGINE CONFIGURATION')}")
    thr()
    blank()

    provider_display = pinfo["color_fn"](bold(pinfo["provider"].upper()))
    note(f"Provider  :  {provider_display}", indent=2)
    note(f"Model     :  {bold(pinfo['model'])}", indent=2)
    note(f"Endpoint  :  {grey(pinfo['endpoint'])}", indent=2)

    if pinfo["provider"] == "ollama":
        note(f"Mode      :  {teal('Local  (no API key needed, no internet)')}", indent=2)
    else:
        key_var = "OPENAI_API_KEY" if pinfo["provider"] == "openai" else "GEMINI_API_KEY"
        key_status = (green("✔  API key loaded") if pinfo["key_set"]
                      else red(f"✘  {key_var} not set in .env"))
        note(f"API Key   :  {key_status}", indent=2)

        if not pinfo["key_set"]:
            blank()
            note(red("⚠  Cloud provider selected but no API key found."), indent=2)
            note(dim(f"   Add {key_var}=your_key to your .env file."), indent=2)
            note(dim("   Or switch to LLM_PROVIDER=ollama in .env."), indent=2)
            blank()
            note(dim("   Continuing — will use fallback if API call fails."), indent=2)

    blank()
    hr()

# ═══════════════════════════════════════════════
#  PROMPT PREVIEW
# ═══════════════════════════════════════════════

def show_prompt(employee, gaps, n_filtered):
    blank()
    note(dim("Prompt sent to AI (abbreviated):"), indent=1)
    blank()
    top3    = list(gaps.items())[:3]
    gap_str = ", ".join(f"{k}: {v['current']}→{v['required']}" for k, v in top3)
    if len(gaps) > 3:
        gap_str += f", +{len(gaps) - 3} more"

    box_top()
    box_row("Task: Pick 3 courses for this PETRONAS employee.", color_fn=gold)
    box_sep()
    box_row(f"Employee : {employee['current_role']}")
    box_row(f"           → {employee['target_role']}")
    box_row(f"Gaps     : {gap_str}")
    box_row(f"Courses  : {n_filtered} pre-filtered from 25-course catalogue")
    box_sep()
    box_row('Output   : {"recommended_path":[...], "summary":"..."}')
    box_bot()

# ═══════════════════════════════════════════════
#  EMPLOYEE PICKER
# ═══════════════════════════════════════════════

def pick_employee(employees):
    blank(); section("SELECT EMPLOYEE FOR DEMO"); blank()
    for i, e in enumerate(employees, 1):
        num   = gold(f"[{i:>2}]")
        name  = bold(e["name"])
        route = f"{grey(e['current_role'])}  →  {teal(e['target_role'])}"
        print(f"  {num}  {name}")
        print(f"         {route}")
        blank()
    print(f"  {gold('[A]')}  Run {bold('all employees')} back-to-back")
    blank(); thr()
    while True:
        try:
            sys.stdout.write(f"\n  {teal('›')} Enter number (or A): ")
            sys.stdout.flush()
            ch = input().strip().upper()
            if ch == 'A':
                return None
            idx = int(ch) - 1
            if 0 <= idx < len(employees):
                return [employees[idx]["id"]]
        except (ValueError, EOFError):
            pass
        print(f"  {red('Invalid — try again.')}")

# ═══════════════════════════════════════════════
#  CORE DEMO FOR ONE EMPLOYEE
# ═══════════════════════════════════════════════

def demo_one(emp_id, employees, roles, courses, pinfo, seq, total):
    emp = next((e for e in employees if e["id"] == emp_id), None)
    if not emp:
        print(red(f"  ✘  Employee {emp_id} not found."))
        return

    blank(); hr()
    print(bold(teal(f"  DEMO {seq}/{total}  —  {emp['name']}  ({emp_id})")))
    hr()

    # ── STEP 1: Profile ──────────────────────────────────────────────────────
    step_tag(1, 5, "Employee Profile")
    blank()
    lbl("Name",       bold(emp["name"]))
    lbl("Department", emp["department"])
    lbl("Current",    bold(gold(emp["current_role"])))
    lbl("Target",     bold(teal(emp["target_role"])))
    lbl("Experience", f"{emp['years_experience']} years")
    lbl("Education",  emp.get("education", "N/A"))
    blank()
    note(grey("Current skill levels:"))
    blank()
    for skill, lvl in emp["current_skills"].items():
        skill_bar(skill, lvl)
    time.sleep(0.3)

    # ── STEP 2: Gap analysis ─────────────────────────────────────────────────
    step_tag(2, 5, "Skill Gap Analysis")
    sp = Spinner("Comparing current skills against target role requirements")
    sp.start()
    time.sleep(0.7)
    gaps, err = calculate_skill_gap(emp, roles)
    sp.stop()

    if err:
        print(red(f"  ✘  {err}"))
        return

    req_skills = roles.get(emp["target_role"], {}).get("required_skills", {})

    if not gaps:
        blank()
        note(green("✔  No skill gaps — employee already meets all requirements!"))
    else:
        blank()
        note(f"Target role : {bold(emp['target_role'])}")
        note(f"Result      : {red(bold(str(len(gaps)) + ' gap(s) found'))}")
        blank()
        note(grey("Gap breakdown  (green = current level, red = shortfall):"))
        blank()
        for skill, data in gaps.items():
            skill_bar(skill, data["current"], data["required"])

        met = [(s, v) for s, v in emp["current_skills"].items()
               if s in req_skills and s not in gaps]
        if met:
            blank()
            note(grey("Skills already at or above required level:"))
            blank()
            for skill, lvl in met:
                skill_bar(skill, lvl, req_skills[skill])

    # ── STEP 3: Pre-filter ───────────────────────────────────────────────────
    step_tag(3, 5, "Pre-filtering Course Catalogue")
    sp = Spinner("Scanning 25 courses for skill gap overlap")
    sp.start()
    time.sleep(0.5)
    relevant = prefilter_courses(gaps, courses, max_courses=8)
    sp.stop()

    blank()
    note(f"Selected {green(bold(str(len(relevant))))} / {len(courses)} courses "
         + dim(f"(top {len(relevant)} by gap coverage, sent to AI)"))
    blank()
    for c in relevant:
        overlap = sorted(set(c["skills_covered"]) & set(gaps.keys()))
        tags    = "  " + "  ".join(teal(f"[{s}]") for s in overlap) if overlap else ""
        title   = c["title"][:50]
        note(f"{dim('·')} {title}{tags}", indent=2)

    # ── STEP 4: Prompt ───────────────────────────────────────────────────────
    step_tag(4, 5, "Building AI Prompt")
    show_prompt(emp, gaps, len(relevant))

    # ── STEP 5: AI call ──────────────────────────────────────────────────────
    step_tag(5, 5, "AI Recommendation Engine")
    blank()

    # Dynamic provider info display
    provider_label = pinfo["color_fn"](bold(pinfo["provider"].upper()))
    note(f"Provider  :  {provider_label}", indent=2)
    note(f"Model     :  {bold(pinfo['model'])}", indent=2)
    note(f"Endpoint  :  {grey(pinfo['endpoint'])}", indent=2)

    if pinfo["provider"] == "ollama":
        note(f"Mode      :  {teal('Local — no internet required')}", indent=2)
    else:
        key_status = green("API key ✔") if pinfo["key_set"] else red("API key missing ✘")
        note(f"Auth      :  {key_status}", indent=2)

    blank()

    sp = Spinner(
        f"Waiting for {pinfo['provider'].upper()} to generate personalised recommendations"
    )
    sp.start()
    t0 = time.time()
    from engine.llm_recommender import get_recommendations
    result = get_recommendations(emp, gaps, relevant)
    elapsed = time.time() - t0
    sp.stop(ok="error" not in result)

    # Fallback detection
    is_fallback = (
        "error" in result or
        result.get("summary", "").lower().startswith("courses selected automatically") or
        result.get("source") == "fallback"
    )

    if is_fallback:
        blank()
        note(orange("⚡  AI engine unavailable — showing rule-based fallback"), indent=2)
        note(dim("   (pure Python skill-overlap scoring, no LLM call)"), indent=2)

    # ── RESULTS ───────────────────────────────────────────────────────────────
    if "error" in result and "recommended_path" not in result:
        blank()
        note(red(f"Error: {result['error']}"), indent=2)
        return

    path     = result.get("recommended_path", [])
    summary  = result.get("summary", "")
    timeline = result.get("total_timeline", "N/A")

    blank(); thr()
    print(f"  {bold(teal('RESULTS'))}"); thr(); blank()

    for course in path:
        box_top()
        box_row(f"#{course['order']}  {course['course_title']}", color_fn=bold)
        box_sep()
        box_row(f"Provider : {course.get('provider', '—')}")
        box_row(f"Duration : {course.get('duration', '—')}")
        box_row("Skills   : " + ", ".join(course.get("skills_addressed", [])))
        box_row("Why      : " + course.get("why_relevant", ""))
        box_bot()
        blank()

    addressed = {s for c in path for s in c.get("skills_addressed", [])}
    covered   = len(set(gaps.keys()) & addressed)

    print(f"  {gold('⏱')}  Timeline       : {bold(timeline)}")
    print(f"  {teal('🎯')} Gaps Addressed  : {bold(f'{covered}/{len(gaps)}')}")

    if is_fallback:
        print(f"  {orange('⚡')} Mode           : {orange('Fallback (no LLM)')}  |  {dim(f'{elapsed:.1f}s')}")
    else:
        mode_label = pinfo["color_fn"](f"Live — {pinfo['provider'].upper()}")
        print(f"  {green('🤖')} AI Response    : {mode_label}  |  {dim(f'{elapsed:.1f}s')}")

    # AI narrative
    blank(); thr()
    print(f"  {bold('AI Narrative')}  {dim('(typewriter output):')}")
    thr(); blank()

    if not summary or summary.strip() in ("", "No summary provided."):
        first   = emp["name"].split()[0]
        summary = (
            f"{first}'s profile shows strong foundational skills for the transition "
            f"to {emp['target_role']}. The recommended courses address {covered} of "
            f"{len(gaps)} identified skill gaps, building critical competencies within "
            f"the target timeline of {timeline}."
        )
        note(dim("(Model returned no narrative — showing computed summary)"), indent=2)
        blank()

    typewrite(summary, indent=4)
    blank()

# ═══════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════

def main():
    os.system("clear || cls")

    # Banner
    hr()
    blank()
    print(bold(teal("  🛢️   NADI PINTARA — AI Engine Live Demo")))
    print(dim("  UTP TTP Project  |  Supervised by AP. Ts. Dr. Ahmad Sobri"))
    blank()
    hr()

    # Detect provider from .env
    pinfo = detect_provider()
    show_provider_box(pinfo)

    # Load data
    blank()
    sp = Spinner("Loading data files (employees, roles, courses)")
    sp.start()
    time.sleep(0.4)
    BASE      = os.path.dirname(os.path.abspath(__file__))
    employees = load_json(os.path.join(BASE, "data/employees.json"))
    roles     = load_json(os.path.join(BASE, "data/roles_skills.json"))
    courses   = load_json(os.path.join(BASE, "data/courses.json"))
    sp.stop()

    note(
        f"  {green(str(len(employees)))} employees   "
        f"{green(str(len(roles)))} roles   "
        f"{green(str(len(courses)))} courses   loaded",
        indent=1
    )

    # Pipeline diagram
    show_pipeline(pinfo)

    # Determine which employees to run
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        ids = ([e["id"] for e in employees] if arg == "--all" else [arg])
    else:
        sel = pick_employee(employees)
        ids = sel if sel else [e["id"] for e in employees]

    # Run demos
    t_start = time.time()
    for i, eid in enumerate(ids, 1):
        demo_one(eid, employees, roles, courses, pinfo, i, len(ids))
        if i < len(ids):
            blank()
            note(dim("─── Press Enter to continue to next employee... ───"), indent=2)
            input()

    # Footer
    elapsed = time.time() - t_start
    blank(); hr()
    print(bold(teal(
        f"  ✔  Demo complete  —  {len(ids)} employee(s)  —  {elapsed:.1f}s total"
    )))
    hr(); blank()


if __name__ == "__main__":
    main()