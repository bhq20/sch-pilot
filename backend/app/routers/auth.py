"""Login e /me."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.deps import get_tenant_db
from app.schemas import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    row = db.execute(
        text("""
            SELECT u.id, u.tenant_id, u.email, u.password_hash, u.full_name, u.role, u.active,
                   t.name AS tenant_name, t.segment
              FROM users u
              JOIN tenants t ON t.id = u.tenant_id
             WHERE lower(u.email) = lower(:email)
        """),
        {"email": payload.email},
    ).mappings().first()

    if not row or not row["active"] or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email ou senha inválidos")

    db.execute(text("UPDATE users SET last_login_at = NOW() WHERE id = :id"), {"id": row["id"]})
    db.commit()

    token = create_access_token(
        subject=str(row["id"]),
        tenant_id=str(row["tenant_id"]),
        role=row["role"],
        extra={"email": row["email"]},
    )
    user = UserOut(
        id=row["id"],
        email=row["email"],
        full_name=row["full_name"],
        role=row["role"],
        tenant_id=row["tenant_id"],
        tenant_name=row["tenant_name"],
        segment=row["segment"],
    )
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserOut)
def me(ctx=Depends(get_tenant_db)):
    db, user = ctx
    row = db.execute(
        text("""
            SELECT u.id, u.tenant_id, u.email, u.full_name, u.role,
                   t.name AS tenant_name, t.segment
              FROM users u
              JOIN tenants t ON t.id = u.tenant_id
             WHERE u.id = :id
        """),
        {"id": user.user_id},
    ).mappings().first()
    if not row:
        raise HTTPException(404, "Usuário não encontrado")
    return UserOut(**dict(row))
