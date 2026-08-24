# FraudShield

**FraudShield** is a full-stack educational banking simulation and fraud monitoring system built with **Python, Flask, SQLite, JavaScript, and Machine Learning**.

It simulates banking transactions and evaluates them using an explainable **rule-based fraud detection system**, with an optional **Random Forest ML model** for fraud probability prediction.

>  **Educational Project:** FraudShield does not connect to real banks, payment networks, or production financial systems. No real money is transferred.

##  Live Demo

**Live Application:** https://fraudshield-be3o.onrender.com

**GitHub Repository:** https://github.com/mahiiarya0089-wq/FraudShield

The application is deployed using **Render** and automatically redeploys when changes are pushed to the `main` branch.

---

##  Features

###  Authentication

* User registration
* User login and logout
* Session-protected APIs
* Password hashing using Werkzeug
* Current-session user endpoint

###  Banking Simulation

* Simulated account balance
* Deposit/refill workflow
* Transfer/payment workflow
* Balance validation
* Insufficient-balance protection
* Transaction history

###  Fraud Detection

* Real-time fraud risk scoring
* LOW, MEDIUM, and HIGH risk levels
* Explainable fraud reasons
* High-value transaction detection
* Multiple transfers within a short period
* Late-night transaction detection
* Large round-number detection
* High transfer-volume detection
* Insufficient-balance detection
* Flagged and blocked transactions

###  Machine Learning

* Random Forest fraud detection model
* Model saved using Joblib
* Optional ML prediction layer
* Credit-card fraud dataset used for model training
* ROC-AUC and classification metrics available

###  Dashboard

* Current simulated balance
* Total transactions
* Total spending
* Fraud detection statistics
* Safe transaction count
* Fraud rate
* Transaction trend chart
* Risk distribution chart
* Recent transactions
* Searchable transaction history
* Fraud alert section

###  Testing

* Pytest test suite
* Authentication tests
* Deposit tests
* Transaction tests
* Fraud scoring tests
* Unauthorized access tests
* Transaction retrieval tests

---

##  Tech Stack

| Category         | Technologies                |
| ---------------- | --------------------------- |
| Backend          | Python, Flask, Flask-CORS   |
| Database         | SQLite                      |
| Frontend         | HTML, CSS, JavaScript       |
| Charts           | Canvas                      |
| Machine Learning | scikit-learn, pandas, NumPy |
| Model Storage    | Joblib                      |
| Testing          | pytest                      |
| Deployment       | Render                      |
| Version Control  | Git, GitHub                 |

---

##  System Architecture

```text
                    ┌──────────────────────┐
                    │   Browser Dashboard  │
                    │ HTML/CSS/JavaScript  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Flask API       │
                    │ Authentication + API │
                    └──────────┬───────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
        ┌─────────────┐ ┌──────────────┐ ┌─────────────┐
        │   SQLite    │ │ Rule-Based   │ │ Random      │
        │  Database   │ │ Fraud Engine │ │ Forest ML   │
        └─────────────┘ └──────────────┘ └─────────────┘
```

---

##  Fraud Detection Approach

FraudShield combines an **explainable rule-based scoring system** with an optional **Machine Learning model**.

The rule-based system is intentionally simple and transparent so that every risk decision can be explained to the user.

### Current Detection Rules

The system considers factors such as:

* High transaction amount
* Multiple transfers within a short time
* Late-night transaction timing
* Large round-number transactions
* High total transfer volume within five minutes
* Insufficient account balance

The detected conditions contribute to the transaction's overall risk score.

---

## Risk Scoring

|  Score | Risk Level | Default Behavior                  |
| -----: | ---------- | --------------------------------- |
|   0–30 | 🟢 LOW     | Transaction completed             |
|  31–70 | 🟡 MEDIUM  | Transaction completed and flagged |
| 71–100 | 🔴 HIGH    | Transaction blocked for review    |

The dashboard displays both the **risk score** and the **reasons** that contributed to the score.

---

##  Machine Learning Model

FraudShield includes a trained **Random Forest** model located at:

```text
ml/saved_model/fraud_model.joblib
```

The model uses the common credit-card fraud dataset feature structure:

```text
Time
V1 ... V28
Amount
```

### Important Design Note

Normal FraudShield banking transactions only provide banking-style inputs such as:

* Amount
* Recipient
* Transaction type
* Timestamp

They do not contain the original `V1`–`V28` PCA-style features.

Therefore, the live banking workflow primarily relies on the **explainable rule-based fraud engine**, while the ML model is available as an optional prediction layer.

This distinction keeps the live transaction decisions understandable and avoids presenting the ML model as a production banking fraud detector.

---

##  Model Performance

The Random Forest model was evaluated on a held-out test set.

| Metric          |     Result |
| --------------- | ---------: |
| ROC-AUC         | **0.9573** |
| Fraud Precision |   **0.91** |
| Fraud Recall    |   **0.79** |
| Fraud F1-Score  |   **0.84** |

### Confusion Matrix

```text
[[56856,     8],
 [   21,    77]]
```

These results are provided for **educational and portfolio demonstration purposes** and should not be interpreted as production banking performance.

---

##  Project Structure

```text
FraudShield/
│
├── app.py
├── index.html
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
├── README.md
│
├── tests/
│   └── test_app.py
│
└── ml/
    ├── train_model.py
    │
    └── saved_model/
        └── fraud_model.joblib
```

### Local-only files

The following files are intentionally not committed to GitHub:

```text
data/creditcard.csv
fraud_db.sqlite
.env
venv/
```

The dataset is ignored because it is large, while the local database, environment file, and virtual environment contain machine-specific or sensitive information.

---

##  Installation

### 1. Clone the Repository

```bash
git clone https://github.com/mahiiarya0089-wq/FraudShield.git
cd FraudShield
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

#### Windows

```powershell
venv\Scripts\activate
```

#### macOS / Linux

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

##  Running the Application Locally

Start the Flask application:

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

---

##  Environment Variables

An example environment configuration is provided in:

```text
.env.example
```

For local development, configure a strong secret key:

```text
SECRET_KEY=your-secret-key
```

Never commit real secrets or API keys to GitHub.

---

##  Deployment

FraudShield is deployed using **Render**.

### Render Configuration

| Setting       | Value                             |
| ------------- | --------------------------------- |
| Runtime       | Python 3                          |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app`                |
| Branch        | `main`                            |

### Deployment Workflow

```text
Local Changes
      ↓
Git
      ↓
GitHub main branch
      ↓
Render
      ↓
Automatic Deployment
      ↓
Live FraudShield Application
```

Live application:

**https://fraudshield-be3o.onrender.com**

> Render's free instance may spin down after inactivity, so the first request after a period of inactivity can take longer.

---

##  API Endpoints

FraudShield exposes REST-style API endpoints.

### Authentication

| Method | Endpoint        | Purpose                  |
| ------ | --------------- | ------------------------ |
| POST   | `/api/register` | Create a new user        |
| POST   | `/api/login`    | Log in                   |
| POST   | `/api/logout`   | Log out                  |
| GET    | `/api/me`       | Get current session user |

### Banking & Monitoring

| Method | Endpoint            | Purpose                       |
| ------ | ------------------- | ----------------------------- |
| POST   | `/api/deposit`      | Add simulated money           |
| POST   | `/api/transaction`  | Create a monitored transfer   |
| GET    | `/api/transactions` | Retrieve transaction history  |
| GET    | `/api/stats`        | Retrieve dashboard statistics |
| POST   | `/api/ml-predict`   | Run ML prediction             |

---

##  Database

FraudShield uses **SQLite** for local persistence.

### Users Table

Stores information such as:

* Username
* Email
* Hashed password
* Simulated balance
* Account creation date

### Transactions Table

Stores information such as:

* Transaction ID
* User
* Transaction type
* Recipient
* Amount
* Timestamp
* Risk score
* Risk level
* Transaction status
* Fraud reasons

The application automatically creates missing tables and handles required transaction columns for older local databases.

---

##  Example User Workflow

```text
1. Register
      ↓
2. Login
      ↓
3. View Dashboard
      ↓
4. Check Balance
      ↓
5. Deposit / Refill
      ↓
6. Create Transfer
      ↓
7. Fraud Detection
      ↓
8. Risk Score Generated
      ↓
9. Transaction Completed / Flagged / Blocked
      ↓
10. Review Transaction History
      ↓
11. Review Fraud Alerts
      ↓
12. Logout
```

---

##  Testing

Run the complete test suite:

```bash
pytest
```

The tests use a temporary SQLite database and cover core backend behavior including:

* User registration
* User login
* Unauthorized access
* Deposits
* Normal transfers
* Insufficient balance
* Fraud scoring
* Transaction retrieval

### Test Result

The project test suite currently contains **7 tests** covering the main backend workflows.

---

##  Why This Project?

Fraud detection is an important application of data science and machine learning.

FraudShield was created to demonstrate how:

* Backend APIs
* Databases
* Authentication
* Rule-based decision systems
* Machine learning
* Data analysis
* Automated testing
* Frontend dashboards
* Cloud deployment

can be combined into one complete software project.

---

##  Limitations

FraudShield is an educational project and has several limitations:

* It does not process real money.
* It does not connect to banks or payment networks.
* The fraud rules are intentionally simplified.
* The ML model is trained on a public credit-card fraud dataset.
* The dataset does not represent real banking production data.
* The live transfer workflow does not collect actual `V1`–`V28` model features.
* Rule-based explanations are therefore the primary detection mechanism for live simulated transactions.
* SQLite is suitable for this educational project but is not intended as the production database architecture for a large banking platform.
* Authentication and security features are designed for demonstration rather than production financial services.

---

##  Future Improvements

Possible future improvements include:

* [ ] Split Flask backend into modular services
* [ ] Add Flask-Migrate or Alembic for database migrations
* [ ] Add password reset functionality
* [ ] Add email verification
* [ ] Add admin fraud-review dashboard
* [ ] Add manual review actions for blocked transactions
* [ ] Add model versioning
* [ ] Add richer ML explanations
* [ ] Add improved transaction anomaly detection
* [ ] Add API documentation with Swagger/OpenAPI
* [ ] Add automated CI/CD testing with GitHub Actions
* [ ] Add a production-grade database such as PostgreSQL
* [ ] Improve deployment configuration

---

##  Educational Disclaimer

FraudShield is intended solely for **educational, portfolio, and interview demonstration purposes**.

It should not be used to make real financial, banking, credit, or fraud decisions.

---
## 👩‍💻 Author

**Mahee Arya**  
BCA — Artificial Intelligence & Data Science

[GitHub](https://github.com/mahiiarya0089-wq)

---

## ⭐ Project Links

| Resource     | Link                                            |
| ------------ | ----------------------------------------------- |
| 💻 GitHub    | https://github.com/mahiiarya0089-wq/FraudShield |
| 🚀 Live Demo | https://fraudshield-be3o.onrender.com           

If you found this project useful, consider giving the repository a ⭐ on GitHub.
