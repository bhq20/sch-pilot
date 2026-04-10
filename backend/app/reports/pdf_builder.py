"""
Gerador de PDFs premium do SCH Pilot.
Três relatórios: Executivo, Centros de Custo, Variação Orçamentária.
Usa ReportLab com layout coerente em azul profundo (#0B3D5C).
"""
from __future__ import annotations

from datetime import date
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
    TableStyle, PageBreak,
)

PRIMARY = colors.HexColor("#0B3D5C")
ACCENT = colors.HexColor("#1F6491")
LIGHT = colors.HexColor("#F2F6FA")
DIM = colors.HexColor("#6B7C8C")
SUCCESS = colors.HexColor("#059669")
DANGER = colors.HexColor("#DC2626")


def _brl(v: float | int) -> str:
    s = f"{float(v):,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(v: float) -> str:
    return f"{float(v):,.2f}%".replace(".", ",")


def _pt_month(d: date) -> str:
    months = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
              "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    return f"{months[d.month - 1]} de {d.year}"


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("Title1", fontName="Helvetica-Bold", fontSize=22, textColor=PRIMARY, spaceAfter=14, leading=26))
    ss.add(ParagraphStyle("Sub1", fontName="Helvetica", fontSize=12, textColor=ACCENT, spaceBefore=4, spaceAfter=22, leading=15))
    ss.add(ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=14, textColor=PRIMARY, spaceBefore=14, spaceAfter=6))
    ss.add(ParagraphStyle("Body1", fontName="Helvetica", fontSize=10, textColor=colors.black, leading=14, alignment=4))
    ss.add(ParagraphStyle("Small", fontName="Helvetica", fontSize=8, textColor=DIM))
    ss.add(ParagraphStyle("KPI", fontName="Helvetica-Bold", fontSize=18, textColor=PRIMARY, alignment=1))
    ss.add(ParagraphStyle("KPILabel", fontName="Helvetica", fontSize=8, textColor=DIM, alignment=1))
    return ss


def _header_footer(tenant_name: str, report_title: str):
    def draw(canvas, doc):
        canvas.saveState()
        # Barra superior institucional BHQ
        canvas.setFillColor(PRIMARY)
        canvas.rect(0, A4[1] - 16 * mm, A4[0], 16 * mm, fill=1, stroke=0)

        # "Logo" BHQ — marca institucional à esquerda (badge + wordmark)
        badge_x = 20 * mm
        badge_y = A4[1] - 12 * mm
        canvas.setFillColor(colors.white)
        canvas.roundRect(badge_x, badge_y, 14 * mm, 8 * mm, 1.5, fill=1, stroke=0)
        canvas.setFillColor(PRIMARY)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawCentredString(badge_x + 7 * mm, badge_y + 2.3 * mm, "BHQ")

        # Wordmark ao lado da badge
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(badge_x + 17 * mm, A4[1] - 8 * mm, "BHQ Consultoria")
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#B8D3E6"))
        canvas.drawString(badge_x + 17 * mm, A4[1] - 11.5 * mm, "SCH · Sistema de Custeio Hospitalar")

        # Divisor vertical sutil + nome do hospital ao lado
        sep_x = badge_x + 62 * mm
        canvas.setStrokeColor(colors.HexColor("#5A8CAE"))
        canvas.setLineWidth(0.6)
        canvas.line(sep_x, A4[1] - 13 * mm, sep_x, A4[1] - 6 * mm)

        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(sep_x + 4 * mm, A4[1] - 8 * mm, tenant_name)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#B8D3E6"))
        canvas.drawString(sep_x + 4 * mm, A4[1] - 11.5 * mm, report_title)

        # Footer
        canvas.setStrokeColor(LIGHT)
        canvas.setLineWidth(0.5)
        canvas.line(20 * mm, 15 * mm, A4[0] - 20 * mm, 15 * mm)
        canvas.setFillColor(DIM)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(20 * mm, 10 * mm, f"BHQ Consultoria · {report_title}")
        canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, f"Página {doc.page}")
        canvas.restoreState()
    return draw


def _build_doc(title: str, tenant_name: str) -> tuple[BaseDocTemplate, BytesIO]:
    buf = BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=24 * mm, bottomMargin=20 * mm,
        title=title, author="BHQ Consultoria",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    tmpl = PageTemplate(id="main", frames=[frame], onPage=_header_footer(tenant_name, title))
    doc.addPageTemplates([tmpl])
    return doc, buf


def _kpi_card(label: str, value: str, color=PRIMARY) -> Table:
    ss = _styles()
    t = Table(
        [[Paragraph(value, ParagraphStyle("v", fontSize=14, fontName="Helvetica-Bold", textColor=color, alignment=1))],
         [Paragraph(label, ss["KPILabel"])]],
        colWidths=[42 * mm],
    )
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, LIGHT),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


# ============================================================
# Relatório 1 — Executivo Mensal
# ============================================================
def build_executive_report(
    tenant_name: str,
    segment: str,
    period: date,
    kpis: dict[str, Any],
    top_productive: list[dict[str, Any]],
) -> bytes:
    doc, buf = _build_doc("Relatório Executivo Mensal", tenant_name)
    ss = _styles()
    story: list[Any] = []

    story.append(Paragraph("RELATÓRIO EXECUTIVO MENSAL", ss["Title1"]))
    story.append(Paragraph(f"{tenant_name} · {_pt_month(period)}", ss["Sub1"]))

    # KPI row
    kpi_row = [
        _kpi_card("Receita Líquida", _brl(kpis["net_revenue"])),
        _kpi_card("Custo Total", _brl(kpis["total_cost"]), DANGER),
        _kpi_card("Margem Contrib.", _brl(kpis["contribution_margin"]), SUCCESS),
        _kpi_card("Margem %", _pct(kpis["margin_pct"]), SUCCESS if kpis["margin_pct"] >= 0 else DANGER),
    ]
    kpi_table = Table([kpi_row], colWidths=[42 * mm] * 4)
    kpi_table.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]))
    story.append(kpi_table)
    story.append(Spacer(1, 12))

    # Resumo narrativo
    story.append(Paragraph("Resumo do Período", ss["H2"]))
    narrative = (
        f"No mês de {_pt_month(period).lower()}, {tenant_name} registrou receita líquida de "
        f"<b>{_brl(kpis['net_revenue'])}</b> e custo total de <b>{_brl(kpis['total_cost'])}</b>, "
        f"resultando em margem de contribuição de <b>{_brl(kpis['contribution_margin'])}</b> "
        f"({_pct(kpis['margin_pct'])}). O lucro operacional do período foi de "
        f"<b>{_brl(kpis['operating_profit'])}</b>, equivalente a {_pct(kpis['operating_margin_pct'])} "
        f"sobre a receita líquida. A operação abrange {kpis['cost_center_count']} centros de custo ativos "
        f"e atendeu um volume de {kpis['volume_units']:,} unidades (atendimentos/internações) no período."
        .replace(",", ".")
    )
    story.append(Paragraph(narrative, ss["Body1"]))
    story.append(Spacer(1, 8))

    # Composição de custos
    story.append(Paragraph("Composição dos Custos", ss["H2"]))
    comp_data = [
        ["Natureza", "Valor (R$)", "% do Total"],
        ["Custos Fixos", _brl(kpis["fixed_cost"]), _pct(kpis["fixed_cost"] / max(kpis["total_cost"], 1) * 100)],
        ["Custos Variáveis", _brl(kpis["variable_cost"]), _pct(kpis["variable_cost"] / max(kpis["total_cost"], 1) * 100)],
        ["TOTAL", _brl(kpis["total_cost"]), "100,00%"],
    ]
    comp = Table(comp_data, colWidths=[70 * mm, 50 * mm, 30 * mm])
    comp.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(comp)
    story.append(Spacer(1, 14))

    # Top produtivos
    story.append(Paragraph("Top 5 Centros Produtivos por Custo", ss["H2"]))
    top_data = [["Cód.", "Centro de Custo", "Custo Total", "Fixo", "Variável"]]
    for r in top_productive:
        top_data.append([r["code"], r["name"], _brl(r["total_cost"]), _brl(r["fixed_cost"]), _brl(r["variable_cost"])])
    top_tbl = Table(top_data, colWidths=[18 * mm, 62 * mm, 30 * mm, 30 * mm, 30 * mm])
    top_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(top_tbl)
    story.append(Spacer(1, 20))

    # Rodapé interpretativo
    story.append(Paragraph("Interpretação & Recomendações", ss["H2"]))
    interp = (
        "A análise do período indica que a operação mantém margem de contribuição saudável. "
        "Recomenda-se atenção aos centros com maior participação no custo total, buscando "
        "oportunidades de otimização em materiais e medicamentos, que costumam ter maior "
        "elasticidade de redução sem comprometer a qualidade assistencial. O próximo ciclo "
        "deve incluir análise de variação orçamentária para identificar desvios sistemáticos "
        "e oportunidades estruturais de economia."
    )
    story.append(Paragraph(interp, ss["Body1"]))

    doc.build(story)
    return buf.getvalue()


# ============================================================
# Relatório 2 — Centros de Custo (detalhado por RKW)
# ============================================================
def build_cost_center_report(
    tenant_name: str,
    segment: str,
    period: date,
    rkw_result: dict[str, Any],
) -> bytes:
    doc, buf = _build_doc("Relatório de Centros de Custo — RKW", tenant_name)
    ss = _styles()
    story: list[Any] = []

    story.append(Paragraph("CENTROS DE CUSTO — MÉTODO RKW/ABSORÇÃO", ss["Title1"]))
    story.append(Paragraph(f"{tenant_name} · {_pt_month(period)}", ss["Sub1"]))

    s = rkw_result["summary"]
    story.append(Paragraph(
        f"Este relatório apresenta o resultado do custeio por absorção total (RKW) do período. "
        f"Todos os custos dos centros auxiliares e administrativos foram rateados aos centros "
        f"produtivos segundo as regras cadastradas. O custo total original de <b>{_brl(s['total_cost_original'])}</b> "
        f"foi integralmente absorvido pelos <b>{s['productive_count']}</b> centros produtivos do hospital, "
        f"com diferença de reconciliação de <b>{_brl(s['reconciliation_diff'])}</b>.",
        ss["Body1"]
    ))
    story.append(Spacer(1, 10))

    # Tabela por tipo
    story.append(Paragraph("Resultado por Centro de Custo", ss["H2"]))
    headers = ["Cód.", "Centro de Custo", "Tipo", "Próprio", "Recebido", "Enviado", "Total"]
    data = [headers]
    for r in rkw_result["by_cost_center"]:
        data.append([
            r["cc_code"], r["cc_name"], r["cc_type"][:3],
            _brl(r["own_cost"]), _brl(r["received_apportionment"]),
            _brl(r["sent_apportionment"]), _brl(r["total_cost"]),
        ])
    tbl = Table(data, colWidths=[16 * mm, 44 * mm, 12 * mm, 28 * mm, 28 * mm, 24 * mm, 28 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 14))

    # Foco nos produtivos
    productive = [r for r in rkw_result["by_cost_center"] if r["cc_type"] == "PRODUTIVO"]
    if productive:
        story.append(Paragraph("Detalhamento dos Centros Produtivos", ss["H2"]))
        det_headers = ["Centro", "Pessoal", "Material", "Medicamento", "Total"]
        det_data = [det_headers]
        for r in productive:
            bd = r["breakdown"]
            det_data.append([
                r["cc_name"], _brl(bd.get("personnel", 0)), _brl(bd.get("material", 0)),
                _brl(bd.get("drug", 0)), _brl(r["total_cost"]),
            ])
        det = Table(det_data, colWidths=[52 * mm, 28 * mm, 28 * mm, 32 * mm, 32 * mm])
        det.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(det)

    doc.build(story)
    return buf.getvalue()


# ============================================================
# Relatório 3 — Variação Orçamentária / Margem
# ============================================================
def build_variance_report(
    tenant_name: str,
    segment: str,
    period: date,
    variavel_result: dict[str, Any],
) -> bytes:
    doc, buf = _build_doc("Relatório de Margem de Contribuição", tenant_name)
    ss = _styles()
    story: list[Any] = []

    story.append(Paragraph("ANÁLISE DE MARGEM E PONTO DE EQUILÍBRIO", ss["Title1"]))
    story.append(Paragraph(f"{tenant_name} · {_pt_month(period)} · Método Custeio Variável", ss["Sub1"]))

    s = variavel_result["summary"]

    # KPIs CVL
    row1 = [
        _kpi_card("Receita Líquida", _brl(s["total_net_revenue"])),
        _kpi_card("Custo Variável", _brl(s["total_variable_cost"]), DANGER),
        _kpi_card("MC Total", _brl(s["total_contribution_margin"]), SUCCESS),
        _kpi_card("MC %", _pct(s["overall_margin_pct"]), SUCCESS),
    ]
    story.append(Table([row1], colWidths=[42 * mm] * 4))
    story.append(Spacer(1, 10))

    row2 = [
        _kpi_card("Custo Fixo", _brl(s["total_fixed_cost"])),
        _kpi_card("Lucro Operacional", _brl(s["operating_profit"]),
                  SUCCESS if s["operating_profit"] >= 0 else DANGER),
        _kpi_card("Ponto Equilíbrio", _brl(s["break_even_revenue"])),
        _kpi_card("Margem Segurança", _pct(s["margin_of_safety_pct"]), SUCCESS),
    ]
    story.append(Table([row2], colWidths=[42 * mm] * 4))
    story.append(Spacer(1, 14))

    # Interpretação
    story.append(Paragraph("Leitura Gerencial", ss["H2"]))
    interp = (
        f"A operação apresenta margem de contribuição global de <b>{_pct(s['overall_margin_pct'])}</b>, "
        f"o que significa que a cada real de receita líquida, <b>{_brl(s['overall_margin_pct'] / 100)}</b> "
        f"ficam disponíveis para cobrir custos fixos e gerar lucro. O ponto de equilíbrio contábil do "
        f"hospital no período é de <b>{_brl(s['break_even_revenue'])}</b> — receita abaixo deste patamar "
        f"produziria prejuízo operacional. A margem de segurança atual é de <b>{_pct(s['margin_of_safety_pct'])}</b>, "
        f"indicando quanto a receita pode cair antes de entrar em zona de prejuízo. A alavancagem "
        f"operacional (GAO) é de <b>{s['operating_leverage']:.2f}</b>, evidenciando que cada 1% de variação "
        f"na receita produz <b>{s['operating_leverage']:.2f}%</b> de variação no lucro operacional."
    )
    story.append(Paragraph(interp, ss["Body1"]))
    story.append(Spacer(1, 12))

    # Tabela por centro produtivo
    story.append(Paragraph("Margem por Centro Produtivo", ss["H2"]))
    headers = ["Cód.", "Centro", "Rec. Líquida", "Custo Var.", "MC (R$)", "MC %", "Volume"]
    data = [headers]
    for r in variavel_result["by_cost_center"]:
        data.append([
            r["cc_code"], r["cc_name"],
            _brl(r["net_revenue"]), _brl(r["variable_cost"]),
            _brl(r["contribution_margin"]), _pct(r["margin_pct"]),
            f"{r['volume']:,}".replace(",", "."),
        ])
    tbl = Table(data, colWidths=[15 * mm, 42 * mm, 28 * mm, 26 * mm, 28 * mm, 18 * mm, 18 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)

    doc.build(story)
    return buf.getvalue()
