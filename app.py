from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sqlite3
import hashlib
import os
import time
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.secret_key = "fraud_detection_bca_2024_secret"
CORS(app, supports_credentials=True, origins=["*"])

DB_PATH = "fraud_db.sqlite"

# ─────────────────────────────────────────
#  DATABASE SETUP
# ─────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            balance     REAL    DEFAULT 100000.0,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # Transactions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id       INTEGER NOT NULL,
            receiver_name   TEXT    NOT NULL,
            amount          REAL    NOT NULL,
            description     TEXT,
            timestamp       TEXT    DEFAULT (datetime('now')),
            unix_ts         REAL    DEFAULT (strftime('%s','now')),
            fraud_score     INTEGER DEFAULT 0,
            fraud_flags     TEXT    DEFAULT '[]',
            is_fraud        INTEGER DEFAULT 0,
            status          TEXT    DEFAULT 'completed',
            FOREIGN KEY(sender_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅  Database initialised")

init_db()

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def analyze_fraud(sender_id: int, amount: float, description: str) -> dict:
    """
    Core fraud-detection engine.
    Returns  { score: 0-100, flags: [...], is_fraud: bool }
    """
    flags  = []
    score  = 0
    conn   = get_db()
    c      = conn.cursor()
    now_ts = time.time()

    # ── Rule 1: Large-amount check (> ₹50,000) ──────────────────────────────
    if amount > 50_000:
        flags.append(f"HIGH_VALUE: Transaction ₹{amount:,.0f} exceeds ₹50,000 limit")
        score += 40
    elif amount > 25_000:
        flags.append(f"MODERATE_VALUE: Transaction ₹{amount:,.0f} is above ₹25,000")
        score += 15

    # ── Rule 2: Frequency check (multiple txn within 60 s) ──────────────────
    c.execute("""
        SELECT COUNT(*) as cnt FROM transactions
        WHERE sender_id = ? AND unix_ts > ?
    """, (sender_id, now_ts - 60))
    row = c.fetchone()
    recent_count = row["cnt"] if row else 0

    if recent_count >= 4:
        flags.append(f"RAPID_FIRE: {recent_count} transactions in last 60 seconds")
        score += 45
    elif recent_count >= 2:
        flags.append(f"FREQUENT: {recent_count} transactions in last 60 seconds")
        score += 25

    # ── Rule 3: Odd hour (12 AM – 5 AM IST) ─────────────────────────────────
    hour = datetime.now().hour
    if 0 <= hour < 5:
        flags.append(f"ODD_HOUR: Transaction at {hour:02d}:00 (late night)")
        score += 15

    # ── Rule 4: Round number suspicion ──────────────────────────────────────
    if amount >= 10_000 and amount % 10_000 == 0:
        flags.append(f"ROUND_AMOUNT: Suspiciously round amount ₹{amount:,.0f}")
        score += 10

    # ── Rule 5: Rapid escalation – same receiver within 5 min ───────────────
    c.execute("""
        SELECT SUM(amount) as total FROM transactions
        WHERE sender_id = ? AND unix_ts > ?
    """, (sender_id, now_ts - 300))
    row = c.fetchone()
    total_5min = (row["total"] or 0) + amount
    if total_5min > 1_00_000:
        flags.append(f"VOLUME_SPIKE: ₹{total_5min:,.0f} total in last 5 minutes")
        score += 20

    conn.close()

    score     = min(score, 100)
    is_fraud  = score >= 50
    return {"score": score, "flags": flags, "is_fraud": is_fraud}

# ─────────────────────────────────────────
#  AUTH ROUTES
# ─────────────────────────────────────────
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "").strip()
    email    = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not all([username, email, password]):
        return jsonify({"error": "All fields required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, hash_password(password))
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Registration successful! Please login."}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username or email already exists"}), 409

@app.route("/api/login", methods=["POST"])
def login():
    data     = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, hash_password(password))
    ).fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    session["user_id"]   = user["id"]
    session["username"]  = user["username"]
    return jsonify({
        "message": "Login successful",
        "user": {
            "id":       user["id"],
            "username": user["username"],
            "email":    user["email"],
            "balance":  user["balance"]
        }
    })

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

@app.route("/api/me", methods=["GET"])
def me():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    conn.close()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "id":       user["id"],
        "username": user["username"],
        "email":    user["email"],
        "balance":  user["balance"]
    })

# ─────────────────────────────────────────
#  TRANSACTION ROUTES
# ─────────────────────────────────────────
@app.route("/api/transaction", methods=["POST"])
def create_transaction():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    data          = request.get_json()
    receiver_name = data.get("receiver", "").strip()
    amount        = float(data.get("amount", 0))
    description   = data.get("description", "").strip()

    if not receiver_name or amount <= 0:
        return jsonify({"error": "Invalid transaction data"}), 400

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()

    if user["balance"] < amount:
        conn.close()
        return jsonify({"error": "Insufficient balance"}), 400

    # Run fraud analysis
    analysis = analyze_fraud(uid, amount, description)

    # Deduct balance
    conn.execute(
        "UPDATE users SET balance = balance - ? WHERE id = ?",
        (amount, uid)
    )

    # Insert transaction
    conn.execute("""
        INSERT INTO transactions
            (sender_id, receiver_name, amount, description,
             fraud_score, fraud_flags, is_fraud, unix_ts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        uid, receiver_name, amount, description,
        analysis["score"],
        json.dumps(analysis["flags"]),
        int(analysis["is_fraud"]),
        time.time()
    ))
    conn.commit()
    conn.close()

    return jsonify({
        "message":    "Transaction processed",
        "amount":     amount,
        "receiver":   receiver_name,
        "fraud_analysis": analysis
    }), 201

@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM transactions
        WHERE sender_id = ?
        ORDER BY id DESC LIMIT 50
    """, (uid,)).fetchall()
    conn.close()

    txns = []
    for r in rows:
        txns.append({
            "id":            r["id"],
            "receiver":      r["receiver_name"],
            "amount":        r["amount"],
            "description":   r["description"],
            "timestamp":     r["timestamp"],
            "fraud_score":   r["fraud_score"],
            "fraud_flags":   json.loads(r["fraud_flags"]),
            "is_fraud":      bool(r["is_fraud"]),
            "status":        r["status"]
        })
    return jsonify(txns)

@app.route("/api/stats", methods=["GET"])
def get_stats():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401

    conn = get_db()
    total    = conn.execute("SELECT COUNT(*) FROM transactions WHERE sender_id=?",  (uid,)).fetchone()[0]
    fraud    = conn.execute("SELECT COUNT(*) FROM transactions WHERE sender_id=? AND is_fraud=1", (uid,)).fetchone()[0]
    total_am = conn.execute("SELECT SUM(amount) FROM transactions WHERE sender_id=?", (uid,)).fetchone()[0] or 0
    user     = conn.execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()

    return jsonify({
        "total_transactions": total,
        "fraud_detected":     fraud,
        "safe_transactions":  total - fraud,
        "total_spent":        round(total_am, 2),
        "balance":            round(user["balance"], 2),
        "fraud_rate":         round((fraud / total * 100) if total else 0, 1)
    })

# ─────────────────────────────────────────
if __name__ == "__main__":
    print("🚀  Starting Fraud Detection Server on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
