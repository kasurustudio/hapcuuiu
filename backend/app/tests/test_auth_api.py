def test_register_creates_user(client):
    resp = client.post(
        "/api/v1/auth/register", json={"email": "trader@example.com", "password": "supersecret123"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "trader@example.com"
    assert body["disclaimer_accepted_at"] is None
    assert "password" not in body
    assert "password_hash" not in body


def test_register_rejects_duplicate_email(client):
    payload = {"email": "dupe@example.com", "password": "supersecret123"}
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
    assert second.json()["detail"]["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


def test_login_returns_access_and_refresh_tokens(client):
    client.post("/api/v1/auth/register", json={"email": "login@example.com", "password": "supersecret123"})

    resp = client.post(
        "/api/v1/auth/login", json={"email": "login@example.com", "password": "supersecret123"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


def test_login_rejects_wrong_password(client):
    client.post("/api/v1/auth/register", json={"email": "wrongpw@example.com", "password": "supersecret123"})

    resp = client.post(
        "/api/v1/auth/login", json={"email": "wrongpw@example.com", "password": "totallywrong"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"]["error"]["code"] == "INVALID_CREDENTIALS"


def test_me_requires_bearer_token(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(client):
    client.post("/api/v1/auth/register", json={"email": "me@example.com", "password": "supersecret123"})
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": "me@example.com", "password": "supersecret123"}
    )
    access_token = login_resp.json()["access_token"]

    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


def test_refresh_issues_new_access_token(client):
    client.post("/api/v1/auth/register", json={"email": "refresh@example.com", "password": "supersecret123"})
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": "refresh@example.com", "password": "supersecret123"}
    )
    refresh_token = login_resp.json()["refresh_token"]

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_refresh_rejects_access_token_used_as_refresh(client):
    client.post("/api/v1/auth/register", json={"email": "badtype@example.com", "password": "supersecret123"})
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": "badtype@example.com", "password": "supersecret123"}
    )
    access_token = login_resp.json()["access_token"]

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401


def test_accept_disclaimer_sets_timestamp(client):
    client.post("/api/v1/auth/register", json={"email": "disclaimer@example.com", "password": "supersecret123"})
    login_resp = client.post(
        "/api/v1/auth/login", json={"email": "disclaimer@example.com", "password": "supersecret123"}
    )
    access_token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    before = client.get("/api/v1/auth/me", headers=headers).json()
    assert before["disclaimer_accepted_at"] is None

    resp = client.post("/api/v1/auth/accept-disclaimer", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["disclaimer_accepted_at"] is not None
