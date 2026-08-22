import importlib
import os


def load_test_app(tmp_path, monkeypatch):
    monkeypatch.setenv("FRAUDSHIELD_DB_PATH", str(tmp_path / "test_fraudshield.sqlite"))
    import app as fraud_app

    fraud_app = importlib.reload(fraud_app)
    fraud_app.app.config.update(TESTING=True, SECRET_KEY="test-secret")
    fraud_app.reset_database_for_tests()
    return fraud_app.app.test_client(), fraud_app


def register_and_login(client, username="mahee", email="mahee@example.com", password="secret123"):
    register_response = client.post(
        "/api/register",
        json={"username": username, "email": email, "password": password},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/login",
        json={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    return login_response.get_json()["data"]["user"]


def test_register_login_and_duplicate_prevention(tmp_path, monkeypatch):
    client, _ = load_test_app(tmp_path, monkeypatch)

    user = register_and_login(client)
    assert user["username"] == "mahee"
    assert "password" not in user

    duplicate = client.post(
        "/api/register",
        json={"username": "mahee", "email": "mahee@example.com", "password": "secret123"},
    )
    assert duplicate.status_code == 409


def test_unauthorized_dashboard_api_access(tmp_path, monkeypatch):
    client, _ = load_test_app(tmp_path, monkeypatch)

    response = client.get("/api/stats")
    assert response.status_code == 401
    assert response.get_json()["success"] is False


def test_deposit_updates_balance_and_history(tmp_path, monkeypatch):
    client, _ = load_test_app(tmp_path, monkeypatch)
    register_and_login(client)

    deposit = client.post("/api/deposit", json={"amount": 5000, "description": "Test refill"})
    assert deposit.status_code == 201
    assert deposit.get_json()["data"]["balance"] == 105000

    history = client.get("/api/transactions").get_json()["data"]["transactions"]
    assert history[0]["type"] == "deposit"
    assert history[0]["status"] == "completed"


def test_normal_transaction_deducts_balance(tmp_path, monkeypatch):
    client, _ = load_test_app(tmp_path, monkeypatch)
    register_and_login(client)

    response = client.post(
        "/api/transaction",
        json={"receiver": "Book Store", "amount": 1200, "description": "Books"},
    )
    body = response.get_json()["data"]

    assert response.status_code == 201
    assert body["status"] == "completed"
    assert body["balance"] == 98800
    assert body["fraud_analysis"]["risk_level"] == "LOW"


def test_insufficient_balance_is_rejected(tmp_path, monkeypatch):
    client, _ = load_test_app(tmp_path, monkeypatch)
    register_and_login(client)

    response = client.post("/api/transaction", json={"receiver": "Car Dealer", "amount": 200000})

    assert response.status_code == 400
    assert "Insufficient balance" in response.get_json()["message"]


def test_high_value_transaction_generates_fraud_score(tmp_path, monkeypatch):
    client, _ = load_test_app(tmp_path, monkeypatch)
    register_and_login(client)

    response = client.post("/api/transaction", json={"receiver": "Jewellery Store", "amount": 90000})
    analysis = response.get_json()["data"]["fraud_analysis"]

    assert response.status_code == 201
    assert analysis["score"] >= 50
    assert analysis["risk_level"] in {"MEDIUM", "HIGH"}


def test_transaction_retrieval_contains_required_fields(tmp_path, monkeypatch):
    client, _ = load_test_app(tmp_path, monkeypatch)
    register_and_login(client)
    client.post("/api/deposit", json={"amount": 1000})
    client.post("/api/transaction", json={"receiver": "Cafe", "amount": 250})

    response = client.get("/api/transactions")
    transactions = response.get_json()["data"]["transactions"]

    assert response.status_code == 200
    assert len(transactions) == 2
    assert {"transaction_id", "type", "amount", "risk_score", "risk_level", "status"} <= set(transactions[0])
