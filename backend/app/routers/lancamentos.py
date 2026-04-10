"""Lançamentos (entries) e receitas (revenues)."""
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text

from app.deps import get_tenant_db, require_role
from app.schemas import EntryIn, EntryOut, RevenueIn, RevenueOut

router = APIRouter(prefix="/api", tags=["lançamentos"])


# ------------------------ Entries ----------------------------
@router.get("/entries", response_model=list[EntryOut])
def list_entries(period: date | None = Query(None), ctx=Depends(get_tenant_db)):
    db, _ = ctx
    sql = "SELECT id, cost_center_id, account_id, period, amount, source, notes FROM entries"
    params = {}
    if period:
        sql += " WHERE period = :p"
        params["p"] = period
    sql += " ORDER BY period DESC, cost_center_id LIMIT 500"
    rows = db.execute(text(sql), params).mappings().all()
    return [EntryOut(**dict(r)) for r in rows]


@router.post("/entries", response_model=EntryOut, status_code=201)
def create_entry(payload: EntryIn, ctx=Depends(require_role("ADMIN", "CONTROLLER"))):
    db, user = ctx
    row = db.execute(text("""
        INSERT INTO entries (tenant_id, cost_center_id, account_id, period, amount, notes, created_by, source)
        VALUES (:tid, :cc, :acc, :p, :amt, :notes, :uid, 'MANUAL')
        RETURNING id, cost_center_id, account_id, period, amount, source, notes
    """), {
        "tid": user.tenant_id, "cc": payload.cost_center_id, "acc": payload.account_id,
        "p": payload.period, "amt": payload.amount, "notes": payload.notes, "uid": user.user_id,
    }).mappings().first()
    db.commit()
    return EntryOut(**dict(row))


@router.delete("/entries/{entry_id}", status_code=204)
def delete_entry(entry_id: UUID, ctx=Depends(require_role("ADMIN", "CONTROLLER"))):
    db, _ = ctx
    db.execute(text("DELETE FROM entries WHERE id = :id"), {"id": entry_id})
    db.commit()


# ------------------------ Revenues ---------------------------
@router.get("/revenues", response_model=list[RevenueOut])
def list_revenues(period: date | None = None, ctx=Depends(get_tenant_db)):
    db, _ = ctx
    sql = "SELECT id, cost_center_id, period, gross_revenue, deductions, variable_cost, volume_units FROM revenues"
    params = {}
    if period:
        sql += " WHERE period = :p"
        params["p"] = period
    sql += " ORDER BY period DESC"
    rows = db.execute(text(sql), params).mappings().all()
    return [RevenueOut(
        id=r["id"],
        cost_center_id=r["cost_center_id"],
        period=r["period"],
        gross_revenue=r["gross_revenue"],
        deductions=r["deductions"],
        variable_cost=r["variable_cost"],
        volume_units=r["volume_units"],
    ) for r in rows]


@router.post("/revenues", response_model=RevenueOut, status_code=201)
def create_revenue(payload: RevenueIn, ctx=Depends(require_role("ADMIN", "CONTROLLER"))):
    db, user = ctx
    row = db.execute(text("""
        INSERT INTO revenues (tenant_id, cost_center_id, period, gross_revenue, deductions, variable_cost, volume_units)
        VALUES (:tid, :cc, :p, :gross, :ded, :var, :vol)
        RETURNING id, cost_center_id, period, gross_revenue, deductions, variable_cost, volume_units
    """), {
        "tid": user.tenant_id, "cc": payload.cost_center_id, "p": payload.period,
        "gross": payload.gross_revenue, "ded": payload.deductions,
        "var": payload.variable_cost, "vol": payload.volume_units,
    }).mappings().first()
    db.commit()
    return RevenueOut(
        id=row["id"],
        cost_center_id=row["cost_center_id"],
        period=row["period"],
        gross_revenue=row["gross_revenue"],
        deductions=row["deductions"],
        variable_cost=row["variable_cost"],
        volume_units=row["volume_units"],
    )
