"""
app/routes/mail.py — Mail blueprint
Handles: compose, inbox, sent, drafts, trash, view, reply, forward, search, attachments
"""
import os
import time
import uuid
from flask import (
    Blueprint, render_template, redirect, url_for, request, flash,
    abort, current_app, send_from_directory, jsonify
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from database import (
    get_user_by_username,
    send_email, save_draft,
    get_inbox, get_sent, get_drafts, get_trash,
    get_email_by_id, mark_as_read,
    move_to_trash, restore_from_trash, delete_forever,
    get_unread_count, search_emails
)
from ai.ai_helper import call_ai

mail_bp = Blueprint("mail", __name__)

ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif',
    'doc', 'docx', 'csv', 'xlsx', 'zip', 'mp3', 'mp4'
}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def mail_ctx():
    return {"unread": get_unread_count(current_user.id)}


# ── Test AI Route ─────────────────────────────────────────────────────────────
@mail_bp.route("/test-ai")
def test_ai():
    prompt = request.args.get(
        "prompt",
        "Write a short, friendly 2-sentence welcome email to a new team member."
    )
    ai_response = call_ai(prompt)
    return render_template("test_ai.html", prompt=prompt, response=ai_response)


# ── Inbox ─────────────────────────────────────────────────────────────────────
@mail_bp.route("/")
@mail_bp.route("/inbox")
@login_required
def inbox():
    emails = get_inbox(current_user.id)
    return render_template("inbox.html", emails=emails, folder="inbox", **mail_ctx())


# ── Sent ──────────────────────────────────────────────────────────────────────
@mail_bp.route("/sent")
@login_required
def sent():
    emails = get_sent(current_user.id)
    return render_template("mail_list.html", emails=emails, folder="sent", **mail_ctx())


# ── Drafts ────────────────────────────────────────────────────────────────────
@mail_bp.route("/drafts")
@login_required
def drafts():
    emails = get_drafts(current_user.id)
    return render_template("mail_list.html", emails=emails, folder="drafts", **mail_ctx())


# ── Trash ─────────────────────────────────────────────────────────────────────
@mail_bp.route("/trash")
@login_required
def trash():
    emails = get_trash(current_user.id)
    return render_template("mail_list.html", emails=emails, folder="trash", **mail_ctx())


# ── Search ────────────────────────────────────────────────────────────────────
@mail_bp.route("/search")
@login_required
def search():
    query = request.args.get("q", "").strip()
    emails = search_emails(current_user.id, query) if query else []
    return render_template(
        "mail_list.html",
        emails=emails,
        folder="search",
        search_query=query,
        **mail_ctx()
    )


def classify_email_priority(subject, body):
    """
    Classify email into: 'high', 'normal', 'low' using local Ollama model.
    """
    content = f"Subject: {subject}\nBody: {body}"
    if len(content) > 1500:
        content = content[:1500]

    prompt = (
        f"Analyze the urgency and priority of this email:\n{content}\n\n"
        "Determine if this is:\n"
        "- HIGH priority: Urgent emergency, production outage, critical security alert, immediate deadline today.\n"
        "- NORMAL priority: Standard business request, project update, client inquiry, scheduled meeting.\n"
        "- LOW priority: Casual chatter, cafeteria menu, optional newsletter, social invite, marketing.\n\n"
        "Format your output strictly as:\n"
        "PRIORITY: <HIGH, NORMAL, or LOW>\n"
        "REASON: <one short sentence>\n"
    )

    try:
        raw = call_ai(prompt).strip()
        upper_raw = raw.upper()
        if "PRIORITY: HIGH" in upper_raw or "HIGH" in upper_raw.splitlines()[0] if upper_raw.splitlines() else False or ("EMERGENCY" in subject.upper() or "CRITICAL" in subject.upper() or "URGENT" in subject.upper()):
            return "high"
        elif "PRIORITY: LOW" in upper_raw:
            return "low"
        elif "PRIORITY: NORMAL" in upper_raw:
            return "normal"
        elif "HIGH" in upper_raw:
            return "high"
        elif "LOW" in upper_raw:
            return "low"
        else:
            return "normal"
    except Exception:
        return "normal"


# ── Compose ───────────────────────────────────────────────────────────────────
@mail_bp.route("/compose", methods=["GET", "POST"])
@login_required
def compose():
    prefill = {
        "to":      request.args.get("to", ""),
        "subject": request.args.get("subject", ""),
        "body":    request.args.get("body", ""),
    }

    if request.method == "POST":
        action    = request.form.get("action", "send")   # send | draft
        to_user   = request.form.get("to", "").strip()
        subject   = request.form.get("subject", "").strip() or "(no subject)"
        body      = request.form.get("body", "").strip()

        # ── Handle Attachment Upload ──────────────────────────────────────────
        attachment_filename = None
        if "attachment" in request.files:
            file = request.files["attachment"]
            if file and file.filename != "":
                if not allowed_file(file.filename):
                    flash("File type not allowed. Supported: txt, pdf, png, jpg, gif, doc, docx, csv, xlsx, zip", "danger")
                    return render_template("compose.html", prefill=prefill, **mail_ctx())

                clean_name = secure_filename(file.filename)
                unique_name = f"{int(time.time())}_{uuid.uuid4().hex[:6]}_{clean_name}"
                file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
                file.save(file_path)
                attachment_filename = unique_name

        # ── Save as Draft ─────────────────────────────────────────────────────
        if action == "draft":
            save_draft(current_user.id, to_user, subject, body, attachment_filename=attachment_filename)
            flash("📝 Draft saved.", "info")
            return redirect(url_for("mail.drafts"))

        # ── Send ──────────────────────────────────────────────────────────────
        if not to_user:
            flash("Please enter a recipient username.", "danger")
            return render_template("compose.html", prefill=prefill, **mail_ctx())

        if to_user == current_user.username:
            flash("You cannot send an email to yourself.", "warning")
            return render_template("compose.html", prefill=prefill, **mail_ctx())

        recipient = get_user_by_username(to_user)
        if not recipient:
            flash(f'User "{to_user}" does not exist.', "danger")
            return render_template("compose.html", prefill=prefill, **mail_ctx())

        # AI Automatic Importance Classification
        priority = classify_email_priority(subject, body)

        send_email(
            current_user.id,
            recipient["id"],
            subject,
            body,
            priority=priority,
            attachment_filename=attachment_filename
        )
        flash(f"✅ Email sent to {to_user}!", "success")
        return redirect(url_for("mail.sent"))

    return render_template("compose.html", prefill=prefill, **mail_ctx())


# ── AI Compose Assistant ──────────────────────────────────────────────────────
@mail_bp.route("/compose/ai-draft", methods=["POST"])
@login_required
def ai_compose():
    data = request.get_json(silent=True) or request.form
    instruction = data.get("prompt", "").strip()

    if not instruction:
        return jsonify({"error": "Please provide a description of what you want to write."}), 400

    prompt = (
        "Write a polite, professional business email update based on the following topic:\n"
        f"Topic: {instruction}\n\n"
        "Your response must include a subject line and the email body.\n"
        "Use this exact format:\n"
        "SUBJECT: <concise subject line>\n"
        "BODY:\n"
        "<full professional email body with greeting, update points, and sign-off>\n"
    )

    ai_raw = call_ai(prompt)

    # Parse SUBJECT and BODY
    subject = "Project Update"
    body = ""

    if "SUBJECT:" in ai_raw.upper() and "BODY:" in ai_raw.upper():
        # Case-insensitive split
        upper_raw = ai_raw.upper()
        s_idx = upper_raw.find("SUBJECT:")
        b_idx = upper_raw.find("BODY:", s_idx)
        if s_idx != -1 and b_idx != -1:
            subject = ai_raw[s_idx + len("SUBJECT:"):b_idx].strip().split("\n")[0].strip()
            body = ai_raw[b_idx + len("BODY:"):].strip()
    elif "Subject:" in ai_raw:
        lines = ai_raw.split("\n")
        subject = lines[0].replace("Subject:", "").strip()
        body = "\n".join(lines[1:]).strip()
    else:
        lines = [l for l in ai_raw.split("\n") if l.strip()]
        if lines:
            subject = lines[0].strip()
            body = "\n".join(lines[1:]).strip()
        else:
            body = ai_raw

    # Clean subject and body of conversational preamble
    if subject.lower().startswith("here") or len(subject) > 80:
        # Look inside body if body starts with Subject:
        if "subject:" in body.lower():
            lines = body.split("\n")
            for i, line in enumerate(lines):
                if line.lower().startswith("subject:"):
                    subject = line.split(":", 1)[1].strip()
                    body = "\n".join(lines[i+1:]).strip()
                    break
        else:
            subject = "Project Update"

    # Clean quotes from subject
    if (subject.startswith('"') and subject.endswith('"')) or (subject.startswith("'") and subject.endswith("'")):
        subject = subject[1:-1].strip()

    if not body:
        body = (
            f"Dear Sir,\n\n"
            f"I am writing to share our latest project update. Everything is progressing on schedule, and we have accomplished our major milestones for the week.\n\n"
            f"Please let me know if you would like me to prepare a more detailed report.\n\n"
            f"Best regards,\n{current_user.username}"
        )

    return jsonify({
        "subject": subject or "Project Update",
        "body": body
    })


# ── AI Tone Rewriter ──────────────────────────────────────────────────────────
@mail_bp.route("/compose/rewrite-tone", methods=["POST"])
@login_required
def rewrite_tone():
    data = request.get_json(silent=True) or request.form
    current_body = data.get("body", "").strip()
    tone = data.get("tone", "Professional").strip()

    if not current_body:
        return jsonify({"error": "Email body is empty. Please write some text first."}), 400

    valid_tones = ["Professional", "Friendly", "Formal", "Concise"]
    if tone not in valid_tones:
        tone = "Professional"

    prompt = (
        f"You are an email assistant rewriting message text into a {tone.lower()} tone.\n"
        f"Rewrite this message to sound {tone.lower()}:\n"
        f"\"{current_body}\"\n\n"
        "Rules:\n"
        f"- Output ONLY the final rewritten email body in a {tone.lower()} tone.\n"
        "- Do not include explanations, disclaimers, or conversational remarks."
    )

    rewritten = call_ai(prompt)

    # Clean preamble if any
    lines = rewritten.split("\n")
    if lines and (lines[0].lower().startswith("here") or lines[0].lower().startswith("sure")):
        rewritten = "\n".join(lines[1:]).strip()

    return jsonify({
        "rewritten_body": rewritten or current_body,
        "tone": tone
    })


# ── AI Generate Subject ───────────────────────────────────────────────────────
@mail_bp.route("/compose/generate-subject", methods=["POST"])
@login_required
def generate_subject():
    data = request.get_json(silent=True) or request.form
    body = data.get("body", "").strip()

    if not body:
        return jsonify({"error": "Email body is empty. Please write some content first."}), 400

    prompt = (
        "You are an assistant creating concise email subjects.\n"
        "Suggest a short, clear email subject line (under 8 words) for this email body:\n\n"
        f"{body}\n\n"
        "Rules:\n"
        "- Output ONLY the subject line itself.\n"
        "- Do not use quotes or prefixes like 'Subject:'."
    )

    subject = call_ai(prompt).strip()

    # Clean any quotes or prefixes
    for prefix in ["Subject:", "SUBJECT:", "Subject line:", "Here is a subject line:", "Here's a subject line:"]:
        if subject.startswith(prefix):
            subject = subject[len(prefix):].strip()
    if (subject.startswith('"') and subject.endswith('"')) or (subject.startswith("'") and subject.endswith("'")):
        subject = subject[1:-1].strip()

    lines = [l.strip() for l in subject.split("\n") if l.strip()]
    if lines:
        subject = lines[0]

    return jsonify({"subject": subject or "Project Update"})


# ── Reply ─────────────────────────────────────────────────────────────────────
@mail_bp.route("/mail/<int:email_id>/reply")
@login_required
def reply(email_id):
    email = get_email_by_id(email_id)
    if not email:
        abort(404)
    if email["sender_id"] != current_user.id and email["recipient_id"] != current_user.id:
        abort(403)

    # If I received it, reply to sender. If I sent it, reply to recipient.
    reply_to = email["sender_name"] if email["recipient_id"] == current_user.id else email["recipient_name"]

    subject = email["subject"]
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    ai_text = request.args.get("ai_text", "").strip()
    if ai_text:
        body_content = (
            f"{ai_text}\n\n\n"
            f"--- Original Message ---\n"
            f"From: {email['sender_name']}\n"
            f"Date: {email['timestamp']}\n"
            f"Subject: {email['subject']}\n\n"
            f"{email['body']}"
        )
    else:
        body_content = (
            f"\n\n\n--- Original Message ---\n"
            f"From: {email['sender_name']}\n"
            f"Date: {email['timestamp']}\n"
            f"Subject: {email['subject']}\n\n"
            f"{email['body']}"
        )

    prefill = {
        "to": reply_to,
        "subject": subject,
        "body": body_content
    }
    return render_template("compose.html", prefill=prefill, **mail_ctx())


# ── Forward ───────────────────────────────────────────────────────────────────
@mail_bp.route("/mail/<int:email_id>/forward")
@login_required
def forward(email_id):
    email = get_email_by_id(email_id)
    if not email:
        abort(404)
    if email["sender_id"] != current_user.id and email["recipient_id"] != current_user.id:
        abort(403)

    subject = email["subject"]
    if not subject.lower().startswith("fwd:"):
        subject = f"Fwd: {subject}"

    forward_body = (
        f"\n\n\n---------- Forwarded message ---------\n"
        f"From: {email['sender_name']}\n"
        f"Date: {email['timestamp']}\n"
        f"Subject: {email['subject']}\n"
        f"To: {email['recipient_name']}\n\n"
        f"{email['body']}"
    )

    prefill = {
        "to": "",
        "subject": subject,
        "body": forward_body
    }
    return render_template("compose.html", prefill=prefill, **mail_ctx())


# ── View single email ─────────────────────────────────────────────────────────
@mail_bp.route("/mail/<int:email_id>")
@login_required
def view_email(email_id):
    email = get_email_by_id(email_id)
    if not email:
        abort(404)

    # Security: only sender or recipient can view
    if email["sender_id"] != current_user.id and email["recipient_id"] != current_user.id:
        abort(403)

    # Mark as read if recipient is viewing
    if email["recipient_id"] == current_user.id and not email["is_read"]:
        mark_as_read(email_id)

    # Clean display name for attachment (strip timestamp prefix)
    attachment_display_name = None
    if email["attachment_filename"]:
        parts = email["attachment_filename"].split("_", 2)
        attachment_display_name = parts[2] if len(parts) >= 3 else email["attachment_filename"]

    folder = request.args.get("folder", "inbox")
    return render_template(
        "email_detail.html",
        email=email,
        folder=folder,
        attachment_display_name=attachment_display_name,
        **mail_ctx()
    )


# ── Summarize Email with AI ───────────────────────────────────────────────────
@mail_bp.route("/mail/<int:email_id>/summarize", methods=["POST"])
@login_required
def summarize_email(email_id):
    email = get_email_by_id(email_id)
    if not email:
        abort(404)
    if email["sender_id"] != current_user.id and email["recipient_id"] != current_user.id:
        abort(403)

    raw_body = email["body"] or ""
    if not raw_body.strip():
        ai_summary = "This email has no text content to summarize."
    else:
        # Truncate if extremely long to avoid overloading local model memory/context
        MAX_CHARS = 3500
        if len(raw_body) > MAX_CHARS:
            truncated_body = raw_body[:MAX_CHARS] + "\n...[Email truncated for length]..."
        else:
            truncated_body = raw_body

        prompt = f"Summarize this email in 2-4 short bullet points:\n\n{truncated_body}"
        ai_summary = call_ai(prompt)

    # Check if requested via AJAX
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({"summary": ai_summary})

    # Standard form POST fallback: re-render detail view with summary
    attachment_display_name = None
    if email["attachment_filename"]:
        parts = email["attachment_filename"].split("_", 2)
        attachment_display_name = parts[2] if len(parts) >= 3 else email["attachment_filename"]

    folder = request.form.get("folder", "inbox")
    return render_template(
        "email_detail.html",
        email=email,
        folder=folder,
        attachment_display_name=attachment_display_name,
        ai_summary=ai_summary,
        **mail_ctx()
    )


# ── Smart Reply Suggestions with AI ───────────────────────────────────────────
@mail_bp.route("/mail/<int:email_id>/smart-reply", methods=["POST"])
@login_required
def smart_reply(email_id):
    email = get_email_by_id(email_id)
    if not email:
        abort(404)
    if email["sender_id"] != current_user.id and email["recipient_id"] != current_user.id:
        abort(403)

    raw_body = email["body"] or ""
    if len(raw_body) > 3000:
        raw_body = raw_body[:3000]

    prompt = (
        "Read this email and write 3 short reply suggestions (1-2 sentences each). "
        "Reply 1 should be positive and accepting. "
        "Reply 2 should be a brief acknowledgment. "
        "Reply 3 should be declining or rescheduling.\n\n"
        "Output ONLY the 3 replies, each on its own line beginning with 1., 2., 3.\n"
        "Do NOT use placeholders like '[reply text]'. Write the actual reply sentences.\n\n"
        f"Email:\n{raw_body}"
    )

    ai_raw = call_ai(prompt)

    suggestions = []
    for line in ai_raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        for prefix in ["1.", "2.", "3.", "1)", "2)", "3)", "Option 1:", "Option 2:", "Option 3:"]:
            if line.startswith(prefix):
                line = line[len(prefix):].strip()
                break
        if (line.startswith('"') and line.endswith('"')) or (line.startswith("'") and line.endswith("'")):
            line = line[1:-1].strip()
        if line and len(line) > 5 and not line.lower().startswith("here are") and not "[reply" in line.lower():
            suggestions.append(line)

    if not suggestions:
        clean_lines = [l.strip().lstrip("-*123456789. ") for l in ai_raw.split("\n") if len(l.strip()) > 10 and not l.strip().lower().startswith("here")]
        suggestions = clean_lines[:3]

    if not suggestions:
        suggestions = [
            "Thanks for the email! Everything sounds good to me.",
            "Received with thanks. I will review this and follow up shortly.",
            "Thanks for reaching out! Could we possibly reschedule for later?"
        ]

    return jsonify({"suggestions": suggestions[:3]})


# ── Download attachment ───────────────────────────────────────────────────────
@mail_bp.route("/download/<int:email_id>")
@login_required
def download_attachment(email_id):
    email = get_email_by_id(email_id)
    if not email:
        abort(404)
    if email["sender_id"] != current_user.id and email["recipient_id"] != current_user.id:
        abort(403)
    if not email["attachment_filename"]:
        abort(404)

    parts = email["attachment_filename"].split("_", 2)
    display_name = parts[2] if len(parts) >= 3 else email["attachment_filename"]

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        email["attachment_filename"],
        as_attachment=True,
        download_name=display_name
    )


# ── Move to Trash ─────────────────────────────────────────────────────────────
@mail_bp.route("/mail/<int:email_id>/trash", methods=["POST"])
@login_required
def trash_email(email_id):
    email = get_email_by_id(email_id)
    if not email:
        abort(404)
    if email["sender_id"] != current_user.id and email["recipient_id"] != current_user.id:
        abort(403)

    move_to_trash(email_id, current_user.id)
    flash("🗑️ Email moved to trash.", "info")

    folder = request.form.get("folder", "inbox")
    return redirect(url_for(f"mail.{folder}") if folder in ("inbox", "sent", "drafts") else url_for("mail.inbox"))


# ── Restore from Trash ────────────────────────────────────────────────────────
@mail_bp.route("/mail/<int:email_id>/restore", methods=["POST"])
@login_required
def restore_email(email_id):
    email = get_email_by_id(email_id)
    if not email:
        abort(404)
    if email["sender_id"] != current_user.id and email["recipient_id"] != current_user.id:
        abort(403)

    restore_from_trash(email_id, current_user.id)
    flash("♻️ Email restored.", "success")
    return redirect(url_for("mail.trash"))


# ── Delete Forever ────────────────────────────────────────────────────────────
@mail_bp.route("/mail/<int:email_id>/delete", methods=["POST"])
@login_required
def delete_email(email_id):
    email = get_email_by_id(email_id)
    if not email:
        abort(404)
    if email["sender_id"] != current_user.id and email["recipient_id"] != current_user.id:
        abort(403)

    # Optionally delete the uploaded file if present
    if email["attachment_filename"]:
        file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], email["attachment_filename"])
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

    delete_forever(email_id, current_user.id)
    flash("❌ Email permanently deleted.", "danger")
    return redirect(url_for("mail.trash"))
