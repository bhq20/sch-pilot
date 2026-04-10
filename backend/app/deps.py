"""Dependências compartilhadas das rotas: autenticação + tenant isolation."""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_token

bearer = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(self, user_id: str, tenant_id: str, role: str, email: str):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.role = role
        self.email = email


def get_tenant_db(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    """Retorna (db, current_user) com o RLS ativado pelo tenant do token."""
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token ausente")
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e))

    user = CurrentUser(
        user_id=payload["sub"],
        tenant_id=payload["tenant_id"],
        role=payload["role"],
        email=payload.get("email", ""),
    )

    db = SessionLocal()
    try:
        db.execute(text(f"SET LOCAL app.current_tenant = '{user.tenant_id}'"))
        yield db, user
    finally:
        db.close()


def require_role(*allowed: str):
    def _check(ctx=Depends(get_tenant_db)):
        db, user = ctx
        if user.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requer papel: {', '.join(allowed)}")
        return ctx
    return _check
