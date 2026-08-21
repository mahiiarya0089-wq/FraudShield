#  FraudShield — Intelligent Transaction Monitoring & Fraud Detection System

FraudShield is a full-stack transaction monitoring application that combines a **Flask-based banking simulation**, **rule-based fraud analysis**, and a **Machine Learning fraud detection model** to identify potentially fraudulent transactions.

The system provides a transaction dashboard, authentication, transaction history, risk analysis, and an ML-powered fraud detection pipeline using **Random Forest**.

>  **Disclaimer:** FraudShield is an educational/project application and does not connect to real banking or payment systems.

---

##  Key Features

*  User registration, login and logout
*  Simulated money transactions
*  Transaction monitoring dashboard
*  Transaction history
*  Rule-based fraud detection
*  Machine Learning fraud detection
*  Class-imbalance handling using balanced Random Forest
*  Fraud probability prediction
*  Classification report and confusion matrix
*  ROC-AUC evaluation
*  Saved ML model using Joblib
*  Real-time frontend risk preview

---

##  Fraud Detection Approach

FraudShield uses **two complementary detection approaches**.

### 1. Rule-Based Detection

Transactions can be evaluated using predefined behavioral rules such as:

| Rule                    | Description                                   | Score Impact |
| ----------------------- | --------------------------------------------- | -----------: |
| 💰 High Value           | Transaction above ₹50,000                     |          +40 |
| ⚡ Frequent Transactions | Multiple transactions within 60 seconds       |   +25 to +45 |
| 🌙 Odd Hours            | Transactions between 12 AM–5 AM               |          +15 |
| 🔢 Round Amount         | Large round-number transactions               |          +10 |
| 📈 Volume Spike         | High transaction volume within a short period |          +20 |

### Risk Classification

|  Score | Classification |
| -----: | -------------- |
|   0–49 | 🟢 Safe        |
|  50–79 | 🟠 Suspicious  |
| 80–100 | 🔴 High Risk   |

---

#  Machine Learning Pipeline

FraudShield also includes a dedicated ML pipeline for detecting fraudulent transactions from historical transaction data.

### Algorithm

The current model uses:

**Random Forest Classifier**

with:

* `n_estimators = 100`
* `class_weight = "balanced"`
* `random_state = 42`
* `n_jobs = -1`

The balanced class weighting is particularly useful because fraudulent transactions represent a much smaller portion of the dataset than legitimate transactions.

### ML Workflow

```text
Historical Transaction Dataset
              ↓
       Data Loading
              ↓
    Feature / Target Split
              ↓
   Stratified Train/Test Split
              ↓
      Random Forest Model
              ↓
       Fraud Prediction
              ↓
 ┌────────────┬──────────────┐
 ↓            ↓              ↓
Classification  Confusion   ROC-AUC
   Report       Matrix       Score
              ↓
       Save Trained Model
              ↓
       fraud_model.joblib
```

---

##  Model Evaluation

The training pipeline evaluates the model using:

### Classification Report

Provides:

* Precision
* Recall
* F1-score
* Support

### Confusion Matrix

Used to analyze:

* True Positives
* True Negatives
* False Positives
* False Negatives

### ROC-AUC

The model also calculates the **ROC-AUC score** using predicted fraud probabilities.

> Model performance values should be generated from the current training run rather than hard-coded into the documentation.

---

##  System Architecture

```text
                 ┌─────────────────────┐
                 │      Frontend       │
                 │ HTML / CSS / JS     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    Flask Backend    │
                 │       app.py        │
                 └──────────┬──────────┘
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
        ┌─────────────────┐   ┌──────────────────┐
        │ Rule-Based      │   │ ML Fraud Model   │
        │ Fraud Engine    │   │ Random Forest    │
        └────────┬────────┘   └─────────┬────────┘
                 │                      │
                 └──────────┬───────────┘
                            ▼
                   Transaction Analysis
                            │
                            ▼
                     Risk / Prediction
```

---

##  Tech Stack

### Backend

* Python
* Flask
* Flask-CORS
* SQLite
* REST API

### Machine Learning

* Python
* Pandas
* Scikit-learn
* Random Forest
* Joblib

### Frontend

* HTML
* CSS
* JavaScript
* Responsive dashboard UI

### Development Tools

* Git
* GitHub
* VS Code
* Python Virtual Environment

---

## Project Structure

```text
FraudShield/
│
├── app.py
├── index.html
├── README.md
├── .gitignore
│
├── ml/
│   ├── train_model.py
│   └── saved_model/
│       └── fraud_model.joblib
│
└── data/
    └── creditcard.csv
```

> `data/creditcard.csv` is intentionally excluded from GitHub because the dataset is approximately 150 MB and exceeds GitHub's normal per-file limit.

The local SQLite database is also excluded from version control.

---

# ⚙️ Installation & Setup

## 1. Clone the repository

```bash
git clone https://github.com/mahiiarya0089-wq/FraudShield.git
cd FraudShield
```

## 2. Create a virtual environment

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install dependencies

```bash
pip install flask flask-cors pandas scikit-learn joblib
```

## 4. Run the application

```bash
python app.py
```

The Flask server should start at:

```text
http://127.0.0.1:5000
```

Open the address in your browser.

---

# 🤖 Training the ML Model

The training script expects the dataset at:

```text
data/creditcard.csv
```

After placing the dataset in the `data` directory, run:

```bash
python ml/train_model.py
```

The script will:

1. Load the transaction dataset
2. Separate features and target
3. Display class distribution
4. Perform a stratified train/test split
5. Train the Random Forest classifier
6. Generate predictions
7. Calculate evaluation metrics
8. Calculate ROC-AUC
9. Save the trained model

The trained model is saved as:

```text
ml/saved_model/fraud_model.joblib
```

---

# 🔌 API Endpoints

## Authentication

| Method | Endpoint        | Purpose          |
| ------ | --------------- | ---------------- |
| POST   | `/api/register` | Register a user  |
| POST   | `/api/login`    | Login            |
| POST   | `/api/logout`   | Logout           |
| GET    | `/api/me`       | Get current user |

## Transactions

| Method | Endpoint            | Purpose                         |
| ------ | ------------------- | ------------------------------- |
| POST   | `/api/transaction`  | Create/analyze transaction      |
| GET    | `/api/transactions` | Retrieve transaction history    |
| GET    | `/api/stats`        | Retrieve transaction statistics |

---

##  Example Fraud Analysis Response

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

#  Future Improvements

*  Integrate ML predictions directly into the transaction API
*  Add advanced fraud analytics and visualizations
*  Compare multiple ML algorithms
*  Hyperparameter tuning
*  Add precision-recall analysis
*  Implement stronger authentication and authorization
*  Improve mobile responsiveness
*  Deploy the application to a cloud platform
*  Add transaction alerts
*  Explore anomaly-detection techniques for previously unseen fraud patterns

---

#  Project Goals

FraudShield was developed to demonstrate the practical application of:

* Full-stack web development
* Machine Learning
* Fraud detection
* Data preprocessing
* Imbalanced classification
* Model evaluation
* REST APIs
* Database management
* Git/GitHub project management

---

## 👩 Author

**Mahee Arya**

BCA — Artificial Intelligence & Data Science

GitHub: [@mahiiarya0089-wq](https://github.com/mahiiarya0089-wq)

---

##  Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.
