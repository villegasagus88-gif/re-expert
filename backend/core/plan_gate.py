"""
Plan-based access control.

`require_pro` is a FastAPI dependency that raises 403 with a structured
error body when the authenticated user does not have the 'pro' plan.

The structured detail lets the frontend show a targeted upgrade prompt
instead of a generic error.
"""
from core.auth import get_current_user
from fastapi import Depends, HTTPException, status
from models.user import User

_PRO_REQUIRED = {
    "message": "Esta función requiere el plan Pro.",
    "plan_required": "pro",
    "upgrade_url": "/pricing.html",
}


def ensure_pro(user: User) -> None:
    """Raise 403 (structured) if `user` is not on the Pro plan.

    Use this inline when only part of an endpoint is Pro-gated (e.g. /api/chat
    when context_type=='sol'). For whole-endpoint gating prefer the
    `require_pro` dependency below. Both share the same error body so the
    frontend upgrade prompt is consistent.
    """
    if user.plan != "pro":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_PRO_REQUIRED,
        )


def require_pro(user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency: gate an entire endpoint behind the Pro plan."""
    ensure_pro(user)
    return user
