"""Execução dos motores de custeio."""
import json
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from app.deps import get_tenant_db, require_role
from app.engines.rkw import run_rkw
from app.engines.variavel import run_variavel
from app.schemas import CostingRequest, CostingRunOut

router = APIRouter(prefix="/api/costing", tags=["custeio"])


def _load_costs_and_meta(db, period: date):
    rows = db.execute(text("""
        SELECT cc.id::text AS cc_id, cc.code, cc.name, cc.cc_type,
               COALESCE(v.fixed_cost, 0)    AS fixed,
               COALESCE(v.variable_cost, 0) AS variable,
               COALESCE(v.total_cost, 0)    AS total,
               COALESCE(v.personnel_cost, 0) AS personnel,
               COALESCE(v.material_cost, 0)  AS material,
               COALESCE(v.drug_cost, 0)      AS drug
          FROM cost_centers cc
          LEFT JOIN v_monthly_cost_center v
                 ON v.cost_center_id = cc.id AND v.period = :p
         WHERE cc.active = true
    """), {"p": period}).mappings().all()
    costs = {}
    meta = {}
    for r in rows:
        cid = r["cc_id"]
        costs[cid] = {
            "fixed": float(r["fixed"]), "variable": float(r["variable"]),
            "total": float(r["total"]), "personnel": float(r["personnel"]),
            "material": float(r["material"]), "drug": float(r["drug"]),
        }
        meta[cid] = {"code": r["code"], "name": r["name"], "cc_type": r["cc_type"]}
    return costs, meta


def _load_rules(db):
    rows = db.execute(text("""
        SELECT source_cc_id::text AS source, target_cc_id::text AS target, percentage
          FROM apportionment_rules
    """)).mappings().all()
    return [dict(r) for r in rows]


def _load_revenues(db, period: date):
    rows = db.execute(text("""
        SELECT cost_center_id::text AS cc_id, gross_revenue, deductions, variable_cost, volume_units
          FROM revenues WHERE period = :p
    """), {"p": period}).mappings().all()
    return {r["cc_id"]: {
        "gross": float(r["gross_revenue"]), "deductions": float(r["deductions"]),
        "variable_cost": float(r["variable_cost"]), "volume": int(r["volume_units"]),
    } for r in rows}


def _persist_run(db, tenant_id: str, user_id: str, period: date, method: str, result: dict):
    row = db.execute(text("""
        INSERT INTO costing_runs (tenant_id, period, method, status, summary, detail, created_by)
        VALUES (:tid, :p, :m, 'DONE', :s, :d, :u)
        RETURNING id, period, method, status, summary, detail, created_at
    """), {
        "tid": tenant_id, "p": period, "m": method,
        "s": json.dumps(result["summary"]),
        "d": json.dumps(result["by_cost_center"]),
        "u": user_id,
    }).mappings().first()
    db.commit()
    return row


@router.post("/run", response_model=CostingRunOut)
def run_costing(payload: CostingRequest, ctx=Depends(require_role("ADMIN", "CONTROLLER"))):
    db, user = ctx

    if payload.method == "RKW":
        costs, meta = _load_costs_and_meta(db, payload.period)
        rules = _load_rules(db)
        result = run_rkw(costs, meta, rules, payload.period)

    elif payload.method == "VARIAVEL":
        _, meta = _load_costs_and_meta(db, payload.period)
        revs = _load_revenues(db, payload.period)
        fixed = db.execute(text("""
            SELECT COALESCE(SUM(fixed_cost), 0) AS fx
              FROM v_monthly_cost_center WHERE period = :p
        """), {"p": payload.period}).scalar() or 0
        result = run_variavel(revs, Decimal(str(fixed)), meta, payload.period)

    else:
        raise HTTPException(400, "Método inválido")

    row = _persist_run(db, user.tenant_id, user.user_id, payload.period, payload.method, result)
    return CostingRunOut(
        id=row["id"], period=row["period"], method=row["method"],
        status=row["status"],
        summary=row["summary"] if isinstance(row["summary"], dict) else json.loads(row["summary"]),
        detail={"by_cost_center": row["detail"] if isinstance(row["detail"], list) else json.loads(row["detail"])},
        created_at=row["created_at"],
    )


@router.get("/runs", response_model=list[CostingRunOut])
def list_runs(ctx=Depends(get_tenant_db)):
    db, _ = ctx
    rows = db.execute(text("""
        SELECT id, period, method, status, summary, detail, created_at
          FROM costing_runs
         ORDER BY created_at DESC LIMIT 50
    """)).mappings().all()
    out = []
    for r in rows:
        summary = r["summary"] if isinstance(r["summary"], dict) else json.loads(r["summary"])
        detail = r["detail"] if isinstance(r["detail"], list) else json.loads(r["detail"])
        out.append(CostingRunOut(
            id=r["id"], period=r["period"], method=r["method"], status=r["status"],
            summary=summary, detail={"by_cost_center": detail}, created_at=r["created_at"],
        ))
    return out
