"""Tests del modelo pago-only (sin tier free): trial / pro / inactive + gate.

Verifican la lógica de acceso introducida en la migración 0017:
  - has_access(): pro siempre, trial mientras esté vigente, resto no.
  - require_access(): 403 estructurado para el paywall del frontend.
  - config/plans: no existe 'free'; trial y pro tienen acceso completo.

Pure: no importan `main`. Corre con pytest o como script.
"""
from datetime import UTC, datetime, timedelta

import pytest
from config.plans import PLAN_FEATURES, PLAN_LIMITS, has_feature, limits_for
from core.plan_gate import has_access, require_access
from fastapi import HTTPException


class _U:
    def __init__(self, plan, ends=None):
        self.plan = plan
        self.trial_ends_at = ends


def _future(days: int = 3):
    return datetime.now(UTC) + timedelta(days=days)


def _past(days: int = 1):
    return datetime.now(UTC) - timedelta(days=days)


# ── has_access ──

def test_pro_tiene_acceso():
    assert has_access(_U("pro")) is True


def test_trial_vigente_tiene_acceso():
    assert has_access(_U("trial", _future())) is True


def test_trial_vencido_sin_acceso():
    assert has_access(_U("trial", _past())) is False


def test_trial_sin_fecha_sin_acceso():
    assert has_access(_U("trial", None)) is False


def test_inactive_sin_acceso():
    assert has_access(_U("inactive")) is False


def test_free_legacy_sin_acceso():
    # 'free' ya no existe; si quedara alguno en la DB, no da acceso.
    assert has_access(_U("free")) is False


# ── require_access (dependency) ──

def test_require_access_pasa_pro():
    u = _U("pro")
    assert require_access(user=u) is u


def test_require_access_pasa_trial_vigente():
    u = _U("trial", _future())
    assert require_access(user=u) is u


def test_require_access_403_inactive():
    with pytest.raises(HTTPException) as e:
        require_access(user=_U("inactive"))
    assert e.value.status_code == 403
    assert e.value.detail["reason"] == "no_subscription"
    assert e.value.detail["upgrade_url"] == "/pricing.html"


def test_require_access_403_trial_vencido_marca_reason():
    with pytest.raises(HTTPException) as e:
        require_access(user=_U("trial", _past()))
    assert e.value.status_code == 403
    assert e.value.detail["reason"] == "trial_expired"


# ── plans: sin free ──

def test_no_existe_free_en_plans():
    assert "free" not in PLAN_FEATURES
    assert "free" not in PLAN_LIMITS


def test_trial_y_pro_tienen_features_completas():
    for feat in ("chat", "sol_assistant", "project_dashboard", "export", "data_ingest"):
        assert has_feature("trial", feat) is True
        assert has_feature("pro", feat) is True


def test_inactive_sin_features():
    assert has_feature("inactive", "chat") is False


def test_trial_limits_igual_pro():
    assert limits_for("trial") == limits_for("pro")
    assert limits_for("trial")["per_day"] == 200


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests pasaron.")


if __name__ == "__main__":
    _run_all()
