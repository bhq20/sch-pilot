"use client";
import { useState } from "react";
import Shell from "@/components/Shell";
import { API_URL, getToken } from "@/lib/api";

const REPORTS = [
  { key: "executive", label: "Relatório Executivo", desc: "KPIs, margens e top centros produtivos" },
  { key: "cost-centers", label: "Centros de Custo (RKW)", desc: "Rateio sequencial por absorção" },
  { key: "variance", label: "Margem de Contribuição", desc: "CVL, ponto de equilíbrio e GAO" },
];

export default function ReportsPage() {
  const [period, setPeriod] = useState("2026-03-01");
  const [loading, setLoading] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function download(kind: string) {
    setLoading(kind);
    setErr(null);
    try {
      const res = await fetch(`${API_URL}/api/reports/${kind}?period=${period}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!res.ok) throw new Error(`Erro ${res.status}`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      window.open(url, "_blank");
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(null);
    }
  }

  return (
    <Shell>
      <h1 className="text-2xl font-bold text-bhq-primary mb-6">Relatórios</h1>

      <div className="bg-white p-5 rounded-xl border border-bhq-light mb-6 flex gap-4 items-end">
        <div>
          <label className="block text-xs text-bhq-dim mb-1">Período</label>
          <input
            type="date"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="px-3 py-2 border border-bhq-light rounded-lg text-sm"
          />
        </div>
      </div>

      {err && <div className="mb-4 p-3 bg-red-50 text-bhq-danger rounded-lg text-sm">{err}</div>}

      <div className="grid grid-cols-3 gap-4">
        {REPORTS.map((r) => (
          <div key={r.key} className="bg-white p-5 rounded-xl border border-bhq-light">
            <h3 className="font-semibold text-bhq-primary">{r.label}</h3>
            <p className="text-xs text-bhq-dim mt-1 mb-4">{r.desc}</p>
            <button
              onClick={() => download(r.key)}
              disabled={loading === r.key}
              className="w-full px-3 py-2 bg-bhq-primary text-white rounded-lg text-sm hover:bg-bhq-accent disabled:opacity-50"
            >
              {loading === r.key ? "Gerando..." : "Baixar PDF"}
            </button>
          </div>
        ))}
      </div>
    </Shell>
  );
}
