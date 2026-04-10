"""CRUD de centros de custo e contas."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from app.deps import get_tenant_db, require_role
from app.schemas import (
    CostCenterIn, CostCenterOut,
    AccountIn, AccountOut,
)

router = APIRouter(prefix="/api", tags=["cadastros"])


# ------------------------ Cost Centers ------------------------
@router.get("/cost-centers", response_model=list[CostCenterOut])
def list_cost_centers(ctx=Depends(get_tenant_db)):
    db, _ = ctx
    rows = db.execute(text("""
        SELECT id, code, name, cc_type, parent_id, active
          FROM cost_centers
         WHERE active = true
         ORDER BY cc_type, code
    """)).mappings().all()
    return [CostCenterOut(**dict(r)) for r in rows]


@router.post("/cost-centers", response_model=CostCenterOut, status_code=201)
def create_cost_center(
    payload: CostCenterIn,
    ctx=Depends(require_role("ADMIN", "CONTROLLER")),
):
    db, user = ctx
    row = db.execute(text("""
        INSERT INTO cost_centers (tenant_id, code, name, cc_type, parent_id)
        VALUES (:tid, :code, :name, :type, :parent)
        RETURNING id, code, name, cc_type, parent_id, active
    """), {
        "tid": user.tenant_id, "code": payload.code, "name": payload.name,
        "type": payload.cc_type.value, "parent": payload.parent_id,
    }).mappings().first()
    db.commit()
    return CostCenterOut(**dict(row))


@router.delete("/cost-centers/{cc_id}", status_code=204)
def delete_cost_center(cc_id: UUID, ctx=Depends(require_role("ADMIN"))):
    db, _ = ctx
    db.execute(text("UPDATE cost_centers SET active=false WHERE id=:id"), {"id": cc_id})
    db.commit()


# --------------------------- Accounts -------------------------
@router.get("/accounts", response_model=list[AccountOut])
def list_accounts(ctx=Depends(get_tenant_db)):
    db, _ = ctx
    rows = db.execute(text("""
        SELECT id, code, name, category, nature, active
          FROM accounts WHERE active = true ORDER BY code
    """)).mappings().all()
    return [AccountOut(**dict(r)) for r in rows]


@router.post("/accounts", response_model=AccountOut, status_code=201)
def create_account(payload: AccountIn, ctx=Depends(require_role("ADMIN", "CONTROLLER"))):
    db, user = ctx
    row = db.execute(text("""
        INSERT INTO accounts (tenant_id, code, name, category, nature)
        VALUES (:tid, :code, :name, :cat, :nat)
        RETURNING id, code, name, category, nature, active
    """), {
        "tid": user.tenant_id, "code": payload.code, "name": payload.name,
        "cat": payload.category.value, "nat": payload.nature.value,
    }).mappings().first()
    db.commit()
    return AccountOut(**dict(row))
