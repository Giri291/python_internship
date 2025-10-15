# utils.py
import sqlite3
import bcrypt
from datetime import datetime
from contextlib import closing

DB_PATH = "banking.db"


def get_connection():
    """Return a sqlite3 connection with proper settings for multi-threaded use."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def create_tables():
    """
    Create users and transactions tables if they don't exist.
    users: username (PK), password (hashed), balance (REAL)
    transactions: id, username, type, amount, timestamp, other_party
    """
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password BLOB,
                balance REAL DEFAULT 0.0
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                type TEXT,
                amount REAL,
                timestamp TEXT,
                other_party TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def signup(username: str, password: str) -> bool:
    """
    Create a new user with hashed password.
    Returns True if created, False if username exists or error.
    """
    if not username or not password:
        return False

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    conn = get_connection()
    try:
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users (username, password, balance) VALUES (?, ?, ?)",
                (username, hashed, 0.0),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Username already exists
            return False
    finally:
        conn.close()


def login(username: str, password: str) -> bool:
    """
    Verify username and password.
    Returns True on success, False otherwise.
    """
    if not username or not password:
        return False

    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        if not row:
            return False
        stored_hash = row[0]
        # stored_hash is bytes because we saved bcrypt bytes
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode("utf-8")
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash)
    finally:
        conn.close()


def get_balance(username: str) -> float:
    """Return current balance for username (0.0 if not found)."""
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        return float(row[0]) if row else 0.0
    finally:
        conn.close()


def deposit(username: str, amount: float) -> bool:
    """Deposit amount into user's account and log the transaction."""
    if amount <= 0:
        return False
    conn = get_connection()
    try:
        c = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, username))
            c.execute(
                "INSERT INTO transactions (username, type, amount, timestamp, other_party) VALUES (?, ?, ?, ?, ?)",
                (username, "Deposit", amount, timestamp, ""),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            conn.rollback()
            return False
    finally:
        conn.close()


def withdraw(username: str, amount: float) -> bool:
    """Withdraw amount from user's account if sufficient balance, and log transaction."""
    if amount <= 0:
        return False
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        if not row or row[0] < amount:
            return False
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            c.execute("UPDATE users SET balance = balance - ? WHERE username = ?", (amount, username))
            c.execute(
                "INSERT INTO transactions (username, type, amount, timestamp, other_party) VALUES (?, ?, ?, ?, ?)",
                (username, "Withdraw", amount, timestamp, ""),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            conn.rollback()
            return False
    finally:
        conn.close()


def transfer(sender: str, receiver: str, amount: float) -> bool:
    """
    Transfer amount from sender to receiver if both exist and sender has enough balance.
    Logs two transaction rows (transfer_out for sender, transfer_in for receiver).
    """
    if amount <= 0 or not sender or not receiver or sender == receiver:
        return False

    conn = get_connection()
    try:
        c = conn.cursor()
        # Check existence and balance
        c.execute("SELECT balance FROM users WHERE username = ?", (sender,))
        sender_row = c.fetchone()
        c.execute("SELECT username FROM users WHERE username = ?", (receiver,))
        receiver_row = c.fetchone()
        if not sender_row or not receiver_row or sender_row[0] < amount:
            return False

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            # Use transaction
            c.execute("BEGIN")
            c.execute("UPDATE users SET balance = balance - ? WHERE username = ?", (amount, sender))
            c.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, receiver))
            c.execute(
                "INSERT INTO transactions (username, type, amount, timestamp, other_party) VALUES (?, ?, ?, ?, ?)",
                (sender, "transfer_out", amount, timestamp, receiver),
            )
            c.execute(
                "INSERT INTO transactions (username, type, amount, timestamp, other_party) VALUES (?, ?, ?, ?, ?)",
                (receiver, "transfer_in", amount, timestamp, sender),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            conn.rollback()
            return False
    finally:
        conn.close()


def get_transactions(username: str):
    """
    Return list of transactions for username.
    Each transaction row: (type, amount, timestamp, other_party)
    Ordered by insertion (oldest first). The UI can reverse it if needed.
    """
    conn = get_connection()
    try:
        c = conn.cursor()
        # Fetch transactions where user is either the username or the other_party
        c.execute(
            """
            SELECT type, amount, timestamp, other_party
            FROM transactions
            WHERE username = ?
            ORDER BY id ASC
            """,
            (username,),
        )
        return c.fetchall()
    finally:
        conn.close()


def get_all_users():
    """Return list of (username, balance) for all users."""
    conn = get_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT username, balance FROM users ORDER BY username ASC")
        return c.fetchall()
    finally:
        conn.close()
