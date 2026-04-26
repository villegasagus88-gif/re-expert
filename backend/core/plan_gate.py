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


def require_pro(user: User = Depends(get_current_user)) -> User:
    if user.plan != "pro":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_PRO_REQUIRED,
        )
    return user
