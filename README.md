# 🌟 Nadi Pintara — AI-Assisted Learning Path Recommendation System

> **For UTP TTP Project** | Supervised by AP. Ts. Dr. Ahmad Sobri Bin Hashim

This system recommends personalised online courses to employees based on their current skills and career goals — powered by a locally-running AI (no internet subscription needed).

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
│   ├── roles_skills.json     ← Defines what skills each job role needs
│   ├── employees.json        ← Synthetic employee profiles for testing
│   └── courses.json          ← Online course catalogue (Coursera, Udemy, etc.)
│
├── engine/
│   ├── gap_analyzer.py       ← Calculates what skills the employee is missing
│   ├── llm_recommender.py    ← Talks to the Qwen2.5 AI to get recommendations
│   └── path_generator.py     ← Puts it all together into a learning path
│
├── app.py                    ← The main server (start here!)
├── test_engine.py            ← Quick test to make sure AI is working
└── requirements.txt          ← List of Python packages needed
```

---

## 🔗 API Endpoints (For Testing)

Once the server is running, you can open these links in your browser:

| URL | What it does |
|-----|-------------|
| `http://localhost:5000/` | Check if server is running |
| `http://localhost:5000/employees` | See all employee profiles |
| `http://localhost:5000/roles` | See all job role frameworks |
| `http://localhost:5000/recommend/E001` | Get AI recommendation for Employee 1 |
| `http://localhost:5000/recommend/E002` | Get AI recommendation for Employee 2 |
| `http://localhost:5000/recommend/E003` | Get AI recommendation for Employee 3 |

---

## ❓ Common Problems & Fixes

**"python is not recognized as a command"**
> You forgot to tick "Add Python to PATH" during installation. Uninstall Python and reinstall — make sure to tick that box.

**"(venv) disappeared from my Command Prompt"**
> You opened a new Command Prompt window. Just run `venv\Scripts\activate` again from inside the project folder.

**The AI is taking too long to respond**
> Qwen2.5 can take 1–2 minutes on the first run. This is normal — the AI is loading into memory. Subsequent requests are faster.

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
