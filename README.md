# 📧 AI Mail App

A **free, offline, local AI-powered email assistant** built with Python Flask + Ollama LLM.
No API key. No credit card. Works 100% on your machine after setup.

---

## 🧱 Tech Stack

| Layer | Tool |
|---|---|
| Web Framework | Flask 3.0.3 |
| Auth | Flask-Login 0.6.3 |
| Password Hashing | Werkzeug 3.0.3 |
| AI (Local LLM) | Ollama (llama3.2:1b or phi3:mini) |
| HTTP to Ollama | Requests 2.32.3 |
| Database | SQLite (built into Python) |

---

## 🚀 Phase-by-Phase Setup

### ✅ Phase 1 — Project Setup (Current)

#### 1. Install Python 3.12+
Download from https://www.python.org/downloads/ (check "Add to PATH")

#### 2. Create & Activate Virtual Environment
```powershell
# Open PowerShell in the AI_Mail_App folder
cd "C:\Users\mathi\OneDrive\Documents\AI_Mail_App"

# Create venv
python -m venv venv

# Activate venv (Windows PowerShell)
venv\Scripts\activate

# You will see (venv) prefix in the terminal
```

#### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

#### 4. Run the App
```powershell
python run.py
```
Open browser → http://localhost:5000 → You should see **"AI Mail App — Phase 1 Running ✅"**

---

## 🤖 Install Ollama (Local AI — FREE)

Ollama runs LLMs locally on your PC. No internet needed after download.

### Step 1 — Download & Install Ollama
- Go to: **https://ollama.com/download**
- Click **Download for Windows**
- Run the installer (`OllamaSetup.exe`)
- Ollama installs as a background service automatically

### Step 2 — Pull a Free Model
Open PowerShell (Ollama must be installed):
```powershell
# Small, fast model (~900 MB) — RECOMMENDED to start
ollama pull llama3.2:1b

# OR ultra-small Microsoft model (~2 GB)
ollama pull phi3:mini
```

### Step 3 — Verify Ollama is Running
```powershell
# Check status — should return JSON with model list
curl http://localhost:11434/api/tags

# OR open in browser
# http://localhost:11434  →  shows "Ollama is running"
```

### Step 4 — Test the Model
```powershell
ollama run llama3.2:1b "Summarise this email: Hello, please submit your report by Friday."
```

> **Ollama API:** `http://localhost:11434` — No API key needed, works offline!

---

## 💰 Cost

| Item | Cost |
|---|---|
| Python | FREE |
| Flask, Flask-Login, Werkzeug | FREE (open source) |
| Ollama | FREE (open source) |
| llama3.2:1b model | FREE |
| Internet after setup | NOT REQUIRED |
| Credit card | NEVER NEEDED |

---

## 📋 Project Phases

| Phase | Description | Status |
|---|---|---|
| 1 | Project setup, venv, Flask skeleton, Ollama guide | ✅ Done |
| 2 | User Auth — Login / Register / Logout | 🔜 Next |
| 3 | Mail Inbox UI (mock emails) | 🔜 |
| 4 | Ollama AI — Summarise / Reply / Compose | 🔜 |
| 5 | Polish, Error Handling, Final Push | 🔜 |

---

## 📁 Project Structure

```
AI_Mail_App/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── routes/
│   │   └── __init__.py      # Routes package
│   ├── models/              # (Phase 2) User model
│   ├── services/            # (Phase 4) AI + Mail services
│   ├── templates/           # (Phase 2) HTML templates
│   └── static/              # (Phase 2) CSS/JS
├── venv/                    # Virtual environment (NOT in git)
├── run.py                   # Entry point: python run.py
├── requirements.txt         # pip dependencies
├── spec.yaml                # 📋 Project spec & phase tracker
├── .gitignore
└── README.md
```

---

## 🔗 GitHub

Repository: https://github.com/ADITHYANWUU2/AI_Mail_App
