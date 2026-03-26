import json
import os
import time

CACHE_FILE = "data/analytics_cache.json"
CACHE_TTL  = 3600  # 1 hour


# ── JSON helpers ──────────────────────────────────────────────────────────────

def load_json(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


# ── Core computation ──────────────────────────────────────────────────────────

def compute_readiness(employee, roles_data):
    """Return (readiness_pct, gaps_dict) for an employee towards their target role."""
    target_role = employee.get("target_role")
    if not target_role or target_role not in roles_data:
        return 100.0, {}

    required = roles_data[target_role]["required_skills"]
    current  = employee.get("current_skills", {})

    gaps   = {}
    scores = []
    for skill, req_level in required.items():
        curr_level = current.get(skill, 0)
        scores.append(min(curr_level / req_level, 1.0))
        if curr_level < req_level:
            gaps[skill] = {
                "current":  curr_level,
                "required": req_level,
                "gap":      req_level - curr_level,
            }

    readiness_pct = round((sum(scores) / len(scores)) * 100, 1) if scores else 100.0
    return readiness_pct, gaps


def compute_workforce_analytics():
    """Compute full workforce analytics. HR employees are excluded from the analysis."""
    employees = load_json("data/employees.json")
    roles     = load_json("data/roles_skills.json")
    courses   = load_json("data/courses.json")

    # Exclude HR employees — they are the audience, not the analysed workforce
    workforce = [e for e in employees if not e.get("is_hr")]

    # ── Per-employee enrichment ───────────────────────────────────────────────
    enriched = []
    for emp in workforce:
        readiness_pct, gaps = compute_readiness(emp, roles)
        enriched.append({
            "id":               emp["id"],
            "name":             emp["name"],
            "department":       emp["department"],
            "current_role":     emp["current_role"],
            "target_role":      emp["target_role"],
            "years_experience": emp["years_experience"],
            "readiness_pct":    readiness_pct,
            "gap_count":        len(gaps),
            "gaps":             gaps,
        })

    # ── Summary KPIs ──────────────────────────────────────────────────────────
    total         = len(enriched)
    avg_readiness = round(sum(e["readiness_pct"] for e in enriched) / total, 1) if total else 0
    fully_ready   = sum(1 for e in enriched if e["gap_count"] == 0)
    total_gaps    = sum(e["gap_count"] for e in enriched)

    high_count   = sum(1 for e in enriched if e["readiness_pct"] >= 80)
    medium_count = sum(1 for e in enriched if 50 <= e["readiness_pct"] < 80)
    low_count    = sum(1 for e in enriched if e["readiness_pct"] < 50)

    # ── Skill gap aggregation ─────────────────────────────────────────────────
    skill_gap_map = {}
    for emp in enriched:
        for skill, info in emp["gaps"].items():
            if skill not in skill_gap_map:
                skill_gap_map[skill] = {"total_gap": 0, "affected_count": 0}
            skill_gap_map[skill]["total_gap"]      += info["gap"]
            skill_gap_map[skill]["affected_count"] += 1

    skill_gaps = sorted(
        [
            {
                "skill":              skill,
                "avg_gap":            round(d["total_gap"] / d["affected_count"], 2),
                "total_gap":          d["total_gap"],
                "employees_affected": d["affected_count"],
            }
            for skill, d in skill_gap_map.items()
        ],
        key=lambda x: x["total_gap"],
        reverse=True,
    )

    # ── Department breakdown ──────────────────────────────────────────────────
    dept_map = {}
    for emp in enriched:
        dept = emp["department"]
        if dept not in dept_map:
            dept_map[dept] = {"employees": [], "skill_gap_map": {}}
        dept_map[dept]["employees"].append(emp)
        for skill, info in emp["gaps"].items():
            sgm = dept_map[dept]["skill_gap_map"]
            if skill not in sgm:
                sgm[skill] = {"total_gap": 0, "count": 0}
            sgm[skill]["total_gap"] += info["gap"]
            sgm[skill]["count"]     += 1

    departments = {}
    for dept, data in dept_map.items():
        emps    = data["employees"]
        avg_r   = round(sum(e["readiness_pct"] for e in emps) / len(emps), 1)
        d_skills = sorted(
            [
                {
                    "skill":              skill,
                    "avg_gap":            round(sd["total_gap"] / sd["count"], 2),
                    "employees_affected": sd["count"],
                }
                for skill, sd in data["skill_gap_map"].items()
            ],
            key=lambda x: x["avg_gap"],
            reverse=True,
        )
        departments[dept] = {
            "employee_count":    len(emps),
            "avg_readiness_pct": avg_r,
            "top_gaps":          d_skills[:5],
        }

    # ── Target role breakdown ─────────────────────────────────────────────────
    role_map = {}
    for emp in enriched:
        role = emp["target_role"]
        if role not in role_map:
            role_map[role] = []
        role_map[role].append(emp["readiness_pct"])

    target_roles = {
        role: {
            "employee_count":    len(r_list),
            "avg_readiness_pct": round(sum(r_list) / len(r_list), 1),
        }
        for role, r_list in role_map.items()
    }

    # ── Training alignment ────────────────────────────────────────────────────
    critical_skills = {item["skill"] for item in skill_gaps[:10]}
    course_alignment = []
    for course in courses:
        covered          = set(course.get("skills_covered", []))
        critical_covered = covered & critical_skills
        if not critical_covered:
            continue
        employees_helped = sum(
            1 for emp in enriched
            if critical_covered & set(emp["gaps"].keys())
        )
        course_alignment.append({
            "course_id":               course["id"],
            "title":                   course["title"],
            "provider":                course["provider"],
            "critical_skills_covered": len(critical_covered),
            "skills_covered":          sorted(critical_covered),
            "employees_helped":        employees_helped,
        })

    course_alignment.sort(
        key=lambda x: (x["employees_helped"], x["critical_skills_covered"]),
        reverse=True,
    )

    return {
        "summary": {
            "total_employees":       total,
            "avg_readiness_pct":     avg_readiness,
            "fully_ready":           fully_ready,
            "total_gaps":            total_gaps,
            "avg_gaps_per_employee": round(total_gaps / total, 1) if total else 0,
            "readiness_bands": {
                "high":   high_count,
                "medium": medium_count,
                "low":    low_count,
            },
        },
        "skill_gaps":         skill_gaps,
        "departments":        departments,
        "target_roles":       target_roles,
        "training_alignment": course_alignment[:8],
        "employees":          enriched,
    }


# ── Cache helpers ─────────────────────────────────────────────────────────────

def _read_cache():
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return None


def _write_cache(data):
    data["_cached_at"] = time.time()
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)


def get_or_compute_analytics():
    """Return cached analytics if fresh, otherwise compute, cache, and return."""
    cached = _read_cache()
    if cached and (time.time() - cached.get("_cached_at", 0)) < CACHE_TTL:
        return cached, False  # (data, was_refreshed)
    data = compute_workforce_analytics()
    _write_cache(data)
    return data, True


def refresh_analytics_cache():
    """Force-recompute analytics, persist to cache, and return fresh data."""
    data = compute_workforce_analytics()
    _write_cache(data)
    return data
