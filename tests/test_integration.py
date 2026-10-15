
import os
import time

import requests


BASE_URL = os.getenv("APP_URL", "http://localhost:8080")


def test_health_checks_postgres_and_redis():
    response = None

    for _ in range(30):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=3)
            break
        except requests.RequestException:
            time.sleep(2)

    assert response is not None, "App did not become available"
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["postgres"] is True
    assert data["redis"] is True
