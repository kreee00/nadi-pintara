# 🌟 Nadi Pintara — AI-Assisted Learning Path Recommendation System

> **For UTP TTP Project** | Supervised by AP. Ts. Dr. Ahmad Sobri Bin Hashim

Nadi Pintara recommends personalised online courses to O&G employees based on their current skills and career goals. Key features:

- **Instant dashboard** — skill gap analysis loads immediately on login (no waiting for AI)
- **AI learning path** — Ollama-powered course recommendations load asynchronously in the background
- **Chatbot skill assessment** — conversational AI assesses skill levels through targeted questions, then saves results directly to your profile
- **Dark/light mode** — system-aware theme with zero flash on page navigation
- **25-course O&G catalogue** — covers Upstream, Downstream, Technical, and Corporate tracks

---

## 👋 Before You Start — What You Need to Install

You only need to install **4 things**. Don't worry, we'll walk through each one.

| # | What | Why |
|---|------|-----|
| 1 | Python | Runs the backend |
| 2 | Git | Downloads the project code |
| 3 | Ollama | Runs the AI on your laptop |
| 4 | Qwen2.5 model | The actual AI brain |

---

## 🪟 Setup Guide — Windows

### Step 1 — Install Python

1. Go to **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python"** button
3. Run the installer
4. ⚠️ **IMPORTANT:** On the first screen, tick the box that says **"Add Python to PATH"** before clicking Install

   ![Add Python to PATH checkbox](https://i.imgur.com/placeholder.png)

5. Click **Install Now** and wait for it to finish

To verify it worked, open **Command Prompt** (press `Windows key`, type `cmd`, press Enter) and type:
```
python --version
```
You should see something like `Python 3.12.x`. If you do, Python is ready ✅

---

### Step 2 — Install Git

1. Go to **https://git-scm.com/download/win**
2. Download the installer and run it
3. Just click **Next** on every screen — the default settings are fine
4. Click **Install** and wait

To verify, in Command Prompt type:
```
git --version
```
You should see `git version 2.x.x` ✅

---

### Step 3 — Download the Project

In Command Prompt, navigate to where you want to save the project. For example, your Desktop:
```
cd Desktop
```

Then download (clone) the project:
```
git clone https://github.com/erinazanie/nadi-pintara.git
```

Switch to the correct branch:
```
cd nadi-pintara
git checkout akram-staging
```

You should now see a folder called `nadi-pintara` on your Desktop 📁

---

### Step 4 — Set Up the Python Environment

Think of this as creating a "clean room" just for this project, so it doesn't mess with anything else on your laptop.

Still in Command Prompt (make sure you're inside the `nadi-pintara` folder):
```
python -m venv venv
```

Now activate it:
```
venv\Scripts\activate
```

You'll notice the line in Command Prompt now starts with `(venv)` — that means it's active ✅

Now install all the required packages:
```
pip install flask flask-cors requests python-dotenv
```

Wait for it to finish downloading. This may take 1–2 minutes.

---

### Step 5 — Install Ollama (The AI Engine)

1. Go to **https://ollama.com/download**
2. Click **Download for Windows**
3. Run the installer — just click through, defaults are fine
4. Once installed, Ollama runs quietly in the background automatically

To verify, open a **new** Command Prompt window and type:
```
ollama --version
```
You should see a version number ✅

---

### Step 6 — Download the AI Model

This downloads the Qwen2.5 AI model to your laptop (~4GB, do this on a good WiFi connection):
```
ollama pull qwen2.5:latest
```

Go grab a coffee ☕ — this takes 5–10 minutes.

Once done, test it works:
```
ollama run qwen2.5:latest "say hello"
```
If it replies with something, the AI is working ✅

Press `Ctrl + D` to exit the chat.

---

### Step 7 — Run the Project

Go back to your Command Prompt that has `(venv)` active. Make sure you're in the `nadi-pintara` folder, then:
```
python app.py
```

You should see:
```
* Running on http://127.0.0.1:5000
```

🎉 The backend is now running! Open your browser and go to:
```
http://localhost:5000
```

To test the AI recommendation engine, open this in your browser:
```
http://localhost:5000/recommend/E001
```

You should see a JSON response with course recommendations for the first employee.

---

### Step 8 — Stopping the Server

When you're done, go back to Command Prompt and press **`Ctrl + C`** to stop the server.

---

## 🐧 Setup Guide — Linux (Ubuntu/Debian)

### Step 1 — Install Python & Git

Open your Terminal and run:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git -y
```

Verify:
```bash
python3 --version
git --version
```

---

### Step 2 — Download the Project

```bash
cd ~/Desktop
git clone https://github.com/erinazanie/nadi-pintara.git
cd nadi-pintara
git checkout akram-staging
```

---

### Step 3 — Set Up Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install flask flask-cors requests python-dotenv
```

---

### Step 4 — Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify:
```bash
ollama --version
```

---

### Step 5 — Download the AI Model

```bash
ollama pull qwen2.5:latest
```

Test it:
```bash
ollama run qwen2.5:latest "say hello"
```

Press `Ctrl + D` to exit.

---

### Step 6 — Run the Project

```bash
python app.py
```

Open browser at **http://localhost:5000** ✅

---

## 📁 Project Structure (What Each File Does)

```
nadi-pintara/
│
├── data/
│   ├── roles_skills.json     ← 12 O&G job roles with required skill levels
│   ├── employees.json        ← Synthetic employee profiles for testing
│   ├── courses.json          ← 25-course O&G catalogue (Coursera, Udemy, etc.)
│   └── cache.json            ← Recommendation cache (auto-generated)
│
├── engine/
│   ├── gap_analyzer.py       ← Calculates missing skills vs. target role
│   ├── path_generator.py     ← Orchestrates full learning path generation
│   ├── llm_recommender.py    ← Builds prompts and calls the LLM
│   ├── llm_ollama.py         ← Ollama adapter (local AI)
│   ├── llm_gemini.py         ← Gemini adapter (cloud fallback)
│   └── chatbot_engine.py     ← Chatbot question bank, keyword scoring,
│                                assessment summary generation
│
├── templates/                ← Flask HTML templates (server-rendered)
│   ├── login.html            ← Employee selector / login page
│   ├── dashboard.html        ← Main dashboard (skill gaps + AI learning path)
│   └── courses.html          ← Browseable course catalogue
│
├── static/
│   ├── css/styles.css        ← Design system, dark/light mode, all component styles
│   └── js/main.js            ← Shared utilities (dark mode, toasts, progress bar)
│
├── app.py                    ← Flask server — all routes defined here
├── test_engine.py            ← Test suite for the AI engine
└── requirements.txt          ← Python package dependencies
```

---

## 🔗 API Endpoints (For Testing)

Once the server is running, you can open these links in your browser:

**Pages**

| URL | What it does |
|-----|-------------|
| `http://localhost:5000/` | Redirects to login |
| `http://localhost:5000/login` | Employee selector / login page |
| `http://localhost:5000/dashboard` | Main dashboard |
| `http://localhost:5000/courses-page` | Course catalogue |

**Data API** (GET)

| URL | What it does |
|-----|-------------|
| `http://localhost:5000/employees` | List all employee profiles |
| `http://localhost:5000/roles` | List all job role skill requirements |
| `http://localhost:5000/courses` | List all courses |
| `http://localhost:5000/employee/E001` | Get a single employee profile |
| `http://localhost:5000/employee/E001/gap` | Get skill gaps instantly (no LLM, <100ms) |
| `http://localhost:5000/health` | Server + LLM provider status |

**Recommendation API**

| URL | Method | What it does |
|-----|--------|-------------|
| `/recommend/E001` | GET | Full AI recommendation for Employee 1 |
| `/recommend/custom` | POST | AI recommendation for a custom profile |

**Chatbot API**

| URL | Method | What it does |
|-----|--------|-------------|
| `/chatbot/message` | POST | Send a skill assessment question/answer |
| `/chatbot/summarize` | POST | Generate AI summary of assessment results |

---

## ❓ Common Problems & Fixes

**"python is not recognized as a command"**
> You forgot to tick "Add Python to PATH" during installation. Uninstall Python and reinstall — make sure to tick that box.

**"(venv) disappeared from my Command Prompt"**
> You opened a new Command Prompt window. Just run `venv\Scripts\activate` again from inside the project folder.

**The AI is taking too long to respond**
> Ollama can take 1–2 minutes on the first run. This is normal — the model is loading into memory. Subsequent requests are faster. The dashboard still shows your skill gap data instantly while the AI loads.

**The chatbot asks a question but I don't see a response**
> Make sure Flask is running (`python app.py`). If the chatbot completes without an AI summary, the fallback template will still display your assessed skill levels correctly.

**"Connection refused" when opening localhost:5000**
> The server isn't running. Go back to Command Prompt and run `python app.py` again.

**Ollama gives an error when pulling the model**
> Make sure you have at least 5GB of free disk space and a stable internet connection.

---

## 👥 Team Members

| Name | Programme | Student ID |
|------|-----------|------------|
| Siti Faiqah Nurulain Binti Mohd Azman Froran | BBM | 22006398 |
| Abdul Hafiz Bin Mohd Noor Azman | BCS | 22007864 |
| Mohamad Akram Bin Mohd Faisal | BCS | 22006626 |
| Anis Nur Erina Binti Izani | BIT | 22010078 |

**Supervisor:** AP. Ts. Dr. Ahmad Sobri Bin Hashim

---

*If you're still stuck after following this guide, reach out to Akram or Harry on WhatsApp 😄*
