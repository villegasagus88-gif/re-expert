"""
Tests for plan-based feature gating.

Covers:
  - `require_pro` FastAPI dependency: 403 for free users, passthrough for pro
  - Structured 403 detail (message / plan_required / upgrade_url) — used by
    the frontend to render the targeted upgrade prompt
  - `has_feature(plan, feature)` matrix: free vs pro per documented feature
  - Integration: a route protected by `require_pro` returns 403 to free
    users and 200 to pro users via FastAPI dependency_overrides.
"""
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from config.plans import PLAN_FEATURES, has_feature
from core.auth import get_current_user
from core.plan_gate import require_pro
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from models.user import User


def _make_user(plan: str) -> MagicMock:
    u = MagicMock(spec=User)
    u.id = uuid4()
    u.email = f"{plan}@example.com"
    u.plan = plan
    return u


# ─────────────────────────────────────────────────── require_pro (unit) --

def test_require_pro_passes_through_pro_user():
    """A user on the pro plan must be returned unchanged."""
    pro = _make_user("pro")
    assert require_pro(user=pro) is pro


def test_require_pro_raises_403_for_free_user():
    """A user on the free plan must trigger a 403."""
    free = _make_user("free")
    with pytest.raises(HTTPException) as exc:
        require_pro(user=free)
    assert exc.value.status_code == 403


def test_require_pro_raises_403_for_unknown_plan():
    """Defensive: any non-'pro' value is treated as free (denied)."""
    other = _make_user("enterprise")  # not a real plan
    with pytest.raises(HTTPException) as exc:
        require_pro(user=other)
    assert exc.value.status_code == 403


def test_require_pro_403_detail_is_structured_for_frontend():
    """
    The 403 body must include `message`, `plan_required`, `upgrade_url`
    so the frontend can render the upgrade prompt without parsing strings.
    """
    free = _make_user("free")
    with pytest.raises(HTTPException) as exc:
        require_pro(user=free)
    detail = exc.value.detail
    assert isinstance(detail, dict)
    assert detail.get("plan_required") == "pro"
    assert detail.get("upgrade_url") == "/pricing.html"
    assert "Pro" in detail.get("message", "")


# ──────────────────────────────────────────────────────── has_feature --

@pytest.mark.parametrize(
    "feature",
    [
        "history_full",
        "sol_assistant",
        "project_dashboard",
        "indicators_cpi_spi",
        "data_ingest",
        "export",
        "priority_support",
    ],
)
def test_has_feature_pro_only_features_blocked_for_free(feature):
    assert has_feature("free", feature) is False
    assert has_feature("pro", feature) is True


@pytest.mark.parametrize("feature", ["chat", "knowledge_read"])
def test_has_feature_shared_features_open_to_both(feature):
    assert has_feature("free", feature) is True
    assert has_feature("pro", feature) is True


def test_has_feature_unknown_plan_falls_back_to_free():
    """Unknown plan must be treated as free — never accidentally elevated."""
    # Pro-only feature: must be denied for unknown plan.
    assert has_feature("enterprise", "export") is False
    # Open feature: still allowed (matches free behaviour).
    assert has_feature("enterprise", "chat") is True


def test_has_feature_unknown_feature_returns_false():
    """A feature not in the table must default to denied for any plan."""
    assert has_feature("free", "no_such_feature") is False
    assert has_feature("pro", "no_such_feature") is False


def test_plan_features_table_has_both_plans():
    """Sanity check: the source-of-truth table covers free & pro."""
    assert "free" in PLAN_FEATURES
    assert "pro" in PLAN_FEATURES
    # Both plans must declare the same set of features (no silent gaps).
    assert set(PLAN_FEATURES["free"].keys()) == set(PLAN_FEATURES["pro"].keys())


# ─────────────────────────────────────────────── integration via TestClient --

def _build_gated_app(current_user: MagicMock) -> FastAPI:
    """Tiny FastAPI app with one route protected by `require_pro`."""
    app = FastAPI()

    @app.get("/pro-only")
    def pro_only(user: User = Depends(require_pro)):
        return {"ok": True, "email": user.email}

    # Override the underlying auth dependency to inject our test user.
    app.dependency_overrides[get_current_user] = lambda: current_user
    return app


def test_pro_only_route_returns_403_for_free_user():
    free = _make_user("free")
    client = TestClient(_build_gated_app(free))
    r = client.get("/pro-only")
    assert r.status_code == 403
    body = r.json()
    assert body["detail"]["plan_required"] == "pro"
    assert body["detail"]["upgrade_url"] == "/pricing.html"


def test_pro_only_route_returns_200_for_pro_user():
    pro = _make_user("pro")
    client = TestClient(_build_gated_app(pro))
    r = client.get("/pro-only")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "email": "pro@example.com"}
