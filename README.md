# FraudShield

FraudShield is a full-stack educational banking simulation and fraud monitoring project. It combines a Flask REST API, SQLite persistence, a responsive HTML/CSS/JavaScript dashboard, rule-based fraud checks, and an optional trained machine learning model.

FraudShield is built for portfolio and interview demonstration. It does not connect to real banks, payment networks, or production fraud systems.

## Features

- User registration, login, logout, and session-protected APIs
- Password hashing with Werkzeug
- Simulated account balance
- Deposit/refill workflow
- Transfer/payment workflow with balance checks
- Rule-based fraud scoring with clear reasons
- Optional Random Forest ML fraud probability layer
- LOW, MEDIUM, and HIGH risk levels
- Completed, flagged, and blocked transaction statuses
- Dashboard statistics from real database data
- Transaction trend and risk distribution charts
- Recent transactions and full searchable/filterable transaction history
- Fraud alert section for medium/high risk activity
- Consistent JSON API responses
- Basic pytest coverage for core backend behavior

## Tech Stack

- Backend: Python, Flask, Flask-CORS
- Database: SQLite
- Frontend: HTML, CSS, JavaScript, Canvas charts
- Machine Learning: pandas, scikit-learn, joblib
- Testing: pytest

## System Architecture

```text
Browser dashboard
      |
      v
Flask REST API
      |
      +-- SQLite users and transactions
      |
      +-- Rule-based fraud detector
      |
      +-- Optional ML model: ml/saved_model/fraud_model.joblib
```

## Fraud Detection Approach

FraudShield combines understandable rules with the saved ML model when available. Rules are intentionally simple so the system is easy to explain in a student portfolio project.

Rules currently include:

- High transaction amount
- Multiple transfers within a short time
- Late-night transaction timing
- Large round-number amounts
- High total transfer volume within five minutes
- Insufficient balance detection

The ML model expects the common credit-card fraud dataset feature shape: `Time`, `V1` to `V28`, and `Amount`. For normal app transfers, the dashboard has only banking-style inputs, so the backend uses the real amount and neutral placeholder values for the PCA-style model features. The rule-based reasons are therefore the most explainable part of the live transaction workflow.

## Risk Scoring

| Score | Risk Level | Default Behavior |
| ---: | --- | --- |
| 0-30 | LOW | Transaction completed |
| 31-70 | MEDIUM | Transaction completed and flagged |
| 71-100 | HIGH | Transaction blocked for review |

## Screenshots

Add screenshots here after running the app locally:

- Login/register screen
- Dashboard
- Deposit and transfer workflow
- Transaction history
- Fraud alerts

## Project Structure

```text
FraudShield/
|-- app.py
|-- index.html
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- README.md
|-- tests/
|   `-- test_app.py
|-- ml/
|   |-- train_model.py
|   `-- saved_model/
|       `-- fraud_model.joblib
`-- data/
    `-- creditcard.csv
```

`data/creditcard.csv` is intentionally ignored because it is a large local dataset. Local SQLite databases are also ignored.

## Installation

```bash
git clone https://github.com/mahiiarya0089-wq/FraudShield.git
cd FraudShield
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

macOS/Linux:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Running The Application

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

Optional environment setup:

```bash
cp .env.example .env
```

Set a strong `SECRET_KEY` before sharing or deploying the project.

## API Endpoints

All API responses use:

```json
{
  "success": true,
  "message": "Readable message",
  "data": {}
}
```

Authentication:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/register` | Create a user |
| POST | `/api/login` | Log in |
| POST | `/api/logout` | Log out |
| GET | `/api/me` | Load current session user |

Banking and monitoring:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/deposit` | Add simulated money |
| POST | `/api/transaction` | Create a monitored transfer |
| GET | `/api/transactions` | Retrieve transaction history |
| GET | `/api/stats` | Retrieve dashboard statistics |
| POST | `/api/ml-predict` | Run direct ML prediction with model features |

## Database

SQLite stores:

- `users`: username, email, hashed password, balance, creation date
- `transactions`: transaction ID, user, type, recipient, amount, timestamp, risk score, risk level, status, and fraud reasons

The app creates missing tables automatically and adds missing transaction columns for older local databases.

## Machine Learning Model

The saved model lives at:

```text
ml/saved_model/fraud_model.joblib
```

To retrain it, place the dataset at:

```text
data/creditcard.csv
```

Then run:

```bash
python ml/train_model.py
```

## Example Workflow

1. Register a new account.
2. Log in.
3. Review the starting simulated balance.
4. Add a deposit/refill.
5. Create a normal transfer.
6. Create a large or suspicious transfer.
7. Review risk score, risk level, status, and fraud reasons.
8. Open transaction history and alerts.
9. Log out.

## Testing

```bash
pytest
```

The tests use a temporary SQLite database and cover registration, login, unauthorized access, deposit, normal transfers, insufficient balance, fraud scoring, and transaction retrieval.

## Limitations

- This is a simulated educational project, not a bank-grade fraud system.
- The dashboard does not move real money.
- The ML model is trained on a public credit-card style dataset and does not represent real banking production behavior.
- The live transfer form does not collect real `V1` to `V28` features, so rule-based explanations are the primary live detection mechanism.

## Future Improvements

- Split the backend into `backend/` modules as the project grows
- Add Alembic or Flask-Migrate for formal database migrations
- Add password reset and email verification
- Add admin review actions for blocked transactions
- Add model versioning and richer ML explanations
- Add deployment configuration

## Author

Mahee Arya  
BCA - Artificial Intelligence & Data Science  
GitHub: [@mahiiarya0089-wq](https://github.com/mahiiarya0089-wq)
