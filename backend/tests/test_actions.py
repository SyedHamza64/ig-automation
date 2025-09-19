import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def login():
    r = client.post("/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]

def test_limits_and_follow_smoke():
    token = login()
    headers = {"Authorization": f"Bearer {token}"}

    # upsert limits (low for test)
    limits = {
        "follow": {"per_hour": 5, "per_day": 10, "warmup": True},
        "random_delay_ms": [1, 2],
    }
    r = client.put("/actions/limits/1", headers=headers, json={"limits_json": limits})
    assert r.status_code == 200, r.text

    # simulate follow
    r = client.post("/actions/follow", headers=headers, json={
        "account_id": 1, "profile_id": 1, "usernames": ["user_a", "user_b"]
    })
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["status"] in ("running", "success", "rate_limited", "error")
