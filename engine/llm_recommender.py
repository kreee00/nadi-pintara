"""
llm_recommender.py
Unified LLM interface for Nadi Pintara.

Reads LLM_PROVIDER from .env and routes all calls to the correct backend.
Supported providers:
    gemini  — Google Gemini API (requires GEMINI_API_KEY)
    ollama  — Local Ollama server (requires Ollama running on localhost)

Usage (anywhere in the project):
    from engine.llm_recommender import get_recommendations, generate_summary
"""

import os
import json
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

# ── Provider config ───────────────────────────────────────────────────────────

PROVIDER     = os.getenv("LLM_PROVIDER", "gemini").lower().strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_KEY   = os.getenv("GEMINI_API_KEY", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL",  "llama3.2:3b")
OLLAMA_URL   = "http://localhost:11434/api/generate"

print(f"[LLM] Provider: {PROVIDER.upper()} | "
      f"Model: {GEMINI_MODEL if PROVIDER == 'gemini' else OLLAMA_MODEL}")


# ═══════════════════════════════════════════════════════════════════════════════
#  RAW API CALLS
# ═══════════════════════════════════════════════════════════════════════════════

def _call_gemini(prompt, retries=3, delay=5):
    """Send prompt to Gemini API. Returns raw text or None on failure."""
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=GEMINI_KEY)
    except Exception as e:
        print(f"[Gemini] SDK init failed: {e}")
        return None

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                    max_output_tokens=1024
                )
            )
            return response.text
        except Exception as e:
            err = str(e)
            if "503" in err or "UNAVAILABLE" in err:
                if attempt < retries - 1:
                    print(f"[Gemini] Busy, retrying in {delay}s... "
                          f"(attempt {attempt + 1}/{retries})")
                    time.sleep(delay)
                else:
                    print("[Gemini] Still unavailable after retries.")
                    return None
            else:
                print(f"[Gemini] Error: {err}")
                return None


def _call_ollama(prompt, retries=2):
    """Send prompt to local Ollama server. Returns raw text or None on failure."""
    for attempt in range(retries):
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model":  OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature":    0,
                        "top_p":          0.1,
                        "num_thread":     4,
                        "num_ctx":        1024,
                        "num_predict":    256,
                        "repeat_penalty": 1.2,
                        "use_mmap":       True,
                    }
                },
                timeout=45
            )
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.ConnectionError:
            print("[Ollama] Not running. Start with: ollama serve")
            return None
        except (requests.exceptions.Timeout,
                requests.exceptions.RequestException) as e:
            if attempt < retries - 1:
                print(f"[Ollama] Attempt {attempt + 1} failed, retrying... ({e})")
            else:
                print(f"[Ollama] Failed after {retries} attempts.")
                return None


def _ask(prompt):
    """Route prompt to the active provider. Returns raw text or None."""
    if PROVIDER == "ollama":
        return _call_ollama(prompt)
    return _call_gemini(prompt)


# ═══════════════════════════════════════════════════════════════════════════════
#  SHARED PROMPT BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def _build_prompt(employee, skill_gaps, courses):
    """
    Lean prompt shared by both providers.
    LLM only needs to return course_id + why_relevant.
    Full course details are re-attached by _hydrate() after the call.
    """
    slim_courses = [
        {"id": c["id"], "title": c["title"], "skills": c["skills_covered"]}
        for c in courses
    ]
    top_3_gaps  = list(skill_gaps.items())[:3]
    gap_strings = [
        f"{s}: {d['current']}->{d['required']}"
        for s, d in top_3_gaps
    ]

    # Ollama benefits from a concrete few-shot example
    example = (
        '\n\nExample Output:\n'
        '{"recommended_path": [{"order": 1, "course_id": "C001", '
        '"why_relevant": "Covers the gap."}], '
        '"total_timeline": "3 months", "summary": "Focus on gaps."}'
        if PROVIDER == "ollama" else ""
    )

    return (
        f"Task: Pick 3 courses for this PETRONAS employee.\n"
        f"Employee: {employee['current_role']} -> {employee['target_role']}\n"
        f"Gaps: {', '.join(gap_strings)}\n\n"
        f"Courses:\n{json.dumps(slim_courses)}"
        f"{example}\n\n"
        f"Output JSON:\n"
        f'{{"recommended_path": [{{"order": 1, "course_id": "C001", '
        f'"why_relevant": "One sentence reason."}}], '
        f'"total_timeline": "...", "summary": "Two sentence summary."}}\n\n'
        f"Respond ONLY in valid JSON. Use only course_id and why_relevant."
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  PARSE & HYDRATE
# ═══════════════════════════════════════════════════════════════════════════════

def _parse(text):
    """Strip markdown fences and parse JSON. Returns dict."""
    if not text:
        return {"error": "Empty response"}
    text = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {"error": "Could not parse response", "raw": text}


def _hydrate(parsed, courses):
    """
    Re-attach full course details to the slim LLM output.
    LLM returns only course_id + why_relevant to save tokens.
    This function adds title, provider, url, duration, skills_addressed.
    """
    course_map = {c["id"]: c for c in courses}
    hydrated   = []

    for item in parsed.get("recommended_path", []):
        cid    = item.get("course_id", "")
        course = course_map.get(cid, {})
        hydrated.append({
            "order":            item.get("order", len(hydrated) + 1),
            "course_id":        cid,
            "course_title":     course.get("title",          "Unknown Course"),
            "provider":         course.get("provider",       "—"),
            "url":              course.get("url",             "#"),
            "duration":         course.get("duration",        "—"),
            "skills_addressed": course.get("skills_covered",  []),
            "why_relevant":     item.get("why_relevant",      ""),
        })

    parsed["recommended_path"] = hydrated
    return parsed


# ═══════════════════════════════════════════════════════════════════════════════
#  FALLBACK  (pure Python, no LLM)
# ═══════════════════════════════════════════════════════════════════════════════

def _fallback(skill_gaps, courses):
    """
    Rule-based fallback when the LLM is unavailable.
    Ranks courses by number of skill gaps they cover.
    Returns the same JSON shape as the LLM would.
    """
    print(f"[{PROVIDER.upper()}] Using rule-based fallback.")
    gap_skills = set(skill_gaps.keys())
    top_3      = sorted(
        courses,
        key=lambda c: len(set(c["skills_covered"]) & gap_skills),
        reverse=True
    )[:3]

    return {
        "recommended_path": [
            {
                "order":            i + 1,
                "course_id":        c["id"],
                "course_title":     c["title"],
                "provider":         c["provider"],
                "url":              c["url"],
                "duration":         c["duration"],
                "skills_addressed": list(set(c["skills_covered"]) & gap_skills),
                "why_relevant":     (
                    "Recommended based on skill gap match "
                    "(AI engine unavailable)"
                ),
            }
            for i, c in enumerate(top_3)
        ],
        "total_timeline": "Flexible",
        "summary": (
            "Courses selected automatically based on skill gap overlap. "
            "AI engine was unavailable."
        ),
        "source": "fallback",
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def get_recommendations(employee, skill_gaps, courses):
    """
    Main entry point. Called by path_generator.py.
    Returns a fully hydrated recommendation dict.
    """
    prompt = _build_prompt(employee, skill_gaps, courses)
    raw    = _ask(prompt)

    if raw is None:
        return _fallback(skill_gaps, courses)

    parsed = _parse(raw)

    if "error" in parsed:
        return _fallback(skill_gaps, courses)

    return _hydrate(parsed, courses)


def generate_summary(employee_name, current_role, target_role, assessed_skills):
    """
    Single LLM call to produce a 2-sentence career development summary.
    Called by chatbot_engine.py after skill assessment is complete.
    Returns a string, or None if the LLM is unavailable.
    """
    skills_str = ", ".join(f"{k}: {v}/5" for k, v in assessed_skills.items())
    prompt = (
        f"Write a 2-sentence career development summary for {employee_name} "
        f"({current_role} → {target_role}). "
        f"Assessed skill levels: {skills_str}. "
        "Be encouraging and specific. No bullet points."
    )
    raw = _ask(prompt)
    if not raw:
        return None

    # Strip any JSON wrapper the model may have added
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj.get("summary", raw)
    except Exception:
        pass
    return raw.strip()