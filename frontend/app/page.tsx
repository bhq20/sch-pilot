"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { API_URL, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@demo.com");
  const [password, setPassword] = useState("demo1234");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) throw new Error("Credenciais inválidas");
      const data = await res.json();
      setToken(data.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8 border border-bhq-light">
        <div className="mb-8 text-center">
          <div className="text-3xl font-bold text-bhq-primary">SCH</div>
          <div className="text-sm text-bhq-dim">Sistema de Custeio Hospitalar</div>
          <div className="mt-1 text-xs text-bhq-dim">BHQ Consultoria · Piloto</div>
        </div>
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">E-mail</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-bhq-light rounded-lg focus:outline-none focus:border-bhq-accent"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Senha</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-bhq-light rounded-lg focus:outline-none focus:border-bhq-accent"
              required
            />
          </div>
          {error && <div className="text-sm text-bhq-danger">{error}</div>}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 bg-bhq-primary text-white rounded-lg font-medium hover:bg-bhq-accent transition disabled:opacity-50"
          >
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>
      </div>
    </main>
  );
}
