"""
Engine RKW / Absorção.

Método: todos os custos (fixos + variáveis) dos centros AUXILIARES e
ADMINISTRATIVOS são rateados para os centros PRODUTIVOS segundo as regras
de apportionment_rules. O custo total dos produtivos é então a soma dos
custos próprios + custos rateados recebidos.

Entradas esperadas (buscadas no banco pela camada de serviço):
    costs_by_cc      : dict[cc_id -> {"fixed": float, "variable": float, "total": float}]
    cc_meta          : dict[cc_id -> {"code": str, "name": str, "cc_type": str}]
    rules            : list[{"source": cc_id, "target": cc_id, "percentage": float}]

Saída:
    {
      "summary": {
         "total_cost_original": X,
         "total_cost_apportioned": X,    # deve bater com original
         "productive_count": N,
         "auxiliary_count": N,
         "period": "YYYY-MM-DD"
      },
      "by_cost_center": [
         {
           "cc_id", "cc_code", "cc_name", "cc_type",
           "own_cost", "received_apportionment", "total_cost",
           "cost_breakdown": {...}
         }, ...
      ]
    }
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass
class CCRow:
    cc_id: str
    code: str
    name: str
    cc_type: str
    own_cost: Decimal = Decimal("0")
    received: Decimal = Decimal("0")
    sent: Decimal = Decimal("0")
    breakdown: dict[str, Decimal] = field(default_factory=dict)

    @property
    def total(self) -> Decimal:
        return self.own_cost + self.received - self.sent


def run_rkw(
    costs_by_cc: dict[str, dict[str, Any]],
    cc_meta: dict[str, dict[str, Any]],
    rules: list[dict[str, Any]],
    period: date,
) -> dict[str, Any]:
    """Executa o rateio de absorção total."""
    rows: dict[str, CCRow] = {}
    for cc_id, meta in cc_meta.items():
        c = costs_by_cc.get(cc_id, {})
        rows[cc_id] = CCRow(
            cc_id=cc_id,
            code=meta["code"],
            name=meta["name"],
            cc_type=meta["cc_type"],
            own_cost=Decimal(str(c.get("total", 0))),
            breakdown={
                "fixed": Decimal(str(c.get("fixed", 0))),
                "variable": Decimal(str(c.get("variable", 0))),
                "personnel": Decimal(str(c.get("personnel", 0))),
                "material": Decimal(str(c.get("material", 0))),
                "drug": Decimal(str(c.get("drug", 0))),
            },
        )

    total_original = sum((r.own_cost for r in rows.values()), Decimal("0"))

    # Índice de regras por centro origem
    by_source: dict[str, list[dict[str, Any]]] = {}
    for rule in rules:
        by_source.setdefault(str(rule["source"]), []).append(rule)

    # Ordem: primeiro ADMINISTRATIVO, depois AUXILIAR (método sequencial)
    order = []
    order += [cid for cid, r in rows.items() if r.cc_type == "ADMINISTRATIVO"]
    order += [cid for cid, r in rows.items() if r.cc_type == "AUXILIAR"]

    for source_id in order:
        source = rows[source_id]
        pool = source.own_cost + source.received
        if pool <= 0:
            continue
        rules_for_source = by_source.get(source_id, [])
        total_pct = sum(Decimal(str(r["percentage"])) for r in rules_for_source)
        if total_pct <= 0:
            continue
        for rule in rules_for_source:
            target_id = str(rule["target"])
            if target_id not in rows:
                continue
            share = pool * Decimal(str(rule["percentage"])) / total_pct
            rows[target_id].received += share
            source.sent += share

    # Filtra produtivos
    productive = [r for r in rows.values() if r.cc_type == "PRODUTIVO"]
    productive.sort(key=lambda r: r.code)
    total_productive = sum((r.total for r in productive), Decimal("0"))

    summary = {
        "period": period.isoformat(),
        "method": "RKW",
        "total_cost_original": float(total_original),
        "total_cost_productive": float(total_productive),
        "reconciliation_diff": float(total_original - total_productive),
        "productive_count": len(productive),
        "auxiliary_count": sum(1 for r in rows.values() if r.cc_type == "AUXILIAR"),
        "administrative_count": sum(1 for r in rows.values() if r.cc_type == "ADMINISTRATIVO"),
    }

    by_cost_center = []
    for r in rows.values():
        by_cost_center.append({
            "cc_id": r.cc_id,
            "cc_code": r.code,
            "cc_name": r.name,
            "cc_type": r.cc_type,
            "own_cost": float(r.own_cost),
            "received_apportionment": float(r.received),
            "sent_apportionment": float(r.sent),
            "total_cost": float(r.total),
            "breakdown": {k: float(v) for k, v in r.breakdown.items()},
        })
    by_cost_center.sort(key=lambda x: (x["cc_type"] != "PRODUTIVO", x["cc_code"]))

    return {"summary": summary, "by_cost_center": by_cost_center}
