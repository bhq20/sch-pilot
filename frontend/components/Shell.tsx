"use client";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { clearToken, getToken } from "@/lib/api";
import { useEffect } from "react";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/costing", label: "Custeio" },
  { href: "/reports", label: "Relatórios" },
];

export default function Shell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!getToken()) router.push("/");
  }, [router]);

  function logout() {
    clearToken();
    router.push("/");
  }

  return (
    <div className="min-h-screen flex">
      <aside className="w-60 bg-bhq-primary text-white p-5 flex flex-col">
        <div className="text-2xl font-bold mb-1">SCH</div>
        <div className="text-xs text-bhq-light/70 mb-8">Piloto BHQ</div>
        <nav className="space-y-1 flex-1">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`block px-3 py-2 rounded-lg text-sm transition ${
                pathname === item.href
                  ? "bg-bhq-accent text-white"
                  : "text-bhq-light/80 hover:bg-bhq-accent/50"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <button
          onClick={logout}
          className="text-xs text-bhq-light/60 hover:text-white mt-4"
        >
          Sair
        </button>
      </aside>
      <main className="flex-1 p-8 overflow-y-auto">{children}</main>
    </div>
  );
}
