# SCH Pilot — Sistema de Custeio Hospitalar (MVP)

> Versão enxuta do SCH focada em validar o produto com o primeiro cliente-piloto. Roda 100% em free tiers.

**Escopo do piloto:**
- Multi-tenant com RLS no Postgres
- Login email/senha + MFA opcional (JWT)
- Dois segmentos: Humana e Veterinária
- Plano de contas por upload Excel/CSV
- Centros de custo hierárquicos
- Lançamentos manuais ou importados
- Custeio **RKW/Absorção** + **Variável (CVL)**
- Dashboard executivo com 5 KPIs
- 3 relatórios PDF premium (executivo, centros de custo, variação orçamentária)
- Exportação Excel
- 3 papéis: Admin, Controller, Viewer

**Fora do escopo do piloto:** ABC, TDABC, DRG, Monte Carlo, EHR, agenda, TISS, imagem, laboratório, farmácia, IA. Tudo isso fica para as ondas seguintes.

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | Next.js 14 + TypeScript + Tailwind + Recharts |
| Backend | FastAPI (Python 3.11) + SQLAlchemy 2 + Pydantic v2 |
| Banco | PostgreSQL 16 (Supabase em produção, Docker local para dev) |
| Auth | JWT HS256 (futuro: Supabase Auth ou Firebase) |
| PDFs | ReportLab |
| Deploy | Cloud Run (backend) + Netlify (frontend) |

## Como rodar localmente

```bash
# 1. Clonar e entrar na pasta
cd sch-pilot

# 2. Copiar variáveis de ambiente
cp .env.example .env

# 3. Subir tudo com Docker
docker compose up -d

# 4. Acessar
#    Frontend: http://localhost:3000
#    Backend:  http://localhost:8000/docs
#    Login:    admin@demo.com / demo1234
```

## Estrutura

```
sch-pilot/
├── backend/            FastAPI + engines de custeio
│   └── app/
│       ├── main.py
│       ├── core/       config, database, security
│       ├── routers/    auth, tenants, cost_centers, lancamentos, costing, reports
│       ├── engines/    rkw.py, variavel.py
│       └── reports/    PDFs premium
├── frontend/           Next.js 14 dark mode
│   ├── app/            Rotas App Router
│   ├── components/     UI reutilizável
│   └── lib/            api client, auth, utils
├── database/           001_schema.sql · 002_seed.sql
├── scripts/            setup.sh, seed.py
└── docker-compose.yml  Orquestração local
```

## Próximos passos após o piloto

Ver `PLANO_LEAN_SCH_Piloto_Custo_Minimo.docx` na raiz do projeto.
