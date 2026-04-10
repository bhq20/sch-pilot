"use client";
import { useState } from "react";
import Shell from "@/components/Shell";
import { api, brl } from "@/lib/api";

type RunOut = {
  id: string;
  period: string;
  method: string;
  status: string;
  summary: any;
  detail: { by_cost_center: any[] };
};

export default function CostingPage() {
  const [period, setPeriod] = useState("2026-03-01");
  const [method, setMethod] = useState<"RKW" | "VARIAVEL">("RKW");
  const [run, setRun] = useState<RunOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function execute() {
    setLoading(true);
    setErr(null);
    try {
      const res = await api<RunOut>("/api/costing/run", {
        method: "POST",
        body: JSON.stringify({ period, method }),
      });
      setRun(res);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Shell>
      <h1 className="text-2xl font-bold text-bhq-primary mb-6">Executar Custeio</h1>

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
        <div>
          <label className="block text-xs text-bhq-dim mb-1">Método</label>
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value as any)}
            className="px-3 py-2 border border-bhq-light rounded-lg text-sm"
          >
            <option value="RKW">RKW / Absorção</option>
            <option value="VARIAVEL">Custeio Variável (CVL)</option>
          </select>
        </div>
        <button
          onClick={execute}
          disabled={loading}
          className="px-5 py-2 bg-bhq-primary text-white rounded-lg text-sm hover:bg-bhq-accent disabled:opacity-50"
        >
          {loading ? "Executando..." : "Executar"}
        </button>
      </div>

      {err && <div className="mb-4 p-3 bg-red-50 text-bhq-danger rounded-lg text-sm">{err}</div>}

      {run && (
        <div className="bg-white p-5 rounded-xl border border-bhq-light">
          <h2 className="text-lg font-semibold text-bhq-primary mb-3">
            {run.method} — {run.period}
          </h2>
          <pre className="text-xs bg-bhq-light p-3 rounded-lg overflow-auto max-h-96">
            {JSON.stringify(run.summary, null, 2)}
          </pre>
          {run.method === "RKW" && run.detail.by_cost_center && (
            <table className="w-full text-sm mt-4">
              <thead>
                <tr className="border-b border-bhq-light text-left text-bhq-dim">
                  <th className="py-2">Código</th>
                  <th>Centro</th>
                  <th>Tipo</th>
                  <th className="text-right">Próprio</th>
                  <th className="text-right">Recebido</th>
                  <th className="text-right">Enviado</th>
                  <th className="text-right">Total</th>
                </tr>
              </thead>
              <tbody>
                {run.detail.by_cost_center.map((cc: any) => (
                  <tr key={cc.cc_id} className="border-b border-bhq-light/50">
                    <td className="py-1">{cc.cc_code}</td>
                    <td>{cc.cc_name}</td>
                    <td className="text-xs text-bhq-dim">{cc.cc_type}</td>
                    <td className="text-right">{brl(cc.own_cost)}</td>
                    <td className="text-right">{brl(cc.received_apportionment)}</td>
                    <td className="text-right">{brl(cc.sent_apportionment)}</td>
                    <td className="text-right font-semibold">{brl(cc.total_cost)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </Shell>
  );
}
