"""Smoke tests for the usage endpoint + cost calculation."""
from decimal import Decimal

from fastapi.testclient import TestClient
from main import app
from services.token_usage_service import calculate_cost_usd


def test_usage_endpoint_requires_auth():
    client = TestClient(app)
    response = client.get("/api/usage")
    assert response.status_code == 401


def test_usage_endpoint_rejects_post():
    client = TestClient(app)
    response = client.post("/api/usage")
    assert response.status_code == 405


def test_cost_calculation_sonnet():
    # 1M input + 1M output on Sonnet = $3 + $15 = $18
    cost = calculate_cost_usd("claude-sonnet-4-6-20250514", 1_000_000, 1_000_000)
    assert cost == Decimal("18.000000")


def test_cost_calculation_small_request():
    # 1000 input + 500 output on Sonnet = $0.003 + $0.0075 = $0.0105
    cost = calculate_cost_usd("claude-sonnet-4-6-20250514", 1000, 500)
    assert cost == Decimal("0.010500")


def test_cost_calculation_unknown_model_fallback():
    # Unknown model should fall back to default (Sonnet) pricing, not crash.
    cost = calculate_cost_usd("non-existent-model", 1000, 500)
    assert cost == Decimal("0.010500")
