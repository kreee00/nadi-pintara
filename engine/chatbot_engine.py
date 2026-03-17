"""
Chatbot Engine — hardcoded skill assessment questions + Ollama summary.
Pure Python scoring (no LLM per question). One Ollama call at the end.
"""

# ── Skill question bank ───────────────────────────────────────────────────────
# Each entry: list of dicts with keys: q (question text), scoring (keyword→level),
#             is_final (True = this question alone can close the assessment).

SKILL_QUESTIONS = {
    "Reservoir Engineering": [
        {
            "q": "Have you performed reservoir simulation or material balance calculations? Briefly describe.",
            "scoring": {"eclipse": 5, "cmg": 5, "petrel": 5, "simulation": 4, "material balance": 4,
                        "ipr": 4, "decline": 3, "basic": 2, "learning": 2, "no": 1, "never": 1},
            "is_final": False,
        },
        {
            "q": "Which reservoir modelling software have you used? (e.g. Eclipse, CMG, Petrel, MBAL)",
            "scoring": {"eclipse": 5, "cmg": 5, "petrel": 4, "mbal": 4, "prosper": 4,
                        "gap": 3, "excel": 2, "none": 1},
            "is_final": True,
        },
    ],
    "Drilling Engineering": [
        {
            "q": "Have you designed or supervised drilling programmes? What was your role?",
            "scoring": {"designed": 5, "supervised": 4, "lead": 4, "wellbore": 4, "casing": 4,
                        "bit": 3, "assisted": 3, "reviewed": 3, "basic": 2, "theoretical": 2, "no": 1},
            "is_final": False,
        },
        {
            "q": "Are you familiar with well control procedures and BOP testing?",
            "scoring": {"well control": 5, "bop": 4, "kick": 4, "certified": 4, "iadc": 5,
                        "familiar": 3, "aware": 2, "no": 1, "not": 1},
            "is_final": True,
        },
    ],
    "Production Optimization": [
        {
            "q": "Have you used nodal analysis or production surveillance tools to optimise well output?",
            "scoring": {"nodal": 5, "prosper": 4, "gap": 4, "surveillance": 4, "choke": 3,
                        "optimis": 4, "lift": 4, "basic": 2, "no": 1, "not": 1},
            "is_final": False,
        },
        {
            "q": "Describe a production bottleneck you identified and resolved.",
            "scoring": {"reduced": 4, "increased": 4, "identified": 3, "resolved": 4, "implemented": 4,
                        "choke": 3, "compressor": 3, "never": 1, "no experience": 1},
            "is_final": True,
        },
    ],
    "Petroleum Geoscience": [
        {
            "q": "Have you interpreted seismic data or petrophysical logs? Describe your experience.",
            "scoring": {"seismic": 5, "petrophysics": 4, "log": 3, "petrel": 4, "interpretation": 4,
                        "kingdom": 4, "basic": 2, "academic": 2, "no": 1},
            "is_final": True,
        },
    ],
    "Python": [
        {
            "q": "What have you built or automated using Python? (e.g. data pipelines, ML models, scripts)",
            "scoring": {"machine learning": 5, "ml": 5, "deep learning": 5, "pandas": 4, "numpy": 4,
                        "automation": 4, "script": 3, "pipeline": 4, "api": 4, "basic": 2,
                        "hello world": 1, "learning": 2, "no": 1, "nothing": 1},
            "is_final": False,
        },
        {
            "q": "Are you comfortable with libraries like pandas, numpy, or scikit-learn?",
            "scoring": {"scikit": 5, "sklearn": 5, "tensorflow": 5, "pytorch": 5,
                        "pandas": 4, "numpy": 4, "matplotlib": 3, "familiar": 3, "basic": 2, "no": 1},
            "is_final": True,
        },
    ],
    "Well Completion": [
        {
            "q": "Have you been involved in well completion design or operations (e.g. perforating, gravel pack)?",
            "scoring": {"completion": 4, "perforat": 4, "gravel": 4, "sand control": 4, "frac": 4,
                        "stimulat": 4, "designed": 5, "supervised": 4, "basic": 2, "no": 1},
            "is_final": True,
        },
    ],
    "Fluid Mechanics": [
        {
            "q": "How have you applied fluid mechanics in your work? (e.g. flow assurance, hydraulics, pipelines)",
            "scoring": {"flow assurance": 5, "hydraulic": 4, "multiphase": 4, "olga": 5, "pipesim": 4,
                        "bernoulli": 3, "reynolds": 3, "pressure drop": 3, "basic": 2, "no": 1},
            "is_final": True,
        },
    ],
    "Data Analytics": [
        {
            "q": "What data analytics tools or techniques have you applied in a work context?",
            "scoring": {"power bi": 5, "tableau": 4, "python": 4, "r": 3, "sql": 3, "excel": 2,
                        "machine learning": 5, "statistics": 4, "dashboard": 3, "none": 1},
            "is_final": False,
        },
        {
            "q": "Have you built dashboards or performed statistical analysis for operational decisions?",
            "scoring": {"built": 4, "developed": 4, "deployed": 5, "statistical": 4, "regression": 4,
                        "some": 3, "basic": 2, "no": 1, "never": 1},
            "is_final": True,
        },
    ],
    "Asset Integrity": [
        {
            "q": "Have you conducted or managed integrity assessments for equipment or structures?",
            "scoring": {"integrity": 4, "inspection": 4, "corrosion": 4, "rbi": 5, "fitness for service": 5,
                        "api 580": 5, "nde": 4, "ndt": 4, "managed": 4, "conducted": 4, "basic": 2, "no": 1},
            "is_final": True,
        },
    ],
    "Stakeholder Management": [
        {
            "q": "Describe a situation where you managed competing stakeholder interests on a project.",
            "scoring": {"stakeholder": 4, "negotiat": 4, "alignment": 4, "executive": 4, "presented": 3,
                        "communicated": 3, "conflict": 3, "resolved": 4, "basic": 2, "no experience": 1},
            "is_final": True,
        },
    ],
    "Subsea Engineering": [
        {
            "q": "Have you worked on subsea systems design or operations (manifolds, flowlines, risers, ROV)?",
            "scoring": {"subsea": 4, "manifold": 4, "riser": 4, "flowline": 4, "rov": 4,
                        "umbilical": 4, "sps": 4, "designed": 5, "basic": 2, "no": 1},
            "is_final": True,
        },
    ],
    "Pipeline Integrity": [
        {
            "q": "Have you used inline inspection (ILI/pigging) or fitness-for-service assessments on pipelines?",
            "scoring": {"ili": 5, "pigging": 4, "fitness for service": 5, "corrosion": 3, "api 1160": 5,
                        "asme b31": 4, "defect": 3, "managed": 4, "familiar": 3, "no": 1},
            "is_final": True,
        },
    ],
    "Risk Assessment": [
        {
            "q": "What risk assessment methodologies have you applied? (e.g. HAZOP, LOPA, QRA, bow-tie)",
            "scoring": {"hazop": 5, "lopa": 5, "qra": 5, "bow-tie": 4, "bowtie": 4,
                        "fmea": 4, "facilitated": 5, "participated": 3, "risk matrix": 3,
                        "basic": 2, "none": 1},
            "is_final": True,
        },
    ],
    "HSSE Compliance": [
        {
            "q": "How have you ensured HSSE compliance in your day-to-day work or projects?",
            "scoring": {"audit": 4, "compliance": 4, "ptw": 4, "permit to work": 4, "incident": 3,
                        "near miss": 3, "toolbox": 3, "safety walk": 3, "managed": 4, "basic": 2, "no": 1},
            "is_final": True,
        },
    ],
    "Regulatory Compliance": [
        {
            "q": "Have you worked directly with regulators or managed regulatory submissions/approvals?",
            "scoring": {"dosh": 5, "petronas": 4, "doe": 4, "approval": 4, "submission": 4,
                        "regulatory": 4, "managed": 4, "assisted": 3, "aware": 2, "no": 1},
            "is_final": True,
        },
    ],
    "Refinery Process Control": [
        {
            "q": "Have you operated or optimised refinery units (CDU, FCC, HDS)? Describe your role.",
            "scoring": {"cdu": 5, "fcc": 5, "hds": 4, "dcs": 4, "pcs": 4, "apc": 5,
                        "optimis": 4, "operated": 3, "monitored": 3, "basic": 2, "no": 1},
            "is_final": True,
        },
    ],
    "Plant Operations": [
        {
            "q": "Have you been responsible for safe, efficient operations of a process plant or facility?",
            "scoring": {"operated": 4, "shift": 4, "plant": 4, "startup": 4, "shutdown": 4,
                        "responsible": 4, "monitored": 3, "assisted": 3, "basic": 2, "no": 1},
            "is_final": True,
        },
    ],
    "Process Safety Management": [
        {
            "q": "Have you participated in or led PSM elements like MOC, PHA, or PSI activities?",
            "scoring": {"moc": 5, "pha": 5, "psi": 4, "psr": 4, "led": 5, "facilitated": 4,
                        "participated": 3, "aware": 2, "no": 1},
            "is_final": True,
        },
    ],
    "HAZOP": [
        {
            "q": "Have you been a HAZOP leader, scribe, or team member? Describe your experience.",
            "scoring": {"leader": 5, "facilitated": 5, "scribe": 4, "team member": 3, "participated": 3,
                        "certified": 5, "attended": 2, "aware": 2, "no": 1},
            "is_final": True,
        },
    ],
    "Turnaround Management": [
        {
            "q": "Have you been involved in planning or executing a major plant turnaround (TAR)?",
            "scoring": {"managed": 5, "led": 5, "planned": 4, "turnaround": 4, "tar": 4,
                        "scope": 3, "involved": 3, "assisted": 3, "aware": 2, "no": 1},
            "is_final": True,
        },
    ],
    "LNG Operations": [
        {
            "q": "Have you worked in LNG liquefaction, storage, or regasification facilities?",
            "scoring": {"liquefaction": 5, "regasification": 5, "cryogenic": 4, "lng": 4,
                        "train": 4, "operated": 4, "managed": 4, "studied": 2, "basic": 2, "no": 1},
            "is_final": True,
        },
    ],
    "Incident Investigation": [
        {
            "q": "Have you led or been part of an incident investigation team? What methodology was used?",
            "scoring": {"led": 5, "root cause": 5, "rca": 5, "taproot": 5, "bow-tie": 4,
                        "participated": 3, "aware": 2, "no": 1},
            "is_final": True,
        },
    ],
    "SAP ERP": [
        {
            "q": "Which SAP modules have you used? (e.g. PM, MM, SD, FICO)",
            "scoring": {"pm": 4, "mm": 4, "sd": 4, "fico": 4, "ps": 4, "super user": 5,
                        "daily": 4, "basic": 2, "entry": 2, "no": 1, "never": 1},
            "is_final": True,
        },
    ],
    "Project Management": [
        {
            "q": "What is the largest project you have managed in terms of budget or team size?",
            "scoring": {"million": 4, "billion": 5, "team": 3, "pmp": 5, "prince2": 4,
                        "led": 4, "managed": 4, "schedule": 3, "small": 2, "no": 1},
            "is_final": False,
        },
        {
            "q": "Are you PMP certified or have you used formal PM methodologies like PMBOK or PRINCE2?",
            "scoring": {"pmp": 5, "prince2": 4, "pmbok": 4, "certified": 4, "agile": 3,
                        "familiar": 3, "no": 1},
            "is_final": True,
        },
    ],
    "Contract Management": [
        {
            "q": "Have you drafted, negotiated, or administered commercial contracts? Describe your role.",
            "scoring": {"negotiated": 5, "drafted": 5, "administered": 4, "fidic": 5, "nec": 4,
                        "reviewed": 3, "assisted": 3, "aware": 2, "no": 1},
            "is_final": True,
        },
    ],
    "Power BI": [
        {
            "q": "Have you built Power BI reports or dashboards for operational or management use?",
            "scoring": {"built": 4, "developed": 4, "deployed": 5, "dax": 5, "power query": 4,
                        "directquery": 4, "used": 3, "basic": 2, "no": 1, "never": 1},
            "is_final": True,
        },
    ],
    "Machine Learning": [
        {
            "q": "Have you trained and deployed ML models in a production or operational context?",
            "scoring": {"deployed": 5, "production": 5, "trained": 4, "scikit": 4, "tensorflow": 5,
                        "pytorch": 5, "xgboost": 4, "regression": 3, "basic": 2, "no": 1, "never": 1},
            "is_final": True,
        },
    ],
    "HSE Management": [
        {
            "q": "Have you been responsible for setting HSE strategy or managing an HSE team?",
            "scoring": {"managed": 5, "led": 5, "strategy": 5, "hse manager": 5, "team": 4,
                        "budget": 4, "kpi": 3, "assisted": 3, "familiar": 2, "no": 1},
            "is_final": True,
        },
    ],
    "Crisis Management": [
        {
            "q": "Have you activated or participated in an emergency response or crisis management plan?",
            "scoring": {"activated": 5, "led": 5, "incident commander": 5, "eoc": 4,
                        "participated": 3, "trained": 3, "drilled": 3, "aware": 2, "no": 1},
            "is_final": True,
        },
    ],
    "Statistics": [
        {
            "q": "Have you applied statistical methods (regression, hypothesis testing, SPC) in your work?",
            "scoring": {"regression": 4, "hypothesis": 4, "spc": 4, "minitab": 4, "anova": 4,
                        "r": 3, "python": 3, "basic": 2, "no": 1, "never": 1},
            "is_final": True,
        },
    ],
}


# ── Scoring helper ────────────────────────────────────────────────────────────

def _score_answer(answer: str, question_config: dict) -> int:
    """Return skill level 1-5 by keyword matching. Falls back to length heuristic."""
    answer_lower = answer.lower()
    scoring = question_config.get("scoring", {})
    max_score = 0
    for keyword, level in scoring.items():
        if keyword.lower() in answer_lower:
            max_score = max(max_score, level)
    if max_score == 0:
        words = len(answer.split())
        if words > 25:
            return 3
        elif words > 8:
            return 2
        else:
            return 1
    return max_score


# ── Core chatbot logic ────────────────────────────────────────────────────────

def process_chatbot_message(data: dict) -> dict:
    """
    Stateless per-call handler.
    Receives: { skill, question_index, answer, conversation_history }
    Returns:  { is_complete, question, question_index, conversation_history }
              or { is_complete: True, skill_level_assigned, conversation_history }
    """
    skill = data.get("skill", "")
    question_index = data.get("question_index", 0)
    answer = data.get("answer")
    history = list(data.get("conversation_history", []))

    questions = SKILL_QUESTIONS.get(skill)
    if not questions:
        return {"is_complete": True, "skill_level_assigned": 3, "conversation_history": history}

    # First call — return first question without scoring
    if answer is None:
        return {
            "is_complete": False,
            "question": questions[0]["q"],
            "question_index": 0,
            "conversation_history": history,
        }

    # Score current answer
    current_q = questions[question_index] if question_index < len(questions) else questions[-1]
    score = _score_answer(answer, current_q)
    history.append({"q_idx": question_index, "answer": answer, "score": score})

    is_last = question_index >= len(questions) - 1
    is_decisive = score >= 4 or score <= 1

    if is_decisive or is_last:
        all_scores = [h.get("score", 3) for h in history]
        final_level = max(1, min(5, round(sum(all_scores) / len(all_scores))))
        return {
            "is_complete": True,
            "skill_level_assigned": final_level,
            "conversation_history": history,
        }

    # More questions available
    next_idx = question_index + 1
    return {
        "is_complete": False,
        "question": questions[next_idx]["q"],
        "question_index": next_idx,
        "conversation_history": history,
    }


# ── Ollama summary ────────────────────────────────────────────────────────────

def generate_assessment_summary(data: dict) -> dict:
    """
    One Ollama call to summarise the assessment.
    Falls back to template string if Ollama is unavailable.
    """
    assessed = data.get("assessed_skills", {})
    employee_name = data.get("employee_name", "the employee")
    current_role = data.get("current_role", "their current role")
    target_role = data.get("target_role", "their target role")

    if not assessed:
        return {"summary": "Assessment complete. No skills were evaluated."}

    n = len(assessed)
    sorted_skills = sorted(assessed.items(), key=lambda x: x[1], reverse=True)
    top_skill = sorted_skills[0][0] if sorted_skills else "—"
    low_skill = sorted_skills[-1][0] if sorted_skills else "—"

    fallback = (
        f"Assessment complete. {n} skill{'s' if n != 1 else ''} evaluated. "
        f"Strongest: {top_skill} (Level {assessed.get(top_skill, '?')}). "
        f"Focus area: {low_skill} (Level {assessed.get(low_skill, '?')})."
    )

    try:
        from engine.llm_ollama import ask_ollama

        skills_str = ", ".join(f"{k}: {v}/5" for k, v in assessed.items())
        prompt = (
            f"Write a 2-sentence career development summary for {employee_name} "
            f"({current_role} → {target_role}). "
            f"Assessed skill levels: {skills_str}. "
            "Be encouraging and specific. No bullet points."
        )
        result = ask_ollama(prompt)
        if result:
            return {"summary": result.strip()}
    except Exception:
        pass

    return {"summary": fallback}
