# 🛡️ FraudShield — Intelligent Transaction Monitoring System

FraudShield is a full-stack web application that simulates a **banking system with real-time fraud detection**.
It analyzes user transactions using rule-based logic and assigns a **fraud risk score (0–100)**.

---

## 🚀 Features

* 🔐 User Authentication (Register / Login / Logout)
* 💸 Send Money Simulation
* 📊 Real-time Dashboard
* 📋 Transaction History with Fraud Analysis
* 🚨 Fraud Detection Engine
* ⚡ Live Risk Score Preview (Frontend)
* 🧠 Rule-based Fraud Detection System

---

## 🧠 Fraud Detection Logic

Each transaction is analyzed using multiple rules:

| Rule                    | Description             | Score Impact |
| ----------------------- | ----------------------- | ------------ |
| 💰 High Value           | > ₹50,000               | +40          |
| ⚡ Frequent Transactions | Multiple txns in 60 sec | +25 to +45   |
| 🌙 Odd Hours            | 12 AM – 5 AM            | +15          |
| 🔢 Round Amount         | ≥ ₹10,000 multiples     | +10          |
| 📈 Volume Spike         | > ₹1,00,000 in 5 min    | +20          |

### 🎯 Final Classification

* **0–49 → Safe**
* **50–79 → Suspicious**
* **80–100 → High Risk**

---

## 🏗️ Tech Stack

### Backend

* Python (Flask)
* SQLite Database
* REST API
* Session-based Authentication

### Frontend

* HTML, CSS, JavaScript (Vanilla)
* Responsive UI
* Real-time UI updates

---

## 📁 Project Structure

```
├── app.py                # Flask backend (API + fraud engine)
├── index.html           # Frontend UI
├── fraud_db.sqlite      # SQLite database
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/fraudshield.git
cd fraudshield
```

### 2. Install dependencies

```bash
pip install flask flask-cors
```

### 3. Run backend server

```bash
python app.py
```

Server will start at:

```
http://127.0.0.1:5000
```

---

### 4. Run frontend

Just open `index.html` in your browser.

---

## 🔌 API Endpoints

### Auth

* `POST /api/register`
* `POST /api/login`
* `POST /api/logout`
* `GET /api/me`

### Transactions

* `POST /api/transaction`
* `GET /api/transactions`
* `GET /api/stats`

---

## 📊 Example Response

```json
{
  "score": 65,
  "flags": [
    "HIGH_VALUE",
    "FREQUENT"
  ],
  "is_fraud": true
}
```

---

## ⚠️ Limitations

* Rule-based (not ML-based)
* No real payment integration
* No email/OTP verification
* Basic security (not production-ready)

---

## 🔮 Future Improvements

* 🤖 Machine Learning fraud detection
* 📱 Mobile responsive improvements
* 🔐 JWT authentication
* 📊 Advanced analytics dashboard
* 🌐 Deployment (AWS / Render)

---

