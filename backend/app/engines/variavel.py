"""
Engine de Custeio Variável (CVL — Custo/Volume/Lucro).

Calcula por centro produtivo:
    - Receita bruta e líquida
    - Custo variável
    - Margem de contribuição (R$) e (%)
    - Ponto de equilíbrio (em R$) usando o custo fixo consolidado do hospital
    - Alavancagem operacional

Entradas:
    revenues_by_cc   : dict[cc_id -> {gross, deductions, variable_cost, volume}]
    fixed_cost_total : Decimal — custo fixo total do hospital no período
    cc_meta          : dict[cc_id -> {code, name}]

Saída: estrutura análoga ao run_rkw com summary + by_cost_center.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


def _round(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def run_variavel(
    revenues_by_cc: dict[str, dict[str, Any]],
    fixed_cost_total: Decimal,
    cc_meta: dict[str, dict[str, Any]],
    period: date,
) -> dict[str, Any]:
    rows = []
    total_net = Decimal("0")
    total_var = Decimal("0")
    total_gross = Decimal("0")
    total_cm = Decimal("0")
    total_volume = 0

    for cc_id, rev in revenues_by_cc.items():
        meta = cc_meta.get(cc_id, {"code": "?", "name": "?"})
        gross = Decimal(str(rev.get("gross", 0)))
        deductions = Decimal(str(rev.get("deductions", 0)))
        var_cost = Decimal(str(rev.get("variable_cost", 0)))
        volume = int(rev.get("volume", 0))

        net = gross - deductions
        cm = net - var_cost
        cm_pct = (cm / net * 100) if net > 0 else Decimal("0")
        cm_unit = (cm / volume) if volume > 0 else Decimal("0")
        var_cost_unit = (var_cost / volume) if volume > 0 else Decimal("0")

        total_gross += gross
        total_net += net
        total_var += var_cost
        total_cm += cm
        total_volume += volume

        rows.append({
            "cc_id": cc_id,
            "cc_code": meta["code"],
            "cc_name": meta["name"],
            "gross_revenue": _round(gross),
            "deductions": _round(deductions),
            "net_revenue": _round(net),
            "variable_cost": _round(var_cost),
            "contribution_margin": _round(cm),
            "margin_pct": _round(cm_pct),
            "volume": volume,
            "cm_per_unit": _round(cm_unit),
            "variable_cost_per_unit": _round(var_cost_unit),
        })

    rows.sort(key=lambda r: -r["contribution_margin"])

    # Consolidado hospital
    overall_cm_pct = (total_cm / total_net * 100) if total_net > 0 else Decimal("0")
    operating_profit = total_cm - fixed_cost_total
    # Ponto de equilíbrio (R$ de receita líquida necessária para zerar o resultado)
    break_even_rev = (fixed_cost_total / (overall_cm_pct / 100)) if overall_cm_pct > 0 else Decimal("0")
    # Margem de segurança
    margin_of_safety = total_net - break_even_rev
    mos_pct = (margin_of_safety / total_net * 100) if total_net > 0 else Decimal("0")
    # Alavancagem operacional (GAO)
    gao = (total_cm / operating_profit) if operating_profit > 0 else Decimal("0")

    summary = {
        "period": period.isoformat(),
        "method": "VARIAVEL",
        "total_gross_revenue": _round(total_gross),
        "total_net_revenue": _round(total_net),
        "total_variable_cost": _round(total_var),
        "total_contribution_margin": _round(total_cm),
        "overall_margin_pct": _round(overall_cm_pct),
        "total_fixed_cost": _round(fixed_cost_total),
        "operating_profit": _round(operating_profit),
        "break_even_revenue": _round(break_even_rev),
        "margin_of_safety": _round(margin_of_safety),
        "margin_of_safety_pct": _round(mos_pct),
        "operating_leverage": _round(gao),
        "total_volume": total_volume,
    }
    return {"summary": summary, "by_cost_center": rows}
