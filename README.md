# 📧 AI Mail App — Intelligent Webmail Assistant

A modern, full-featured webmail client powered by **Python (Flask)**, **SQLite**, and **Google Gemini AI** (with local Ollama compatibility).

AI Mail App turns a standard webmail interface into an intelligent productivity copilot that drafts emails from natural language prompts, refines tone on demand, generates contextual subject lines, summarizes long message threads, suggests one-click smart replies, and automatically triages inbox priorities.

---

## 🎥 Video Demo & Screenshots

- **Live Demo Video & Project Assets:**  
  👉 **[Google Drive Demo Folder](https://drive.google.com/drive/folders/1tmASKIx1gSzLIToI8I9UrxFUjmFGaoKo)**  
  *(Contains the 4–5 minute video demonstration showcasing the AI assistant controlling the UI, drafting messages, adjusting tones, and triaging the inbox).*

---

## 🚀 1. How to Set It Up and Run It Locally

Follow these instructions to run the application fresh on any Windows machine:

### Prerequisites
- **Python 3.12+** installed from [python.org](https://www.python.org/downloads/) *(make sure to check "Add python.exe to PATH")*.
- A web browser (Chrome, Edge, Firefox).
- *(Optional)* A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey) — **Note: A pre-configured multi-key failover pool is already provided in `.env`**.

---

### Step-by-Step Installation

#### 1. Open PowerShell in the Project Directory
```powershell
cd "C:\Users\<YourUsername>\Documents\AI_Mail_App"
```

#### 2. Create and Activate the Virtual Environment
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment in PowerShell
venv\Scripts\activate

# You will see the (venv) prefix in your prompt
```

#### 3. Install Python Dependencies
```powershell
pip install -r requirements.txt
```

#### 4. Configure Environment Variables (`.env`)
The project comes with a `.env` file containing an automatic multi-key failover pool. To view or customize:
```ini
# .env
GEMINI_API_KEYS=key1,key2,key3...
GEMINI_MODEL=gemini-flash-latest
```

#### 5. Launch the Application
```powershell
python run.py
```

#### 6. Open in Your Browser
Visit: **[http://localhost:5000](http://localhost:5000)**

---

### Quick Demo Accounts
You can register new users anytime or use pre-configured test accounts:
- **Username:** `alice` | **Password:** `password123`
- **Username:** `bob` | **Password:** `password123`

---

## 🏛️ 2. Architecture Decisions and Trade-offs

During development, several key design choices and trade-offs were made to balance performance, reliability, security, and developer velocity:

### A. Single-Row Dual-Perspective Email Schema (SQLite)
- **Decision:** Instead of duplicating entire email records for both sender and recipient, a single row in the `emails` table stores both `folder` (recipient's perspective: inbox/trash) and `sender_folder` (sender's perspective: sent/trash/deleted).
- **Trade-off:**
  - *Benefits:* Halves disk footprint, eliminates sync bugs between sender and recipient versions of attachments, and simplifies message lifecycle management.
  - *Trade-off:* Requires conditional query logic (`folder = 'inbox' AND recipient_id = ?` vs `sender_folder = 'sent' AND sender_id = ?`).

### B. Multi-Key Auto-Failover API Pool Architecture
- **Decision:** Rather than relying on a single static API key, `ai/ai_helper.py` maintains an 11-key rotation pool with automatic failover.
- **Trade-off:**
  - *Benefits:* Eliminates sudden 429 (Resource Exhausted) disruptions during live demos or heavy use. If key #1 is rate-limited, the system seamlessly retries key #2 without user interruption.
  - *Trade-off:* Requires defensive error parsing and round-robin index synchronization.

### C. Strict Human-in-the-Loop Safety Principle
- **Decision:** The AI never automatically sends an email or performs destructive actions. All generated outputs (AI Drafts, Smart Replies, Tone Adjustments) pre-fill editable UI form fields.
- **Trade-off:**
  - *Benefits:* Completely eliminates the danger of AI hallucinations, unintended commitments, or offensive wording reaching real recipients. The user always retains final editorial authority.
  - *Trade-off:* Requires an extra user click to send rather than fully autonomous 1-click execution.

### D. Progressive Enhancement: AJAX with No-JS Form Fallbacks
- **Decision:** Features like Summarize, Tone Rewrite, and Smart Reply utilize client-side `fetch` for instantaneous, non-reloading UI updates, but backend routes maintain standard HTML form fallbacks.
- **Trade-off:**
  - *Benefits:* Instant feedback with live loading indicators while ensuring graceful degradation if JavaScript fails.

### E. AI-Assisted Disclaimer for Priority Triage
- **Decision:** Automatic priority classification is prominently labeled in the UI as *"AI-assisted classification — not a guaranteed spam/priority filter"*.
- **Trade-off:**
  - *Benefits:* Sets honest user expectations. LLMs lack personal inbox history and corporate context, so transparent labeling prevents over-reliance on heuristics.

---

## 🌟 3. Complete Feature Tour

| Feature Area | Capabilities |
|---|---|
| **Authentication** | User registration, login/logout, password hashing (scrypt via Werkzeug), session persistence. |
| **Webmail Simulator** | Inbox, Sent, Drafts, Trash folders, unread indicators, badge counters, and secure attachments (16MB limit). |
| **AI Draft Assistant** | Prompt-to-email generator (`"send project update to sir"`) &rarr; generates subject + formatted body. |
| **AI Tone Adjustment** | On-the-fly rewrite toolbar: **Professional**, **Friendly**, **Formal**, and **Concise** + instant **Undo**. |
| **Dynamic Subject Generator** | Context-aware button active only when subject is empty; summarizes email body into < 8 words. |
| **AI Email Summarizer** | Real-time 2–4 bullet point summary card displayed directly above message body. |
| **AI Smart Reply** | 3 context-aware response chips (Positive, Acknowledge, Reschedule) pre-filling reply with quoted headers. |
| **Automatic Priority Triage**| Real-time urgency classification into **🔴 High**, **🟡 Normal**, and **⚪ Low** priority badges. |
| **Search & Trash Lifecycle**| SQL full-text search by keyword, soft-delete to Trash, restore, and permanent deletion. |

---

## 🔮 4. What We'd Improve With More Time

If given an extended development cycle, the following enhancements would take the application to production grade:

1. **Real SMTP / IMAP Protocol Integration:**
   - Integrate standard email protocols (`aiosmtpd`, `imaplib`) or OAuth2 connectors (Gmail API, Microsoft Graph) to turn the application into a bridge for real-world personal and corporate inboxes.

2. **RAG & Vector Memory over User's Email History:**
   - Implement a local vector database (such as ChromaDB or SQLite-vec) to index previous email threads. This would allow the AI to draft replies matching the user's specific writing style and pull facts from past emails.

3. **Multi-Recipient CC / BCC & Contact Groups:**
   - Expand compose addressing to support multiple comma-separated recipients, CC, BCC, and address-book autocompletion.

4. **Edge Privacy: Fully Local SLM Mode with Zero-Network Guarantees:**
   - Add a toggle switch between cloud Gemini API and local Ollama (`llama3.2:1b` / `phi3:mini`) for users requiring air-gapped, zero-network privacy.

5. **End-to-End PGP Encryption:**
   - Add client-side cryptographic message signing and encryption for high-security environments.

6. **Progressive Web App (PWA) Offline Caching:**
   - Implement service workers and IndexedDB caching so users can browse their inbox and compose draft emails without an active internet connection.

---

## 📁 Repository Structure

```text
AI_Mail_App/
├── app/
│   ├── __init__.py          # Flask factory, 404/500 error handlers
│   ├── models/
│   │   └── user.py          # User authentication model & DB bridge
│   ├── routes/
│   │   ├── auth.py          # Register, Login, Logout routes
│   │   └── mail.py          # Core mail routes & AI endpoints
│   ├── static/
│   │   └── css/
│   │       └── style.css    # Complete dark theme, tone toolbar, responsive UI
│   └── templates/
│       ├── base.html        # Navbar, flash messages, base shell
│       ├── mail_layout.html # Sidebar navigation & search bar
│       ├── login.html       # User login page
│       ├── register.html    # User registration page
│       ├── inbox.html       # Inbox view with priority badges
│       ├── mail_list.html   # Sent, Drafts, Trash, Search list
│       ├── compose.html     # Compose with AI Assistant & Tone toolbar
│       ├── email_detail.html# Email view with AI Summarize & Smart Reply
│       ├── test_ai.html     # Interactive Gemini sandbox
│       ├── 404.html         # Custom 404 error page
│       └── 500.html         # Custom 500 error page
├── ai/
│   ├── __init__.py
│   └── ai_helper.py         # Multi-key Gemini failover client
├── uploads/                 # Secure file attachments directory
├── database.py              # SQLite schema, migrations, CRUD operations
├── spec.yaml                # Master specification & phase tracker
├── requirements.txt         # Python package dependencies
├── run.py                   # Application entry point
├── README.md                # Markdown documentation
└── README.docx              # Microsoft Word documentation version
```

---

## 📋 End-to-End Demo Checklist

Before presenting the project, execute this 5-minute walkthrough:

- [ ] **1. Start App:** Run `python run.py` &rarr; Navigate to `http://localhost:5000`.
- [ ] **2. Auth Flow:** Log in as `alice` (`password123`).
- [ ] **3. AI Compose Assistant:** Open Compose &rarr; Type `"send project status report to team"` &rarr; Click **Generate Draft** &rarr; Verify Subject & Body auto-fill.
- [ ] **4. Tone Adjustment:** Select **Friendly** &rarr; Click **Rewrite** &rarr; Verify phrasing adapts &rarr; Click **Undo** to revert.
- [ ] **5. Dynamic Subject:** Clear Subject input &rarr; Click **Generate Subject** &rarr; Verify auto-fill.
- [ ] **6. Attachment & Send:** Attach a `.txt` / `.pdf` file &rarr; Send email to `bob`.
- [ ] **7. Inbox Priority:** Log in as `bob` &rarr; Confirm priority badge (`🔴 High` / `🟡 Normal` / `⚪ Low`).
- [ ] **8. AI Summarize:** Open message &rarr; Click **✨ Summarize Email** &rarr; Verify bullet points.
- [ ] **9. AI Smart Reply:** Click **💬 Smart Reply** &rarr; Select an option &rarr; Verify reply composer opens with pre-filled AI response and quoted original message.
- [ ] **10. Search & Trash:** Test search by keyword, soft-delete to Trash, and restore.
