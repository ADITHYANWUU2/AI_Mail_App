"""
database.py — Central SQLite setup for AI_Mail_App
====================================================
Phase 3: Added full mail CRUD — send, draft, move, trash, delete forever.
"""
import sqlite3
import os

DB_DIR  = "instance"
DB_PATH = os.path.join(DB_DIR, "ai_mail.db")


# ── Connection ────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ── Schema ────────────────────────────────────────────────────────────────────
def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER  PRIMARY KEY AUTOINCREMENT,
            username      TEXT     NOT NULL UNIQUE,
            email         TEXT     NOT NULL UNIQUE,
            password_hash TEXT     NOT NULL,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS emails (
            id             INTEGER  PRIMARY KEY AUTOINCREMENT,
            sender_id      INTEGER  NOT NULL,
            recipient_id   INTEGER  NOT NULL,
            subject        TEXT     NOT NULL DEFAULT '(no subject)',
            body           TEXT     NOT NULL DEFAULT '',
            timestamp      DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_read        INTEGER  NOT NULL DEFAULT 0,
            folder         TEXT     NOT NULL DEFAULT 'inbox'
                               CHECK(folder IN ('inbox','sent','drafts','trash')),
            sender_folder  TEXT     NOT NULL DEFAULT 'sent'
                               CHECK(sender_folder IN ('sent','drafts','trash','deleted')),
            priority       TEXT     CHECK(priority IN ('high','normal','low') OR priority IS NULL),
            attachment_filename TEXT DEFAULT NULL,

            FOREIGN KEY (sender_id)    REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    # Migration for existing DBs missing sender_folder column
    cursor = conn.execute("PRAGMA table_info(emails)")
    columns = [row["name"] for row in cursor.fetchall()]
    if "sender_folder" not in columns:
        try:
            conn.execute("ALTER TABLE emails ADD COLUMN sender_folder TEXT NOT NULL DEFAULT 'sent'")
        except Exception as e:
            pass

    if "attachment_filename" not in columns:
        try:
            conn.execute("ALTER TABLE emails ADD COLUMN attachment_filename TEXT DEFAULT NULL")
        except Exception as e:
            pass

    conn.commit()
    conn.close()


# ── User helpers ──────────────────────────────────────────────────────────────
def create_user(username, email, password_hash):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?,?,?)",
            (username, email, password_hash)
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = get_db()
    row  = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return row


def get_user_by_username(username):
    conn = get_db()
    row  = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return row


def get_user_by_email(email):
    conn = get_db()
    row  = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    return row


# ── Email CRUD ────────────────────────────────────────────────────────────────

def send_email(sender_id, recipient_id, subject, body, priority=None, attachment_filename=None):
    """
    Insert TWO rows for one sent email:
      - recipient sees it in 'inbox'
      - sender    sees it in 'sent'   (via sender_folder)
    We use a single row but track both perspectives:
      folder        = recipient's folder  (inbox)
      sender_folder = sender's folder     (sent)
    """
    conn = get_db()
    try:
        cur  = conn.execute(
            """INSERT INTO emails
                   (sender_id, recipient_id, subject, body, folder, sender_folder, priority, attachment_filename)
               VALUES (?,?,?,?,'inbox','sent',?,?)""",
            (sender_id, recipient_id, subject, body, priority, attachment_filename)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def save_draft(sender_id, recipient_username, subject, body, attachment_filename=None):
    """
    Save a draft. recipient_id = sender_id (self-addressed placeholder).
    """
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO emails
                   (sender_id, recipient_id, subject, body, folder, sender_folder, is_read, attachment_filename)
               VALUES (?,?,?,?,'drafts','drafts',1,?)""",
            (sender_id, sender_id, f"[DRAFT] {subject}", body, attachment_filename)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def search_emails(user_id, query):
    """
    Search emails by subject or body containing query for this user.
    Includes emails where user is recipient (inbox) or sender (sent).
    """
    conn = get_db()
    try:
        pattern = f"%{query}%"
        rows = conn.execute(
            """SELECT e.*, u.username AS sender_name,
                      r.username AS recipient_name
               FROM   emails e
               JOIN   users u ON u.id = e.sender_id
               JOIN   users r ON r.id = e.recipient_id
               WHERE  ((e.recipient_id = ? AND e.folder = 'inbox')
                    OR (e.sender_id = ? AND e.sender_folder = 'sent'))
                 AND  (e.subject LIKE ? OR e.body LIKE ?)
               ORDER BY e.timestamp DESC""",
            (user_id, user_id, pattern, pattern)
        ).fetchall()
        return rows
    finally:
        conn.close()


def get_inbox(user_id):
    """All emails where I am the recipient and folder = inbox."""
    conn = get_db()
    rows = conn.execute(
        """SELECT e.*, u.username AS sender_name,
                  r.username AS recipient_name
           FROM   emails e
           JOIN   users u ON u.id = e.sender_id
           JOIN   users r ON r.id = e.recipient_id
           WHERE  e.recipient_id = ? AND e.folder = 'inbox'
           ORDER BY e.timestamp DESC""",
        (user_id,)
    ).fetchall()
    conn.close()
    return rows


def get_sent(user_id):
    """All emails I sent (sender_folder = sent)."""
    conn = get_db()
    rows = conn.execute(
        """SELECT e.*, u.username AS sender_name,
                  r.username AS recipient_name
           FROM   emails e
           JOIN   users u ON u.id = e.sender_id
           JOIN   users r ON r.id = e.recipient_id
           WHERE  e.sender_id = ? AND e.sender_folder = 'sent'
           ORDER BY e.timestamp DESC""",
        (user_id,)
    ).fetchall()
    conn.close()
    return rows


def get_drafts(user_id):
    """Drafts saved by this user."""
    conn = get_db()
    rows = conn.execute(
        """SELECT e.*, u.username AS sender_name,
                  r.username AS recipient_name
           FROM   emails e
           JOIN   users u ON u.id = e.sender_id
           JOIN   users r ON r.id = e.recipient_id
           WHERE  e.sender_id = ? AND e.folder = 'drafts'
           ORDER BY e.timestamp DESC""",
        (user_id,)
    ).fetchall()
    conn.close()
    return rows


def get_trash(user_id):
    """
    Emails in trash:
      - inbox items I moved to trash  (recipient_id=me, folder='trash')
      - sent  items I moved to trash  (sender_id=me,    sender_folder='trash')
    """
    conn = get_db()
    rows = conn.execute(
        """SELECT e.*, u.username AS sender_name,
                  r.username AS recipient_name
           FROM   emails e
           JOIN   users u ON u.id = e.sender_id
           JOIN   users r ON r.id = e.recipient_id
           WHERE (e.recipient_id = ? AND e.folder        = 'trash')
              OR (e.sender_id    = ? AND e.sender_folder = 'trash'
                  AND e.recipient_id != ?)
           ORDER BY e.timestamp DESC""",
        (user_id, user_id, user_id)
    ).fetchall()
    conn.close()
    return rows


def get_email_by_id(email_id):
    conn = get_db()
    row  = conn.execute(
        """SELECT e.*, u.username AS sender_name,
                  r.username AS recipient_name
           FROM   emails e
           JOIN   users u ON u.id = e.sender_id
           JOIN   users r ON r.id = e.recipient_id
           WHERE  e.id = ?""",
        (email_id,)
    ).fetchone()
    conn.close()
    return row


def mark_as_read(email_id):
    conn = get_db()
    conn.execute("UPDATE emails SET is_read=1 WHERE id=?", (email_id,))
    conn.commit()
    conn.close()


def move_to_trash(email_id, user_id):
    """
    Recipient moves inbox/sent mail to trash.
    Updates the correct folder field based on who's acting.
    """
    conn = get_db()
    row  = conn.execute("SELECT * FROM emails WHERE id=?", (email_id,)).fetchone()
    if row:
        if row["recipient_id"] == user_id:
            conn.execute("UPDATE emails SET folder='trash' WHERE id=?", (email_id,))
        elif row["sender_id"] == user_id:
            conn.execute("UPDATE emails SET sender_folder='trash' WHERE id=?", (email_id,))
    conn.commit()
    conn.close()


def restore_from_trash(email_id, user_id):
    """Move a trashed email back to inbox or sent."""
    conn = get_db()
    row  = conn.execute("SELECT * FROM emails WHERE id=?", (email_id,)).fetchone()
    if row:
        if row["recipient_id"] == user_id and row["folder"] == "trash":
            conn.execute("UPDATE emails SET folder='inbox' WHERE id=?", (email_id,))
        elif row["sender_id"] == user_id and row["sender_folder"] == "trash":
            conn.execute("UPDATE emails SET sender_folder='sent' WHERE id=?", (email_id,))
    conn.commit()
    conn.close()


def delete_forever(email_id, user_id):
    """Permanently remove an email from trash."""
    conn = get_db()
    try:
        conn.execute("DELETE FROM emails WHERE id = ? AND (sender_id = ? OR recipient_id = ?)", (email_id, user_id, user_id))
        conn.commit()
    finally:
        conn.close()


def get_unread_count(user_id):
    conn   = get_db()
    result = conn.execute(
        "SELECT COUNT(*) FROM emails WHERE recipient_id=? AND folder='inbox' AND is_read=0",
        (user_id,)
    ).fetchone()
    conn.close()
    return result[0]


# ── Legacy alias (keep backward compat) ──────────────────────────────────────
def insert_email(sender_id, recipient_id, subject, body, folder="inbox", priority=None):
    return send_email(sender_id, recipient_id, subject, body, priority)


def get_emails_for_user(user_id, folder="inbox"):
    if folder == "inbox":   return get_inbox(user_id)
    if folder == "sent":    return get_sent(user_id)
    if folder == "drafts":  return get_drafts(user_id)
    if folder == "trash":   return get_trash(user_id)
    return []
