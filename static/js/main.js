/* ═══════════════════════════════════════════════
   NADI PINTARA — Shared JS Utilities
   main.js
═══════════════════════════════════════════════ */

/* ── Dark Mode ──────────────────────────────────────────── */
(function initDarkMode() {
  const saved = localStorage.getItem('np-theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (saved === 'dark' || (!saved && prefersDark)) {
    document.documentElement.classList.add('dark');
  }
})();

document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('darkToggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      const isDark = document.documentElement.classList.toggle('dark');
      localStorage.setItem('np-theme', isDark ? 'dark' : 'light');
    });
  }

  // Fade-up on scroll
  initFadeObserver();
});

/* ── Top Progress Bar ───────────────────────────────────── */
let progressTimer = null;

function setTopProgress(pct) {
  const bar = document.getElementById('top-progress');
  if (!bar) return;
  clearTimeout(progressTimer);
  bar.style.opacity = '1';
  bar.style.width = pct + '%';
  if (pct >= 100) {
    progressTimer = setTimeout(() => {
      bar.style.opacity = '0';
      setTimeout(() => { bar.style.width = '0%'; }, 400);
    }, 600);
  }
}

/* ── Toast Notifications ────────────────────────────────── */
function showToast(icon, message, duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `
    <span class="toast-icon">${icon}</span>
    <span style="flex:1">${message}</span>
  `;

  // Add pulse dot for AI processing toasts
  if (icon === '🤖') {
    toast.innerHTML = `
      <div class="toast-dot"></div>
      <span style="flex:1">${message}</span>
    `;
  }

  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('leaving');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/* ── Intersection Observer (fade-up) ────────────────────── */
function initFadeObserver() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.fade-up').forEach(el => observer.observe(el));
}

/* ── Add /courses route to Flask app.py ─────────────────── */
// NOTE FOR DEVELOPER: Add this route to app.py:
//
// @app.route("/courses", methods=["GET"])
// def get_courses():
//     courses = load_json("data/courses.json")
//     return jsonify(courses)
//
// Also update your Flask routes to serve these HTML templates:
//
// @app.route("/")
// @app.route("/dashboard")
// def dashboard():
//     return render_template("dashboard.html")
//
// @app.route("/courses-page")
// def courses_page():
//     return render_template("courses.html")
