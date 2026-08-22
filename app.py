from datetime import datetime
import hashlib
import json
import os
import sqlite3
import time
from uuid import uuid4

import joblib
import pandas as pd
from flask import Flask, jsonify, request, send_file, session
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("FRAUDSHIELD_DB_PATH", os.path.join(BASE_DIR, "fraud_db.sqlite"))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "saved_model", "fraud_model.joblib")
DEFAULT_BALANCE = 100000.0
HIGH_RISK_BLOCKS_TRANSACTION = True

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-dev-secret")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://127.0.0.1:5000",
        "http://localhost:5000",
    ],
)


def log(*values):
    message = " ".join(str(value) for value in values)
    print(message.encode("ascii", errors="backslashreplace").decode("ascii"))


try:
    fraud_model = joblib.load(MODEL_PATH)
    log("[OK] ML fraud model loaded")
except Exception as exc:
    fraud_model = None
    log("[WARN] ML fraud model unavailable:", exc)


def api_response(success=True, message="", data=None, status=200):
    payload = {"success": success, "message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def column_exists(conn, table_name, column_name):
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row["name"] == column_name for row in rows)


def add_column_if_missing(conn, table_name, column_name, definition):
    if not column_exists(conn, table_name, column_name):
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def init_db():
    db_directory = os.path.dirname(DB_PATH)
    if db_directory:
        os.makedirs(db_directory, exist_ok=True)
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            balance REAL DEFAULT 100000.0,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE,
            sender_id INTEGER NOT NULL,
            receiver_name TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_type TEXT DEFAULT 'transfer',
            description TEXT,
            timestamp TEXT DEFAULT (datetime('now', 'localtime')),
            unix_ts REAL DEFAULT (strftime('%s','now')),
            fraud_score INTEGER DEFAULT 0,
            fraud_flags TEXT DEFAULT '[]',
            risk_level TEXT DEFAULT 'LOW',
            is_fraud INTEGER DEFAULT 0,
            status TEXT DEFAULT 'completed',
            FOREIGN KEY(sender_id) REFERENCES users(id)
        )
        """
    )

    add_column_if_missing(conn, "transactions", "transaction_id", "TEXT")
    add_column_if_missing(conn, "transactions", "transaction_type", "TEXT DEFAULT 'transfer'")
    add_column_if_missing(conn, "transactions", "risk_level", "TEXT DEFAULT 'LOW'")

    rows = conn.execute("SELECT id FROM transactions WHERE transaction_id IS NULL OR transaction_id = ''").fetchall()
    for row in rows:
        conn.execute(
            "UPDATE transactions SET transaction_id = ? WHERE id = ?",
            (generate_transaction_id(), row["id"]),
        )
    conn.commit()
    conn.close()
    log("[OK] Database ready")


def reset_database_for_tests():
    conn = get_db()
    conn.execute("DROP TABLE IF EXISTS transactions")
    conn.execute("DROP TABLE IF EXISTS users")
    conn.commit()
    conn.close()
    init_db()


def generate_transaction_id():
    return f"TXN-{uuid4().hex[:10].upper()}"


def hash_password(password):
    return generate_password_hash(password)


def verify_password(stored_hash, password):
    legacy_sha256 = hashlib.sha256(password.encode()).hexdigest()
    if stored_hash == legacy_sha256:
        return True
    return check_password_hash(stored_hash, password)


def current_user_id():
    return session.get("user_id")


def require_auth():
    user_id = current_user_id()
    if not user_id:
        return None
    conn = get_db()
    user = conn.execute(
        "SELECT id, username, email, balance, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return user


def public_user(user):
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "balance": round(float(user["balance"]), 2),
        "created_at": user["created_at"],
    }


def clean_amount(value):
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None
    if amount <= 0 or amount > 10000000:
        return None
    return round(amount, 2)


def risk_level_from_score(score):
    if score < 40:
        return "LOW"
    elif score < 70:
        return "MEDIUM"
    else:
        return "HIGH"


def analyze_rules(user_id, amount, receiver_name="", transaction_type="transfer"):
    flags = []
    score = 0
    now_ts = time.time()
    conn = get_db()

    if transaction_type == "deposit":
        if amount >= 100000:
            flags.append("Large deposit amount entered for review")
            score += 15
        conn.close()
        return score, flags

    if amount > 50000:
        flags.append("Unusually large transaction above Rs. 50,000")
        score += 40
    elif amount > 25000:
        flags.append("Transaction amount is above Rs. 25,000")
        score += 15

    recent_count = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE sender_id = ? AND transaction_type = 'transfer' AND unix_ts > ?
        """,
        (user_id, now_ts - 60),
    ).fetchone()["count"]
    if recent_count >= 4:
        flags.append(f"Very high transaction frequency: {recent_count} transfers in 60 seconds")
        score += 45
    elif recent_count >= 2:
        flags.append(f"Multiple transfers in a short time: {recent_count} transfers in 60 seconds")
        score += 25

    if 0 <= datetime.now().hour < 5:
        flags.append("Late-night transaction timing")
        score += 15

    if amount >= 10000 and amount % 10000 == 0:
        flags.append("Large round-number amount")
        score += 10

    five_minute_total = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM transactions
        WHERE sender_id = ? AND transaction_type = 'transfer' AND unix_ts > ?
        """,
        (user_id, now_ts - 300),
    ).fetchone()["total"]
    if five_minute_total + amount > 100000:
        flags.append("Unusual total transfer volume in five minutes")
        score += 20

    if receiver_name and len(receiver_name) <= 2:
        flags.append("Recipient name is unusually short")
        score += 5

    conn.close()
    return min(score, 100), flags


def run_ml_prediction(amount):
    if fraud_model is None:
        return 0, 0

    try:
        required_features = [
            "Time",
            "V1",
            "V2",
            "V3",
            "V4",
            "V5",
            "V6",
            "V7",
            "V8",
            "V9",
            "V10",
            "V11",
            "V12",
            "V13",
            "V14",
            "V15",
            "V16",
            "V17",
            "V18",
            "V19",
            "V20",
            "V21",
            "V22",
            "V23",
            "V24",
            "V25",
            "V26",
            "V27",
            "V28",
            "Amount",
        ]
        values = {"Time": time.time(), "Amount": amount}
        for index in range(1, 29):
            values[f"V{index}"] = 0
        input_data = pd.DataFrame([[values[name] for name in required_features]], columns=required_features)
        prediction = int(fraud_model.predict(input_data)[0])
        probability = round(float(fraud_model.predict_proba(input_data)[0][1]) * 100, 2)
        return prediction, probability
    except Exception as exc:
        log("[WARN] ML prediction failed:", exc)
        return 0, 0


def analyze_fraud(user_id, amount, receiver_name="", transaction_type="transfer", balance=None):
    rule_score, flags = analyze_rules(user_id, amount, receiver_name, transaction_type)
    ml_prediction, ml_probability = run_ml_prediction(amount) if transaction_type == "transfer" else (0, 0)

    if balance is not None and transaction_type == "transfer" and amount > balance:
        flags.append("Insufficient balance")
        rule_score = max(rule_score, 90)

    weighted_score = round((rule_score * 0.75) + (ml_probability * 0.25))
    score = min(100, int(max(rule_score, weighted_score)))
    risk_level = risk_level_from_score(score)

    if ml_probability >= 75:
        flags.append(f"ML model probability is high: {ml_probability}%")
    elif ml_probability >= 40:
        flags.append(f"ML model probability is moderate: {ml_probability}%")

    if not flags:
        flags.append("No unusual pattern detected")

    return {
        "score": score,
        "risk_score": score,
        "risk_level": risk_level,
        "flags": flags,
        "reasons": flags,
        "is_fraud": risk_level == "HIGH",
        "rule_score": rule_score,
        "ml_prediction": ml_prediction,
        "ml_probability": ml_probability,
    }


def serialize_transaction(row):
    flags = []
    try:
        flags = json.loads(row["fraud_flags"] or "[]")
    except json.JSONDecodeError:
        flags = []
    return {
        "id": row["id"],
        "transaction_id": row["transaction_id"] or f"TXN-{row['id']:06d}",
        "type": row["transaction_type"] or "transfer",
        "receiver": row["receiver_name"],
        "recipient": row["receiver_name"],
        "amount": round(float(row["amount"]), 2),
        "description": row["description"] or "",
        "timestamp": row["timestamp"],
        "fraud_score": int(row["fraud_score"] or 0),
        "risk_score": int(row["fraud_score"] or 0),
        "risk_level": row["risk_level"] or risk_level_from_score(int(row["fraud_score"] or 0)),
        "fraud_flags": flags,
        "reasons": flags,
        "is_fraud": bool(row["is_fraud"]),
        "status": row["status"],
    }


@app.route("/")
def home():
    return send_file(os.path.join(BASE_DIR, "index.html"))


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not email or not password:
        return api_response(False, "Username, email, and password are required.", status=400)
    if len(username) < 3:
        return api_response(False, "Username must be at least 3 characters.", status=400)
    if "@" not in email or "." not in email:
        return api_response(False, "Enter a valid email address.", status=400)
    if len(password) < 6:
        return api_response(False, "Password must be at least 6 characters.", status=400)

    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, email, password, balance) VALUES (?, ?, ?, ?)",
            (username, email, hash_password(password), DEFAULT_BALANCE),
        )
        conn.commit()
        conn.close()
        return api_response(True, "Registration successful. Please log in.", status=201)
    except sqlite3.IntegrityError:
        return api_response(False, "Username or email already exists.", status=409)


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username.lower())).fetchone()
    conn.close()

    if not user or not verify_password(user["password"], password):
        return api_response(False, "Invalid username/email or password.", status=401)

    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return api_response(True, "Login successful.", {"user": public_user(user)})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return api_response(True, "Logged out successfully.")


@app.route("/api/me", methods=["GET"])
def me():
    user = require_auth()
    if not user:
        return api_response(False, "Not authenticated.", status=401)
    return api_response(True, "Authenticated user loaded.", {"user": public_user(user)})


@app.route("/api/deposit", methods=["POST"])
def deposit():
    user = require_auth()
    if not user:
        return api_response(False, "Not authenticated.", status=401)

    data = request.get_json(silent=True) or {}
    amount = clean_amount(data.get("amount"))
    description = (data.get("description") or "Account refill").strip()
    if amount is None:
        return api_response(False, "Deposit amount must be a positive number.", status=400)

    analysis = analyze_fraud(user["id"], amount, "Self account", "deposit")
    transaction_id = generate_transaction_id()
    conn = get_db()
    conn.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user["id"]))
    conn.execute(
        """
        INSERT INTO transactions (
            transaction_id, sender_id, receiver_name, amount, transaction_type,
            description, fraud_score, fraud_flags, risk_level, is_fraud, unix_ts, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            transaction_id,
            user["id"],
            "Self account",
            amount,
            "deposit",
            description,
            analysis["score"],
            json.dumps(analysis["flags"]),
            analysis["risk_level"],
            0,
            time.time(),
            "completed",
        ),
    )
    conn.commit()
    updated = conn.execute(
        "SELECT id, username, email, balance, created_at FROM users WHERE id = ?",
        (user["id"],),
    ).fetchone()
    conn.close()
    return api_response(
        True,
        "Deposit completed successfully.",
        {
            "transaction_id": transaction_id,
            "amount": amount,
            "balance": round(float(updated["balance"]), 2),
            "fraud_analysis": analysis,
        },
        status=201,
    )


@app.route("/api/transaction", methods=["POST"])
def create_transaction():
    user = require_auth()
    if not user:
        return api_response(False, "Not authenticated.", status=401)

    data = request.get_json(silent=True) or {}
    receiver_name = (data.get("receiver") or data.get("recipient") or "").strip()
    amount = clean_amount(data.get("amount"))
    description = (data.get("description") or "").strip()

    if not receiver_name:
        return api_response(False, "Recipient or merchant is required.", status=400)
    if amount is None:
        return api_response(False, "Transaction amount must be a positive number.", status=400)
    if float(user["balance"]) < amount:
        analysis = analyze_fraud(user["id"], amount, receiver_name, "transfer", balance=float(user["balance"]))
        return api_response(
            False,
            "Insufficient balance. Transaction was not created.",
            {"balance": round(float(user["balance"]), 2), "fraud_analysis": analysis},
            status=400,
        )

    analysis = analyze_fraud(user["id"], amount, receiver_name, "transfer", balance=float(user["balance"]))
    risk_level = analysis["risk_level"]

    if risk_level == "HIGH" and HIGH_RISK_BLOCKS_TRANSACTION:
        status = "blocked"
        deduct_balance = False
        message = "High-risk transaction blocked for review."
    elif risk_level == "MEDIUM":
        status = "flagged"
        deduct_balance = True
        message = "Transaction completed and flagged for monitoring."
    else:
        status = "completed"
        deduct_balance = True
        message = "Transaction completed successfully."

    transaction_id = generate_transaction_id()
    conn = get_db()
    if deduct_balance:
        conn.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, user["id"]))
    conn.execute(
        """
        INSERT INTO transactions (
            transaction_id, sender_id, receiver_name, amount, transaction_type,
            description, fraud_score, fraud_flags, risk_level, is_fraud, unix_ts, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            transaction_id,
            user["id"],
            receiver_name,
            amount,
            "transfer",
            description,
            analysis["score"],
            json.dumps(analysis["flags"]),
            risk_level,
            1 if risk_level == "HIGH" else 0,
            time.time(),
            status,
        ),
    )
    conn.commit()
    updated = conn.execute("SELECT balance FROM users WHERE id = ?", (user["id"],)).fetchone()
    conn.close()

    return api_response(
        True,
        message,
        {
            "transaction_id": transaction_id,
            "amount": amount,
            "receiver": receiver_name,
            "status": status,
            "balance": round(float(updated["balance"]), 2),
            "fraud_analysis": analysis,
        },
        status=201,
    )


@app.route("/api/stats", methods=["GET"])
def get_stats():
    user = require_auth()
    if not user:
        return api_response(False, "Not authenticated.", status=401)

    conn = get_db()
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS total_transactions,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS approved_transactions,
            SUM(CASE WHEN status IN ('flagged', 'blocked') OR risk_level IN ('MEDIUM', 'HIGH') THEN 1 ELSE 0 END) AS flagged_transactions,
            SUM(CASE WHEN transaction_type = 'transfer' AND status IN ('completed', 'flagged') THEN amount ELSE 0 END) AS total_amount_transacted,
            SUM(CASE WHEN transaction_type = 'deposit' THEN amount ELSE 0 END) AS total_deposited
        FROM transactions
        WHERE sender_id = ?
        """,
        (user["id"],),
    ).fetchone()
    risk_rows = conn.execute(
        """
        SELECT risk_level, COUNT(*) AS count
        FROM transactions
        WHERE sender_id = ?
        GROUP BY risk_level
        """,
        (user["id"],),
    ).fetchall()
    trend_rows = conn.execute(
        """
        SELECT substr(timestamp, 1, 10) AS day, COUNT(*) AS count, COALESCE(SUM(amount), 0) AS amount
        FROM transactions
        WHERE sender_id = ?
        GROUP BY substr(timestamp, 1, 10)
        ORDER BY day ASC
        LIMIT 10
        """,
        (user["id"],),
    ).fetchall()
    conn.close()

    total = row["total_transactions"] or 0
    flagged = row["flagged_transactions"] or 0
    approved = row["approved_transactions"] or 0
    risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for risk_row in risk_rows:
        risk_distribution[risk_row["risk_level"] or "LOW"] = risk_row["count"]

    return api_response(
        True,
        "Dashboard statistics loaded.",
        {
            "balance": round(float(user["balance"]), 2),
            "total_transactions": total,
            "approved_transactions": approved,
            "flagged_transactions": flagged,
            "fraud_detected": risk_distribution["HIGH"],
            "safe_transactions": approved,
            "total_amount_transacted": round(float(row["total_amount_transacted"] or 0), 2),
            "total_deposited": round(float(row["total_deposited"] or 0), 2),
            "fraud_rate": round((flagged / total * 100) if total else 0, 1),
            "risk_distribution": risk_distribution,
            "trend": [
                {
                    "day": trend["day"],
                    "count": trend["count"],
                    "amount": round(float(trend["amount"] or 0), 2),
                }
                for trend in trend_rows
            ],
        },
    )


@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    user = require_auth()
    if not user:
        return api_response(False, "Not authenticated.", status=401)

    conn = get_db()
    rows = conn.execute(
        """
        SELECT *
        FROM transactions
        WHERE sender_id = ?
        ORDER BY id DESC
        """,
        (user["id"],),
    ).fetchall()
    conn.close()
    return api_response(
        True,
        "Transactions loaded.",
        {"transactions": [serialize_transaction(row) for row in rows]},
    )


@app.route("/api/ml-predict", methods=["POST"])
def ml_predict():
    if fraud_model is None:
        return api_response(False, "ML model is not loaded.", status=500)

    data = request.get_json(silent=True) or {}
    required_features = [
        "Time",
        "V1",
        "V2",
        "V3",
        "V4",
        "V5",
        "V6",
        "V7",
        "V8",
        "V9",
        "V10",
        "V11",
        "V12",
        "V13",
        "V14",
        "V15",
        "V16",
        "V17",
        "V18",
        "V19",
        "V20",
        "V21",
        "V22",
        "V23",
        "V24",
        "V25",
        "V26",
        "V27",
        "V28",
        "Amount",
    ]
    missing = [feature for feature in required_features if feature not in data]
    if missing:
        return api_response(False, "Missing required ML features.", {"missing": missing}, status=400)

    try:
        input_data = pd.DataFrame([[data[feature] for feature in required_features]], columns=required_features)
        prediction = int(fraud_model.predict(input_data)[0])
        probability = round(float(fraud_model.predict_proba(input_data)[0][1]) * 100, 2)
        return api_response(
            True,
            "ML prediction completed.",
            {
                "prediction": prediction,
                "is_fraud": bool(prediction),
                "fraud_probability": probability,
                "risk_level": risk_level_from_score(int(probability)),
            },
        )
    except Exception as exc:
        return api_response(False, "ML prediction failed.", {"details": str(exc)}, status=500)


init_db()


if __name__ == "__main__":
    log("Starting FraudShield on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
