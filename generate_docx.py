import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

doc = docx.Document()

# Page Margins (1 inch all sides)
for section in doc.sections:
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

# Colors
COLOR_PRIMARY = RGBColor(31, 78, 121)    # Dark Navy
COLOR_SECONDARY = RGBColor(46, 117, 182) # Blue
COLOR_DARK = RGBColor(38, 38, 38)        # Charcoal
COLOR_MUTED = RGBColor(89, 89, 89)       # Grey

def add_hyperlink(paragraph, url, text, color="1F4E79", underline=True):
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink = parse_xml(f'<w:hyperlink {nsdecls("w")} {nsdecls("r")} r:id="{r_id}"/>')
    new_run = parse_xml(f'<w:r {nsdecls("w")}><w:rPr><w:color w:val="{color}"/>{"<w:u w:val=\'single\'/>" if underline else ""}</w:rPr><w:t>{text}</w:t></w:r>')
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)

def add_styled_title(text, subtitle_text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(26)
    run.font.bold = True
    run.font.color.rgb = COLOR_PRIMARY

    p2 = doc.add_paragraph()
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after = Pt(16)
    run2 = p2.add_run(subtitle_text)
    run2.font.name = 'Calibri'
    run2.font.size = Pt(12)
    run2.font.italic = True
    run2.font.color.rgb = COLOR_MUTED

def add_heading_1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(18)
    run.font.bold = True
    run.font.color.rgb = COLOR_PRIMARY

def add_heading_2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(14)
    run.font.bold = True
    run.font.color.rgb = COLOR_SECONDARY

def add_heading_3(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(11.5)
    run.font.bold = True
    run.font.color.rgb = COLOR_DARK

def add_paragraph(text, bold_prefix=None, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = 'Calibri'
        r_pre.font.size = Pt(11)
        r_pre.font.bold = True
        r_pre.font.color.rgb = COLOR_DARK
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(11)
    run.font.color.rgb = COLOR_DARK
    return p

def add_bullet(text, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = 'Calibri'
        r_pre.font.size = Pt(11)
        r_pre.font.bold = True
        r_pre.font.color.rgb = COLOR_DARK
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(11)
    run.font.color.rgb = COLOR_DARK
    return p

def add_code_block(code_text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    # Background shading XML
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F2F4F7"/>')
    p._p.get_or_add_pPr().append(shd)
    run = p.add_run(code_text)
    run.font.name = 'Consolas'
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(40, 44, 52)

def set_cell_background(cell, fill_hex):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

# ----------------- DOCUMENT CONTENT -----------------

# Title & Subtitle
add_styled_title(
    "AI Mail App — Intelligent Webmail Assistant",
    "A Modern Webmail Client with Local & Cloud LLM Capabilities | Python Flask & SQLite"
)

add_paragraph("AI Mail App is a modern, full-featured webmail simulator and email assistant. It transforms a standard email interface into an intelligent productivity copilot that drafts emails from brief user prompts, refines tone on demand, automatically generates contextual subject lines, summarizes message threads into bullet points, suggests one-click smart replies, and automatically triages inbox priority.")

# ----------------- LIVE DEMO LINK -----------------
add_heading_1("🌐 Live Deployed Application")

p_live = doc.add_paragraph()
p_live.paragraph_format.space_before = Pt(0)
p_live.paragraph_format.space_after = Pt(6)
r_live_lbl = p_live.add_run("🚀 Live URL: ")
r_live_lbl.font.bold = True
r_live_lbl.font.name = 'Calibri'
r_live_lbl.font.size = Pt(12)
r_live_lbl.font.color.rgb = COLOR_PRIMARY
add_hyperlink(p_live, "https://ai-mail-app-v5pq.onrender.com", "https://ai-mail-app-v5pq.onrender.com", color="2E75B6")

add_paragraph("The application is live and fully functional. Use the test credentials below to explore all features without any local setup.")

add_bullet("alice  |  Password: password123", bold_prefix="Test Account 1: ")
add_bullet("bob  |  Password: password123", bold_prefix="Test Account 2: ")

p_github = doc.add_paragraph()
p_github.paragraph_format.space_before = Pt(6)
p_github.paragraph_format.space_after = Pt(8)
r_gh_lbl = p_github.add_run("📦 GitHub Repository: ")
r_gh_lbl.font.bold = True
r_gh_lbl.font.name = 'Calibri'
add_hyperlink(p_github, "https://github.com/ADITHYANWUU2/AI_Mail_App", "https://github.com/ADITHYANWUU2/AI_Mail_App", color="2E75B6")

# ----------------- VIDEO DEMO & DRIVE LINK -----------------
add_heading_1("🎥 Video Demonstration & Screenshots")

p_drive = doc.add_paragraph()
p_drive.paragraph_format.space_before = Pt(0)
p_drive.paragraph_format.space_after = Pt(8)
r_drive_lbl = p_drive.add_run("👉 Google Drive Project Link: ")
r_drive_lbl.font.bold = True
r_drive_lbl.font.name = 'Calibri'
add_hyperlink(p_drive, "https://drive.google.com/drive/folders/1tmASKIx1gSzLIToI8I9UrxFUjmFGaoKo", "https://drive.google.com/drive/folders/1tmASKIx1gSzLIToI8I9UrxFUjmFGaoKo", color="2E75B6")

add_paragraph("The link above contains the full 4–5 minute video demonstration showcasing the AI assistant controlling the UI, drafting messages, adjusting tones, and triaging inbox priority, along with high-resolution walkthrough screenshots.")

# ----------------- 1. SETUP GUIDE -----------------
add_heading_1("1. How to Set It Up and Run It Locally")
add_paragraph("The application is self-contained and runs on any standard Windows machine without external database servers.")

add_heading_2("Prerequisites")
add_bullet("Python 3.12 or newer installed from python.org (ensure 'Add python.exe to PATH' is checked).")
add_bullet("A standard web browser (Google Chrome, Microsoft Edge, Mozilla Firefox).")
add_bullet("Internet connection for initial dependency installation and Gemini API calls.")

add_heading_2("Installation Steps")

add_paragraph("1. Open PowerShell in the project directory:")
add_code_block('cd "C:\\Users\\mathi\\OneDrive\\Documents\\AI_Mail_App"')

add_paragraph("2. Create and activate the Python virtual environment:")
add_code_block("python -m venv venv\nvenv\\Scripts\\activate")

add_paragraph("3. Install all required dependencies:")
add_code_block("pip install -r requirements.txt")

add_paragraph("4. Configure Environment Variables (.env):")
add_paragraph("A pre-configured .env file is included with an 11-key Gemini API failover pool:")
add_code_block("GEMINI_API_KEYS=key1,key2,key3...\nGEMINI_MODEL=gemini-flash-latest")

add_paragraph("5. Start the web server:")
add_code_block("python run.py")

add_paragraph("6. Open in your browser:")
add_paragraph("Navigate to: http://localhost:5000 (or http://127.0.0.1:5000)")

add_heading_2("Pre-configured Demo Accounts")
add_bullet("alice (Password: password123)", bold_prefix="User 1: ")
add_bullet("bob (Password: password123)", bold_prefix="User 2: ")

# ----------------- 2. ARCHITECTURE & TRADEOFFS -----------------
add_heading_1("2. Architecture Decisions and Trade-offs")
add_paragraph("During development, key engineering decisions and trade-offs were made to balance real-time responsiveness, safety, data consistency, and user autonomy:")

add_heading_2("A. Single-Row Dual-Perspective Email Schema (SQLite)")
add_bullet("Instead of inserting duplicated rows for sender and recipient upon every email transmission, a single row in the 'emails' table stores both 'folder' (recipient's perspective: inbox/trash) and 'sender_folder' (sender's perspective: sent/trash/deleted).", bold_prefix="Design Decision: ")
add_bullet("Halves database storage requirements, eliminates synchronization bugs between sender and recipient attachment files, and prevents orphaned state during deletions.", bold_prefix="Advantage: ")
add_bullet("Requires conditional SQL query clauses based on whether current_user is the sender or the recipient.", bold_prefix="Trade-off: ")

add_heading_2("B. Multi-Key Auto-Failover API Pool Architecture")
add_bullet("Implemented an 11-key rotation pool in ai/ai_helper.py that automatically rotates to subsequent keys when encountering rate limits (429), quota exhaustion, or temporary API errors.", bold_prefix="Design Decision: ")
add_bullet("Guarantees uninterrupted live demos and sustained application performance without manual key rotation.", bold_prefix="Advantage: ")
add_bullet("Requires synchronized index tracking and defensive error catching across multiple HTTP response codes.", bold_prefix="Trade-off: ")

add_heading_2("C. Strict Human-in-the-Loop Safety Guardrail")
add_bullet("The AI assistant never sends emails automatically. All generated drafts, smart replies, and tone rewrites are injected into editable form fields for user review.", bold_prefix="Design Decision: ")
add_bullet("Eliminates the danger of AI hallucinations, unintentional commitments, or incorrect phrasing reaching real recipients.", bold_prefix="Advantage: ")
add_bullet("Requires an extra user confirmation click rather than fully autonomous 1-click execution.", bold_prefix="Trade-off: ")

add_heading_2("D. Progressive Enhancement: AJAX with No-JS Form Fallbacks")
add_bullet("AI interactions (Drafting, Summarization, Tone Adjustment, Smart Reply) utilize asynchronous fetch() calls to update the DOM without full page reloads, paired with server-side form fallbacks.", bold_prefix="Design Decision: ")
add_bullet("Delivers instant feedback with animated loading states while preserving accessibility.", bold_prefix="Advantage: ")

add_heading_2("E. AI-Assisted Transparency Disclaimer")
add_bullet("The email priority classifier is explicitly labeled as 'AI-assisted classification — not a guaranteed spam/priority filter'.", bold_prefix="Design Decision: ")
add_bullet("Transparently communicates that small/general LLMs lack personal inbox history and organizational context, avoiding false sense of security.", bold_prefix="Advantage: ")

# ----------------- 3. FEATURE MATRIX TABLE -----------------
add_heading_1("3. Key Features & Capabilities Matrix")

table = doc.add_table(rows=1, cols=2)
table.alignment = WD_TABLE_ALIGNMENT.CENTER
table.autofit = False

hdr_cells = table.rows[0].cells
hdr_cells[0].width = Inches(2.2)
hdr_cells[1].width = Inches(4.3)
hdr_cells[0].text = "Feature Module"
hdr_cells[1].text = "Capabilities & Architecture"
for c in hdr_cells:
    set_cell_background(c, "1F4E79")
    set_cell_margins(c, 120, 120, 150, 150)
    for p in c.paragraphs:
        for r in p.runs:
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)

features = [
    ("User Authentication", "Secure user registration, login, logout, password hashing using Werkzeug scrypt, session persistence via Flask-Login."),
    ("Webmail Simulator", "Inbox, Sent, Drafts, Trash folders, unread dots, live badge counters, and file attachment support up to 16MB."),
    ("AI Draft Assistant", "Natural language prompt-to-email generator (e.g. 'send project update to sir') &rarr; auto-fills subject and structured body."),
    ("AI Tone Rewriter", "Interactive rewrite toolbar with Professional, Friendly, Formal, and Concise modes, plus instant Undo/Revert support."),
    ("Dynamic Subject Generator", "Active-when-empty button that analyzes the email body and auto-generates a clear, concise subject line under 8 words."),
    ("AI Email Summarizer", "One-click real-time summarizer displaying 2–4 concise bullet points in a dedicated glassmorphism card above the email body."),
    ("AI Smart Reply", "Generates 3 distinct clickable reply suggestions (Agree, Acknowledge, Decline) that pre-fill compose with quoted message headers."),
    ("Automatic Priority Triage", "Real-time urgency classification into High (Red), Normal (Yellow), and Low (Grey) badges with inbox disclaimer."),
    ("Search & Trash Lifecycle", "SQL full-text search across subjects and message bodies, soft-delete to Trash, restore, and permanent deletion.")
]

for mod, cap in features:
    row_cells = table.add_row().cells
    row_cells[0].width = Inches(2.2)
    row_cells[1].width = Inches(4.3)
    set_cell_margins(row_cells[0], 80, 80, 120, 120)
    set_cell_margins(row_cells[1], 80, 80, 120, 120)
    row_cells[0].paragraphs[0].text = mod
    row_cells[0].paragraphs[0].runs[0].font.bold = True
    row_cells[0].paragraphs[0].runs[0].font.color.rgb = COLOR_PRIMARY
    row_cells[1].paragraphs[0].text = cap
    set_cell_background(row_cells[0], "F9FAFB")
    set_cell_background(row_cells[1], "FFFFFF")

# ----------------- 4. FUTURE IMPROVEMENTS -----------------
add_heading_1("4. What We'd Improve With More Time")
add_paragraph("With additional development cycles, the following high-value enhancements would elevate the application from a simulator to a production enterprise system:")

add_bullet("Implement a bidirectional IMAP/SMTP proxy bridge and OAuth2 connectors (Google Workspace, Microsoft 365) to manage real-world email accounts.", bold_prefix="1. Real SMTP/IMAP Protocol Integration: ")
add_bullet("Integrate a local vector database (ChromaDB or SQLite-vec) to index historical user threads, enabling personalized replies matching user writing style and past context.", bold_prefix="2. RAG & Vector Memory over User Email History: ")
add_bullet("Expand recipient fields to accommodate multi-recipient comma separation, Carbon Copy (CC), Blind Carbon Copy (BCC), and address book autocompletion.", bold_prefix="3. Multi-Recipient CC/BCC & Contact Groups: ")
add_bullet("Provide a toggle between cloud Gemini API and local Ollama (llama3.2:1b) for air-gapped zero-network enterprise privacy.", bold_prefix="4. Edge Privacy & Local SLM Mode: ")
add_bullet("Implement service workers, background sync, and IndexedDB so users can read inboxes and write drafts while completely offline.", bold_prefix="5. Progressive Web App (PWA) Offline Caching: ")
add_bullet("Add client-side OpenPGP message signing and encryption for high-security communications.", bold_prefix="6. End-to-End PGP Encryption: ")

# ----------------- 5. DEMO CHECKLIST -----------------
add_heading_1("5. Pre-Demo Verification Checklist")
add_paragraph("Verify each step prior to presenting:")

checklist_items = [
    "1. Start App: Run 'python run.py' and open http://localhost:5000 in browser.",
    "2. Auth: Log in as alice (password: password123).",
    "3. AI Draft: In Compose, type 'send project status report to team' and generate draft.",
    "4. Tone Rewrite: Select 'Friendly' tone, click Rewrite, then test Undo.",
    "5. Subject Generator: Clear subject field, click 'Generate Subject', verify auto-fill.",
    "6. Attachment & Send: Attach a document and send to bob.",
    "7. Inbox Triage: Log in as bob and verify colored priority badge.",
    "8. AI Summarize: Open email and click 'Summarize Email' to see bullet points.",
    "9. AI Smart Reply: Click 'Smart Reply' and select an option to open reply box.",
    "10. Search & Trash: Test keyword search in top bar, trash an email, and test restore."
]

for item in checklist_items:
    add_bullet(item)

# Save the document
output_path = r"C:\Users\mathi\OneDrive\Documents\AI_Mail_App\README_v2.docx"
doc.save(output_path)
print("SUCCESS: README.docx generated successfully at", output_path)
