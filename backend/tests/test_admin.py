"""Tests del gate de administrador (gestión del knowledge base).

Cubre is_admin() / require_admin(): cierra el agujero de escritura/borrado del
KB por cualquier usuario autenticado — solo emails en ADMIN_EMAILS pasan.
"""
import pytest
from fastapi import HTTPException


def _user(email):
    u = type("U", (), {})()
    u.email = email
    return u


def test_is_admin_true_for_listed(monkeypatch):
    from config import settings as s
    monkeypatch.setattr(s.settings, "ADMIN_EMAILS", "mati@re.app, agus@re.app")
    from core.auth import is_admin
    assert is_admin(_user("mati@re.app")) is True
    assert is_admin(_user("MATI@RE.APP")) is True  # case-insensitive


def test_is_admin_false_for_unlisted(monkeypatch):
    from config import settings as s
    monkeypatch.setattr(s.settings, "ADMIN_EMAILS", "mati@re.app")
    from core.auth import is_admin
    assert is_admin(_user("otro@x.com")) is False


def test_is_admin_false_when_empty(monkeypatch):
    from config import settings as s
    monkeypatch.setattr(s.settings, "ADMIN_EMAILS", "")
    from core.auth import is_admin
    assert is_admin(_user("mati@re.app")) is False  # vacío = nadie es admin


def test_require_admin_403_for_non_admin(monkeypatch):
    from config import settings as s
    monkeypatch.setattr(s.settings, "ADMIN_EMAILS", "mati@re.app")
    from core.auth import require_admin
    with pytest.raises(HTTPException) as e:
        require_admin(user=_user("otro@x.com"))
    assert e.value.status_code == 403


def test_require_admin_passes_admin(monkeypatch):
    from config import settings as s
    monkeypatch.setattr(s.settings, "ADMIN_EMAILS", "mati@re.app")
    from core.auth import require_admin
    u = _user("mati@re.app")
    assert require_admin(user=u) is u


def test_admin_bypasses_paywall(monkeypatch):
    # Los fundadores/operadores no quedan paywalled de su propia app: un admin
    # tiene acceso aunque su plan sea "inactive" o el trial haya vencido.
    from config import settings as s
    monkeypatch.setattr(s.settings, "ADMIN_EMAILS", "mati@re.app")
    from core.plan_gate import has_access
    u = _user("mati@re.app")
    u.plan = "inactive"
    u.trial_ends_at = None
    assert has_access(u) is True


def test_non_admin_inactive_has_no_access(monkeypatch):
    from config import settings as s
    monkeypatch.setattr(s.settings, "ADMIN_EMAILS", "mati@re.app")
    from core.plan_gate import has_access
    u = _user("otro@x.com")
    u.plan = "inactive"
    u.trial_ends_at = None
    assert has_access(u) is False


def _run_all():
    import inspect
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    class _MP:
        def setattr(self, obj, name, val): setattr(obj, name, val)
    for fn in fns:
        fn(_MP()) if "monkeypatch" in inspect.signature(fn).parameters else fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests pasaron.")


if __name__ == "__main__":
    _run_all()
