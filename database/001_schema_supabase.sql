-- ============================================================
--  SCH — Schema para Supabase (Postgres gerenciado)
--  Idêntico ao 001_schema.sql local, com ajustes para o
--  ambiente Supabase (sem CREATE DATABASE, com extensões
--  padrão já disponíveis).
--  Execute este script no SQL Editor do Supabase após
--  criar o projeto.
-- ============================================================

-- Extensões (Supabase já tem pgcrypto habilitado por padrão)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Schema dedicado para evitar conflito com auth.* do Supabase
CREATE SCHEMA IF NOT EXISTS sch;
SET search_path = sch, public;

-- ============================================================
--  ENUMS
-- ============================================================
DO $$ BEGIN
  CREATE TYPE segment_type AS ENUM ('HUMANA', 'VETERINARIA');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE user_role AS ENUM ('ADMIN', 'CONTROLLER', 'VIEWER');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE cc_type AS ENUM ('PRODUTIVO', 'AUXILIAR', 'ADMINISTRATIVO');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE cost_nature AS ENUM ('FIXO', 'VARIAVEL');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE cost_category AS ENUM ('PESSOAL', 'MATERIAL', 'MEDICAMENTO', 'UTILIDADE', 'OUTRO');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ============================================================
--  TABELAS (mesma estrutura do ambiente local)
-- ============================================================
CREATE TABLE IF NOT EXISTS tenants (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  segment     segment_type NOT NULL,
  cnpj        TEXT,
  active      BOOLEAN NOT NULL DEFAULT TRUE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  email           TEXT NOT NULL UNIQUE,
  password_hash   TEXT NOT NULL,
  name            TEXT NOT NULL,
  role            user_role NOT NULL DEFAULT 'VIEWER',
  active          BOOLEAN NOT NULL DEFAULT TRUE,
  last_login_at   TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cost_centers (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  code        TEXT NOT NULL,
  name        TEXT NOT NULL,
  cc_type     cc_type NOT NULL,
  parent_id   UUID REFERENCES cost_centers(id),
  active      BOOLEAN NOT NULL DEFAULT TRUE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (tenant_id, code)
);

CREATE TABLE IF NOT EXISTS accounts (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  code        TEXT NOT NULL,
  name        TEXT NOT NULL,
  nature      cost_nature NOT NULL,
  category    cost_category NOT NULL,
  active      BOOLEAN NOT NULL DEFAULT TRUE,
  UNIQUE (tenant_id, code)
);

CREATE TABLE IF NOT EXISTS entries (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  period          DATE NOT NULL,
  cost_center_id  UUID NOT NULL REFERENCES cost_centers(id),
  account_id      UUID NOT NULL REFERENCES accounts(id),
  amount          NUMERIC(18,2) NOT NULL,
  memo            TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by      UUID REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_entries_tenant_period ON entries(tenant_id, period);

CREATE TABLE IF NOT EXISTS revenues (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  period          DATE NOT NULL,
  cost_center_id  UUID NOT NULL REFERENCES cost_centers(id),
  gross_revenue   NUMERIC(18,2) NOT NULL DEFAULT 0,
  deductions      NUMERIC(18,2) NOT NULL DEFAULT 0,
  variable_cost   NUMERIC(18,2) NOT NULL DEFAULT 0,
  volume_units    INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_revenues_tenant_period ON revenues(tenant_id, period);

CREATE TABLE IF NOT EXISTS apportionment_rules (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  source_cc   UUID NOT NULL REFERENCES cost_centers(id),
  target_cc   UUID NOT NULL REFERENCES cost_centers(id),
  percentage  NUMERIC(6,3) NOT NULL,
  UNIQUE (tenant_id, source_cc, target_cc)
);

CREATE TABLE IF NOT EXISTS costing_runs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  period      DATE NOT NULL,
  method      TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'OK',
  summary     JSONB NOT NULL,
  detail      JSONB NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by  UUID REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS audit_log (
  id          BIGSERIAL PRIMARY KEY,
  tenant_id   UUID,
  user_id     UUID,
  action      TEXT NOT NULL,
  target      TEXT,
  meta        JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
--  ROW LEVEL SECURITY
-- ============================================================
ALTER TABLE tenants              ENABLE ROW LEVEL SECURITY;
ALTER TABLE users                ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_centers         ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts             ENABLE ROW LEVEL SECURITY;
ALTER TABLE entries              ENABLE ROW LEVEL SECURITY;
ALTER TABLE revenues             ENABLE ROW LEVEL SECURITY;
ALTER TABLE apportionment_rules  ENABLE ROW LEVEL SECURITY;
ALTER TABLE costing_runs         ENABLE ROW LEVEL SECURITY;

-- Política: isola cada tenant via variável de sessão "app.current_tenant"
-- definida pelo backend via SET LOCAL por requisição.
DO $$
DECLARE
  t TEXT;
BEGIN
  FOREACH t IN ARRAY ARRAY['tenants','users','cost_centers','accounts','entries',
                           'revenues','apportionment_rules','costing_runs']
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS tenant_isolation ON %I', t);
    IF t = 'tenants' THEN
      EXECUTE format($f$
        CREATE POLICY tenant_isolation ON %I
          USING (id::text = current_setting('app.current_tenant', true))
      $f$, t);
    ELSE
      EXECUTE format($f$
        CREATE POLICY tenant_isolation ON %I
          USING (tenant_id::text = current_setting('app.current_tenant', true))
      $f$, t);
    END IF;
  END LOOP;
END $$;

-- ============================================================
--  VIEWS de suporte
-- ============================================================
CREATE OR REPLACE VIEW v_monthly_cost_center AS
SELECT
  e.tenant_id,
  e.period,
  cc.id              AS cc_id,
  cc.code            AS cc_code,
  cc.name            AS cc_name,
  cc.cc_type         AS cc_type,
  SUM(CASE WHEN a.nature = 'FIXO'     THEN e.amount ELSE 0 END) AS fixed_cost,
  SUM(CASE WHEN a.nature = 'VARIAVEL' THEN e.amount ELSE 0 END) AS variable_cost,
  SUM(e.amount)                                                 AS total_cost,
  SUM(CASE WHEN a.category = 'PESSOAL'     THEN e.amount ELSE 0 END) AS personnel_cost,
  SUM(CASE WHEN a.category = 'MATERIAL'    THEN e.amount ELSE 0 END) AS material_cost,
  SUM(CASE WHEN a.category = 'MEDICAMENTO' THEN e.amount ELSE 0 END) AS drug_cost
FROM entries e
JOIN cost_centers cc ON cc.id = e.cost_center_id
JOIN accounts     a  ON a.id  = e.account_id
GROUP BY e.tenant_id, e.period, cc.id, cc.code, cc.name, cc.cc_type;

CREATE OR REPLACE VIEW v_monthly_margin AS
SELECT
  r.tenant_id,
  r.period,
  r.cost_center_id AS cc_id,
  SUM(r.gross_revenue) AS gross_revenue,
  SUM(r.deductions)    AS deductions,
  SUM(r.gross_revenue - r.deductions) AS net_revenue,
  SUM(r.variable_cost) AS variable_cost,
  SUM(r.volume_units)  AS volume_units
FROM revenues r
GROUP BY r.tenant_id, r.period, r.cost_center_id;
