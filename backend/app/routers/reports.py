"""Geração e entrega dos PDFs premium do SCH Pilot."""
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import text

from app.deps import get_tenant_db
from app.engines.rkw import run_rkw
from app.engines.variavel import run_variavel
from app.reports.pdf_builder import (
    build_cost_center_report,
    build_executive_report,
    build_variance_report,
)
from app.routers.costing import (
    _load_costs_and_meta,
    _load_revenues,
    _load_rules,
)

router = APIRouter(prefix="/api/reports", tags=["relatórios"])


def _tenant_info(db, tenant_id: str) -> tuple[str, str]:
    row = db.execute(text("""
        SELECT name, segment FROM tenants WHERE id = :tid
    """), {"tid": tenant_id}).mappings().first()
    if not row:
        raise HTTPException(404, "Tenant não encontrado")
    return row["name"], row["segment"]


def _kpis_and_top(db, period: date) -> tuple[dict, list[dict]]:
    rev = db.execute(text("""
        SELECT COALESCE(SUM(gross_revenue), 0) AS gross,
               COALESCE(SUM(deductions), 0)    AS ded,
               COALESCE(SUM(variable_cost), 0) AS var,
               COALESCE(SUM(volume_units), 0)  AS vol
          FROM revenues WHERE period = :p
    """), {"p": period}).mappings().first()

    cost = db.execute(text("""
        SELECT COALESCE(SUM(total_cost), 0) AS total,
               COALESCE(SUM(fixed_cost), 0) AS fx,
               COALESCE(SUM(variable_cost), 0) AS vr
          FROM v_monthly_cost_center WHERE period = :p
    """), {"p": period}).mappings().first()

    gross = float(rev["gross"]); ded = float(rev["ded"])
    net = gross - ded
    var_cost = float(rev["var"])
    cm = net - var_cost
    cm_pct = (cm / net * 100) if net > 0 else 0.0
    fixed = float(cost["fx"])
    op = cm - fixed
    op_pct = (op / net * 100) if net > 0 else 0.0

    kpis = {
        "gross_revenue": gross, "net_revenue": net,
        "total_cost": float(cost["total"]), "fixed_cost": fixed,
        "variable_cost": var_cost, "contribution_margin": cm,
        "operating_profit": op, "margin_pct": cm_pct,
        "operating_margin_pct": op_pct, "volume_units": int(rev["vol"]),
    }

    top = db.execute(text("""
        SELECT cc_code, cc_name, total_cost, fixed_cost, variable_cost
          FROM v_monthly_cost_center
         WHERE period = :p AND cc_type = 'PRODUTIVO'
         ORDER BY total_cost DESC LIMIT 5
    """), {"p": period}).mappings().all()
    top_list = [{
        "code": r["cc_code"], "name": r["cc_name"],
        "total_cost": float(r["total_cost"]),
        "fixed_cost": float(r["fixed_cost"]),
        "variable_cost": float(r["variable_cost"]),
    } for r in top]

    return kpis, top_list


@router.get("/executive")
def report_executive(period: date = Query(...), ctx=Depends(get_tenant_db)):
    db, user = ctx
    tenant_name, segment = _tenant_info(db, user.tenant_id)
    kpis, top = _kpis_and_top(db, period)
    pdf = build_executive_report(tenant_name, segment, period, kpis, top)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="executivo_{period}.pdf"'},
    )


@router.get("/cost-centers")
def report_cost_centers(period: date = Query(...), ctx=Depends(get_tenant_db)):
    db, user = ctx
    tenant_name, segment = _tenant_info(db, user.tenant_id)
    costs, meta = _load_costs_and_meta(db, period)
    rules = _load_rules(db)
    rkw_result = run_rkw(costs, meta, rules, period)
    pdf = build_cost_center_report(tenant_name, segment, period, rkw_result)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="centros_custo_{period}.pdf"'},
    )


@router.get("/variance")
def report_variance(period: date = Query(...), ctx=Depends(get_tenant_db)):
    db, user = ctx
    tenant_name, segment = _tenant_info(db, user.tenant_id)
    _, meta = _load_costs_and_meta(db, period)
    revs = _load_revenues(db, period)
    fixed = db.execute(text("""
        SELECT COALESCE(SUM(fixed_cost), 0) AS fx
          FROM v_monthly_cost_center WHERE period = :p
    """), {"p": period}).scalar() or 0
    variavel_result = run_variavel(revs, Decimal(str(fixed)), meta, period)
    pdf = build_variance_report(tenant_name, segment, period, variavel_result)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="margem_{period}.pdf"'},
    )
