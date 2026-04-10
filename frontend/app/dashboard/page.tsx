"use client";
import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { api, brl, pct } from "@/lib/api";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid,
} from "recharts";

type KpisResponse = {
  period: string;
  kpis: Record<string, number>;
  top_productive: { code: string; name: string; total_cost: number; fixed_cost: number; variable_cost: number }[];
  cost_trend: { period: string; cost: number }[];
};

export default function DashboardPage() {
  const [period, setPeriod] = useState("2026-03-01");
  const [data, setData] = useState<KpisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setErr(null);
    try {
      const res = await api<KpisResponse>(`/api/dashboard/kpis?period=${period}`);
      setData(res);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const k = data?.kpis;

  return (
    <Shell>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-bhq-primary">Dashboard Executivo</h1>
        <div className="flex gap-2">
          <input
            type="date"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="px-3 py-1 border border-bhq-light rounded-lg text-sm"
          />
          <button
            onClick={load}
            className="px-4 py-1 bg-bhq-primary text-white rounded-lg text-sm hover:bg-bhq-accent"
          >
            Atualizar
          </button>
        </div>
      </div>

      {err && <div className="mb-4 p-3 bg-red-50 text-bhq-danger rounded-lg text-sm">{err}</div>}
      {loading && <div className="text-bhq-dim">Carregando...</div>}

      {k && (
        <>
          <div className="grid grid-cols-4 gap-4 mb-6">
            <Card label="Receita Líquida" value={brl(k.net_revenue)} />
            <Card label="Custo Total" value={brl(k.total_cost)} />
            <Card label="Margem Contrib." value={brl(k.contribution_margin)} sub={pct(k.margin_pct)} />
            <Card label="Lucro Operacional" value={brl(k.operating_profit)} sub={pct(k.operating_margin_pct)} positive={k.operating_profit > 0} />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="bg-white p-5 rounded-xl border border-bhq-light">
              <h2 className="text-sm font-semibold text-bhq-dim mb-3">Top Centros Produtivos</h2>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={data?.top_productive}>
                  <XAxis dataKey="code" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v: number) => brl(v)} />
                  <Bar dataKey="total_cost" fill="#0B3D5C" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="bg-white p-5 rounded-xl border border-bhq-light">
              <h2 className="text-sm font-semibold text-bhq-dim mb-3">Tendência de Custo (6 meses)</h2>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={data?.cost_trend}>
                  <CartesianGrid stroke="#F2F6FA" />
                  <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v: number) => brl(v)} />
                  <Line type="monotone" dataKey="cost" stroke="#1F6491" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </Shell>
  );
}

function Card({ label, value, sub, positive }: { label: string; value: string; sub?: string; positive?: boolean }) {
  return (
    <div className="bg-white p-5 rounded-xl border border-bhq-light">
      <div className="text-xs text-bhq-dim uppercase tracking-wide">{label}</div>
      <div className="text-2xl font-bold text-bhq-primary mt-1">{value}</div>
      {sub && (
        <div className={`text-sm mt-1 ${positive === false ? "text-bhq-danger" : "text-bhq-success"}`}>
          {sub}
        </div>
      )}
    </div>
  );
}
