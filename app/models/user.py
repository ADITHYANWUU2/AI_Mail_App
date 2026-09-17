"""
app/models/user.py
Flask-Login UserMixin wrapper around the database.py user helpers.

HOW PASSWORD HASHING WORKS (plain language):
─────────────────────────────────────────────
When you type "mypassword123" and register:

  1. Werkzeug runs it through the bcrypt algorithm:
       "mypassword123"  →  "pbkdf2:sha256:600000$xY7z...abcd"

  2. That long scrambled string is what gets saved in the DB.
     The original password is NEVER stored — not even we can read it.

  3. When you log in later and type "mypassword123":
       Werkzeug hashes your input the same way
       Then compares the two hashes
       If they match → you're in ✅
       If not → rejected ❌

  Why is this safe?
  - Hashing is one-way — you can't "un-hash" to get the original.
  - Each hash includes a random "salt" so two users with the same
    password get completely different hashes.
  - Even if someone steals the database, they only see gibberish.
"""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database import (
    create_user       as db_create_user,
    get_user_by_id    as db_get_by_id,
    get_user_by_username as db_get_by_username,
    get_user_by_email as db_get_by_email,
)


class User(UserMixin):
    """
    Represents an authenticated user session.
    Flask-Login calls get_id() automatically — provided by UserMixin.
    """

    def __init__(self, id, username, email):
        self.id       = id
        self.username = username
        self.email    = email

    # ── Flask-Login required ─────────────────────────────────────────────────
    def get_id(self):
        return str(self.id)

    # ── Factory methods ──────────────────────────────────────────────────────
    @classmethod
    def from_row(cls, row):
        """Build a User object from a sqlite3.Row."""
        if row is None:
            return None
        return cls(row["id"], row["username"], row["email"])

    @classmethod
    def get_by_id(cls, user_id):
        return cls.from_row(db_get_by_id(user_id))

    @classmethod
    def get_by_username(cls, username):
        """Returns raw sqlite3.Row (includes password_hash for verification)."""
        return db_get_by_username(username)

    @classmethod
    def get_by_email(cls, email):
        return db_get_by_email(email)

    # ── Auth helpers ─────────────────────────────────────────────────────────
    @classmethod
    def register(cls, username, email, plain_password):
        """
        Hash the password, insert into DB, return User object.
        Returns None if username/email already exists.
        """
        hashed  = generate_password_hash(plain_password)
        user_id = db_create_user(username, email, hashed)
        if user_id is None:
            return None
        return cls(user_id, username, email)

    @staticmethod
    def verify_password(password_hash, plain_password):
        """
        Check a plain password against the stored hash.
        Returns True if they match, False otherwise.
        """
        return check_password_hash(password_hash, plain_password)
