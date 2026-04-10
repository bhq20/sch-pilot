"""KPIs agregados para o dashboard executivo."""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text

from app.deps import get_tenant_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/kpis")
def get_kpis(period: date = Query(...), ctx=Depends(get_tenant_db)):
    db, _ = ctx

    # Receita líquida + custo variável + margem
    rev_row = db.execute(text("""
        SELECT
            COALESCE(SUM(gross_revenue), 0) AS gross,
            COALESCE(SUM(deductions), 0)    AS deductions,
            COALESCE(SUM(variable_cost), 0) AS var_cost,
            COALESCE(SUM(volume_units), 0)  AS volume
          FROM revenues WHERE period = :p
    """), {"p": period}).mappings().first()

    # Custo total
    cost_row = db.execute(text("""
        SELECT
            COALESCE(SUM(total_cost), 0)    AS total_cost,
            COALESCE(SUM(fixed_cost), 0)    AS fixed,
            COALESCE(SUM(variable_cost), 0) AS var,
            COUNT(DISTINCT cost_center_id)  AS cc_count
          FROM v_monthly_cost_center WHERE period = :p
    """), {"p": period}).mappings().first()

    gross = float(rev_row["gross"])
    deductions = float(rev_row["deductions"])
    net = gross - deductions
    total_cost = float(cost_row["total_cost"])
    fixed = float(cost_row["fixed"])
    var_cost = float(rev_row["var_cost"])
    contribution_margin = net - var_cost
    operating_profit = contribution_margin - fixed
    margin_pct = (contribution_margin / net * 100) if net > 0 else 0
    op_margin_pct = (operating_profit / net * 100) if net > 0 else 0

    # Top 5 centros produtivos por custo
    top_cc = db.execute(text("""
        SELECT cc_code, cc_name, total_cost, fixed_cost, variable_cost
          FROM v_monthly_cost_center
         WHERE period = :p AND cc_type = 'PRODUTIVO'
         ORDER BY total_cost DESC LIMIT 5
    """), {"p": period}).mappings().all()

    # Série mensal (últimos 6 meses)
    serie = db.execute(text("""
        SELECT period, SUM(total_cost) AS cost
          FROM v_monthly_cost_center
         WHERE period >= (:p::date - INTERVAL '5 months')
           AND period <= :p
         GROUP BY period ORDER BY period
    """), {"p": period}).mappings().all()

    return {
        "period": period.isoformat(),
        "kpis": {
            "gross_revenue": round(gross, 2),
            "net_revenue": round(net, 2),
            "total_cost": round(total_cost, 2),
            "fixed_cost": round(fixed, 2),
            "variable_cost": round(var_cost, 2),
            "contribution_margin": round(contribution_margin, 2),
            "operating_profit": round(operating_profit, 2),
            "margin_pct": round(margin_pct, 2),
            "operating_margin_pct": round(op_margin_pct, 2),
            "volume_units": int(rev_row["volume"]),
            "cost_center_count": int(cost_row["cc_count"] or 0),
        },
        "top_productive": [
            {
                "code": r["cc_code"], "name": r["cc_name"],
                "total_cost": float(r["total_cost"]),
                "fixed_cost": float(r["fixed_cost"]),
                "variable_cost": float(r["variable_cost"]),
            } for r in top_cc
        ],
        "cost_trend": [
            {"period": r["period"].isoformat(), "cost": float(r["cost"])}
            for r in serie
        ],
    }
