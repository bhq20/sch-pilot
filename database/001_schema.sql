-- ================================================================
-- SCH PILOT — Schema inicial
-- Multi-tenant com Row Level Security
-- ================================================================

-- Extensões
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Enums
CREATE TYPE segment_type   AS ENUM ('HUMANA', 'VETERINARIA');
CREATE TYPE user_role      AS ENUM ('ADMIN', 'CONTROLLER', 'VIEWER');
CREATE TYPE cc_type        AS ENUM ('PRODUTIVO', 'AUXILIAR', 'ADMINISTRATIVO');
CREATE TYPE cost_nature    AS ENUM ('FIXO', 'VARIAVEL', 'SEMI_VARIAVEL');
CREATE TYPE cost_category  AS ENUM ('PESSOAL', 'MATERIAL', 'MEDICAMENTO', 'SERVICO', 'INFRA', 'DEPRECIACAO', 'OUTROS');

-- ================================================================
-- TENANTS (uma linha por hospital/clínica)
-- ================================================================
CREATE TABLE tenants (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug            VARCHAR(50) UNIQUE NOT NULL,
    name            VARCHAR(200) NOT NULL,
    segment         segment_type NOT NULL,
    cnpj            VARCHAR(20),
    active          BOOLEAN DEFAULT true,
    trial_ends_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ================================================================
-- USERS
-- ================================================================
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email           VARCHAR(200) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(200) NOT NULL,
    role            user_role NOT NULL DEFAULT 'VIEWER',
    active          BOOLEAN DEFAULT true,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_users_tenant ON users(tenant_id);

-- ================================================================
-- COST CENTERS (centros de custo, hierárquicos)
-- ================================================================
CREATE TABLE cost_centers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    parent_id       UUID REFERENCES cost_centers(id) ON DELETE SET NULL,
    code            VARCHAR(30) NOT NULL,
    name            VARCHAR(200) NOT NULL,
    cc_type         cc_type NOT NULL,
    active          BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (tenant_id, code)
);
CREATE INDEX idx_cc_tenant ON cost_centers(tenant_id);
CREATE INDEX idx_cc_parent ON cost_centers(parent_id);

-- ================================================================
-- CHART OF ACCOUNTS (plano de contas)
-- ================================================================
CREATE TABLE accounts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    code            VARCHAR(30) NOT NULL,
    name            VARCHAR(200) NOT NULL,
    category        cost_category NOT NULL,
    nature          cost_nature NOT NULL,
    active          BOOLEAN DEFAULT true,
    UNIQUE (tenant_id, code)
);
CREATE INDEX idx_accounts_tenant ON accounts(tenant_id);

-- ================================================================
-- ENTRIES (lançamentos mensais por centro + conta)
-- ================================================================
CREATE TABLE entries (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    cost_center_id  UUID NOT NULL REFERENCES cost_centers(id),
    account_id      UUID NOT NULL REFERENCES accounts(id),
    period          DATE NOT NULL,           -- sempre primeiro dia do mês
    amount          NUMERIC(14,2) NOT NULL CHECK (amount >= 0),
    source          VARCHAR(30) DEFAULT 'MANUAL',   -- MANUAL, CSV, ERP
    notes           TEXT,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_entries_tenant_period ON entries(tenant_id, period);
CREATE INDEX idx_entries_cc ON entries(cost_center_id);

-- ================================================================
-- REVENUE (receita por centro produtivo)
-- ================================================================
CREATE TABLE revenues (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    cost_center_id  UUID NOT NULL REFERENCES cost_centers(id),
    period          DATE NOT NULL,
    gross_revenue   NUMERIC(14,2) NOT NULL DEFAULT 0,
    deductions      NUMERIC(14,2) NOT NULL DEFAULT 0,
    variable_cost   NUMERIC(14,2) NOT NULL DEFAULT 0, -- para CVL
    volume_units    INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_revenues_tenant_period ON revenues(tenant_id, period);

-- ================================================================
-- APPORTIONMENT RULES (regras de rateio para RKW)
-- Auxiliar → Produtivo(s)
-- ================================================================
CREATE TABLE apportionment_rules (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    source_cc_id    UUID NOT NULL REFERENCES cost_centers(id),
    target_cc_id    UUID NOT NULL REFERENCES cost_centers(id),
    percentage      NUMERIC(6,3) NOT NULL CHECK (percentage >= 0 AND percentage <= 100),
    valid_from      DATE NOT NULL DEFAULT '1900-01-01',
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_apport_tenant ON apportionment_rules(tenant_id);

-- ================================================================
-- COSTING RUNS (resultado persistido de um cálculo)
-- ================================================================
CREATE TABLE costing_runs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    period          DATE NOT NULL,
    method          VARCHAR(20) NOT NULL,  -- RKW | VARIAVEL
    status          VARCHAR(20) DEFAULT 'DONE',
    summary         JSONB NOT NULL,
    detail          JSONB NOT NULL,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_runs_tenant_period ON costing_runs(tenant_id, period);

-- ================================================================
-- AUDIT LOG
-- ================================================================
CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    tenant_id       UUID,
    user_id         UUID,
    action          VARCHAR(50) NOT NULL,
    entity          VARCHAR(50) NOT NULL,
    entity_id       UUID,
    payload         JSONB,
    ip              INET,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_audit_tenant_time ON audit_log(tenant_id, created_at DESC);

-- ================================================================
-- ROW LEVEL SECURITY
-- ================================================================
ALTER TABLE users                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_centers          ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts              ENABLE ROW LEVEL SECURITY;
ALTER TABLE entries               ENABLE ROW LEVEL SECURITY;
ALTER TABLE revenues              ENABLE ROW LEVEL SECURITY;
ALTER TABLE apportionment_rules   ENABLE ROW LEVEL SECURITY;
ALTER TABLE costing_runs          ENABLE ROW LEVEL SECURITY;

-- Política: tenant_id da linha deve bater com o app.current_tenant setado pela sessão
CREATE POLICY tenant_isolation_users ON users
    USING (tenant_id::text = current_setting('app.current_tenant', true));
CREATE POLICY tenant_isolation_cc ON cost_centers
    USING (tenant_id::text = current_setting('app.current_tenant', true));
CREATE POLICY tenant_isolation_acc ON accounts
    USING (tenant_id::text = current_setting('app.current_tenant', true));
CREATE POLICY tenant_isolation_entries ON entries
    USING (tenant_id::text = current_setting('app.current_tenant', true));
CREATE POLICY tenant_isolation_rev ON revenues
    USING (tenant_id::text = current_setting('app.current_tenant', true));
CREATE POLICY tenant_isolation_apport ON apportionment_rules
    USING (tenant_id::text = current_setting('app.current_tenant', true));
CREATE POLICY tenant_isolation_runs ON costing_runs
    USING (tenant_id::text = current_setting('app.current_tenant', true));

-- ================================================================
-- VIEWS analíticas
-- ================================================================
CREATE OR REPLACE VIEW v_monthly_cost_center AS
SELECT
    e.tenant_id,
    e.cost_center_id,
    cc.code AS cc_code,
    cc.name AS cc_name,
    cc.cc_type,
    e.period,
    SUM(CASE WHEN a.nature = 'FIXO' THEN e.amount ELSE 0 END)    AS fixed_cost,
    SUM(CASE WHEN a.nature = 'VARIAVEL' THEN e.amount ELSE 0 END) AS variable_cost,
    SUM(e.amount) AS total_cost,
    SUM(CASE WHEN a.category = 'PESSOAL' THEN e.amount ELSE 0 END)     AS personnel_cost,
    SUM(CASE WHEN a.category = 'MATERIAL' THEN e.amount ELSE 0 END)    AS material_cost,
    SUM(CASE WHEN a.category = 'MEDICAMENTO' THEN e.amount ELSE 0 END) AS drug_cost
FROM entries e
JOIN cost_centers cc ON cc.id = e.cost_center_id
JOIN accounts a ON a.id = e.account_id
GROUP BY e.tenant_id, e.cost_center_id, cc.code, cc.name, cc.cc_type, e.period;

CREATE OR REPLACE VIEW v_monthly_margin AS
SELECT
    r.tenant_id,
    r.cost_center_id,
    cc.code AS cc_code,
    cc.name AS cc_name,
    r.period,
    r.gross_revenue,
    r.deductions,
    (r.gross_revenue - r.deductions) AS net_revenue,
    r.variable_cost,
    (r.gross_revenue - r.deductions - r.variable_cost) AS contribution_margin,
    CASE WHEN (r.gross_revenue - r.deductions) > 0
         THEN ((r.gross_revenue - r.deductions - r.variable_cost) / (r.gross_revenue - r.deductions)) * 100
         ELSE 0
    END AS margin_pct,
    r.volume_units
FROM revenues r
JOIN cost_centers cc ON cc.id = r.cost_center_id;

-- Trigger updated_at
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_tenants_updated
    BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
