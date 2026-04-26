"""Smoke + validation tests for POST /api/data/ingest."""
from decimal import Decimal

import pytest
from api.schemas.ingest import (
    BudgetIngest,
    IngestRequest,
    MaterialIngest,
    MilestoneIngest,
    PaymentIngest,
)
from fastapi.testclient import TestClient
from main import app
from pydantic import TypeAdapter, ValidationError

_ingest_adapter: TypeAdapter = TypeAdapter(IngestRequest)


# -------------------------------------------------------------------- HTTP --

def test_ingest_endpoint_requires_auth():
    client = TestClient(app)
    response = client.post("/api/data/ingest", json={"type": "payment", "amount": 100})
    assert response.status_code == 401


def test_ingest_endpoint_rejects_get():
    client = TestClient(app)
    response = client.get("/api/data/ingest")
    assert response.status_code == 405


# ------------------------------------------------------------ schema parsing --

def test_payment_payload_parses_with_minimal_fields():
    parsed = _ingest_adapter.validate_python(
        {"type": "payment", "amount": 500000}
    )
    assert isinstance(parsed, PaymentIngest)
    assert parsed.amount == Decimal("500000")
    assert parsed.currency == "ARS"
    assert parsed.provider is None


def test_payment_payload_parses_with_all_fields():
    parsed = _ingest_adapter.validate_python(
        {
            "type": "payment",
            "amount": "12500.50",
            "currency": "USD",
            "provider": "Albañil Juan",
            "concept": "anticipo",
            "paid_at": "2026-04-20",
            "notes": "transferencia",
        }
    )
    assert isinstance(parsed, PaymentIngest)
    assert parsed.amount == Decimal("12500.50")
    assert parsed.currency == "USD"
    assert parsed.provider == "Albañil Juan"


def test_milestone_payload_defaults_status_to_planned():
    parsed = _ingest_adapter.validate_python(
        {"type": "milestone", "name": "Hormigonado losa P1"}
    )
    assert isinstance(parsed, MilestoneIngest)
    assert parsed.status == "planned"


def test_milestone_invalid_status_rejected():
    with pytest.raises(ValidationError):
        _ingest_adapter.validate_python(
            {"type": "milestone", "name": "x", "status": "invalid_state"}
        )


def test_material_payload_parses_ok():
    parsed = _ingest_adapter.validate_python(
        {
            "type": "material",
            "name": "Cemento Loma Negra",
            "unit": "bolsa",
            "unit_price": "12500",
            "supplier": "Easy",
        }
    )
    assert isinstance(parsed, MaterialIngest)
    assert parsed.unit == "bolsa"
    assert parsed.unit_price == Decimal("12500")


def test_material_negative_price_rejected():
    with pytest.raises(ValidationError):
        _ingest_adapter.validate_python(
            {
                "type": "material",
                "name": "x",
                "unit": "ud",
                "unit_price": -1,
            }
        )


def test_budget_payload_parses_ok():
    parsed = _ingest_adapter.validate_python(
        {
            "type": "budget",
            "category": "Albañilería",
            "amount": 8500000,
            "kind": "extra",
        }
    )
    assert isinstance(parsed, BudgetIngest)
    assert parsed.kind == "extra"


def test_budget_invalid_kind_rejected():
    with pytest.raises(ValidationError):
        _ingest_adapter.validate_python(
            {
                "type": "budget",
                "category": "x",
                "amount": 1,
                "kind": "no_existe",
            }
        )


def test_unknown_type_rejected():
    with pytest.raises(ValidationError):
        _ingest_adapter.validate_python({"type": "weather", "amount": 1})


def test_missing_type_rejected():
    with pytest.raises(ValidationError):
        _ingest_adapter.validate_python({"amount": 100})


def test_payment_amount_must_be_positive():
    with pytest.raises(ValidationError):
        _ingest_adapter.validate_python({"type": "payment", "amount": 0})
