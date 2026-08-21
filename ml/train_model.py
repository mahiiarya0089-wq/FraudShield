import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score
)

# -----------------------------
# 1. Load dataset
# -----------------------------

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "creditcard.csv"
)

df = pd.read_csv(DATA_PATH)

print("Dataset loaded successfully!")
print("Shape:", df.shape)

# -----------------------------
# 2. Separate features and target
# -----------------------------

X = df.drop("Class", axis=1)
y = df["Class"]

print("\nClass distribution:")
print(y.value_counts())

# -----------------------------
# 3. Train-test split
# -----------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# -----------------------------
# 4. Train Random Forest
# -----------------------------

print("\nTraining Random Forest model...")

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    class_weight="balanced",
    n_jobs=-1
)

model.fit(X_train, y_train)

print("Model training completed!")

# -----------------------------
# 5. Predictions
# -----------------------------

y_pred = model.predict(X_test)
y_probability = model.predict_proba(X_test)[:, 1]

# -----------------------------
# 6. Evaluation
# -----------------------------

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

roc_auc = roc_auc_score(y_test, y_probability)

print("\nROC-AUC Score:", round(roc_auc, 4))

# -----------------------------
# 7. Save model
# -----------------------------

MODEL_DIR = os.path.join(
    os.path.dirname(__file__),
    "saved_model"
)

os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "fraud_model.joblib"
)

joblib.dump(model, MODEL_PATH)

print("\nModel saved successfully!")
print("Location:", MODEL_PATH)