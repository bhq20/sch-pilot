-- ================================================================
-- SCH PILOT — Seed inicial para demo
-- ================================================================

-- Tenant demo HUMANA
INSERT INTO tenants (id, slug, name, segment, cnpj)
VALUES ('11111111-1111-1111-1111-111111111111', 'demo-humana', 'Hospital Demo Humana', 'HUMANA', '00.000.000/0001-00');

-- Tenant demo VET
INSERT INTO tenants (id, slug, name, segment, cnpj)
VALUES ('22222222-2222-2222-2222-222222222222', 'demo-vet', 'Clínica Demo Veterinária', 'VETERINARIA', '00.000.000/0002-00');

-- Admin demo (senha: demo1234, bcrypt hash gerado via passlib)
-- Hash válido para 'demo1234'
INSERT INTO users (id, tenant_id, email, password_hash, full_name, role)
VALUES (
    '33333333-3333-3333-3333-333333333333',
    '11111111-1111-1111-1111-111111111111',
    'admin@demo.com',
    '$2b$12$KIXq0N1BJ1rQoBtZJkX5muIqk8kYXhzLqLJpXXBRPVwVMjW0aLVSG',
    'Administrador Demo',
    'ADMIN'
);

-- Plano de contas básico
INSERT INTO accounts (tenant_id, code, name, category, nature) VALUES
('11111111-1111-1111-1111-111111111111', '3.01.01', 'Salários e encargos',              'PESSOAL',     'FIXO'),
('11111111-1111-1111-1111-111111111111', '3.01.02', 'Plantão médico',                    'PESSOAL',     'SEMI_VARIAVEL'),
('11111111-1111-1111-1111-111111111111', '3.02.01', 'Material médico-hospitalar',        'MATERIAL',    'VARIAVEL'),
('11111111-1111-1111-1111-111111111111', '3.02.02', 'Material de escritório',            'MATERIAL',    'FIXO'),
('11111111-1111-1111-1111-111111111111', '3.03.01', 'Medicamentos',                      'MEDICAMENTO', 'VARIAVEL'),
('11111111-1111-1111-1111-111111111111', '3.04.01', 'Energia elétrica',                  'INFRA',       'SEMI_VARIAVEL'),
('11111111-1111-1111-1111-111111111111', '3.04.02', 'Água e esgoto',                     'INFRA',       'SEMI_VARIAVEL'),
('11111111-1111-1111-1111-111111111111', '3.04.03', 'Aluguel',                           'INFRA',       'FIXO'),
('11111111-1111-1111-1111-111111111111', '3.05.01', 'Serviços de lavanderia',            'SERVICO',     'VARIAVEL'),
('11111111-1111-1111-1111-111111111111', '3.05.02', 'Serviços de limpeza',               'SERVICO',     'FIXO'),
('11111111-1111-1111-1111-111111111111', '3.06.01', 'Depreciação equipamentos',          'DEPRECIACAO', 'FIXO');

-- Centros de custo (auxiliares + produtivos)
INSERT INTO cost_centers (id, tenant_id, code, name, cc_type) VALUES
-- Auxiliares
('aaaa1111-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'AUX-01', 'Lavanderia',        'AUXILIAR'),
('aaaa1111-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111', 'AUX-02', 'Nutrição',          'AUXILIAR'),
('aaaa1111-0000-0000-0000-000000000003', '11111111-1111-1111-1111-111111111111', 'AUX-03', 'Manutenção',        'AUXILIAR'),
-- Administrativos
('aaaa1111-0000-0000-0000-000000000004', '11111111-1111-1111-1111-111111111111', 'ADM-01', 'Administração',     'ADMINISTRATIVO'),
('aaaa1111-0000-0000-0000-000000000005', '11111111-1111-1111-1111-111111111111', 'ADM-02', 'TI',                'ADMINISTRATIVO'),
-- Produtivos
('aaaa1111-0000-0000-0000-000000000010', '11111111-1111-1111-1111-111111111111', 'PRD-01', 'UTI Adulto',        'PRODUTIVO'),
('aaaa1111-0000-0000-0000-000000000011', '11111111-1111-1111-1111-111111111111', 'PRD-02', 'Internação Clínica','PRODUTIVO'),
('aaaa1111-0000-0000-0000-000000000012', '11111111-1111-1111-1111-111111111111', 'PRD-03', 'Centro Cirúrgico',  'PRODUTIVO'),
('aaaa1111-0000-0000-0000-000000000013', '11111111-1111-1111-1111-111111111111', 'PRD-04', 'Pronto-Socorro',    'PRODUTIVO');

-- Regras de rateio (auxiliares → produtivos)
-- Lavanderia: UTI 30%, Internação 40%, CC 20%, PS 10%
INSERT INTO apportionment_rules (tenant_id, source_cc_id, target_cc_id, percentage) VALUES
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000001', 'aaaa1111-0000-0000-0000-000000000010', 30),
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000001', 'aaaa1111-0000-0000-0000-000000000011', 40),
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000001', 'aaaa1111-0000-0000-0000-000000000012', 20),
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000001', 'aaaa1111-0000-0000-0000-000000000013', 10),
-- Nutrição: UTI 25%, Internação 55%, PS 20%
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000002', 'aaaa1111-0000-0000-0000-000000000010', 25),
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000002', 'aaaa1111-0000-0000-0000-000000000011', 55),
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000002', 'aaaa1111-0000-0000-0000-000000000013', 20),
-- Manutenção: UTI 30%, Internação 30%, CC 25%, PS 15%
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000003', 'aaaa1111-0000-0000-0000-000000000010', 30),
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000003', 'aaaa1111-0000-0000-0000-000000000011', 30),
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000003', 'aaaa1111-0000-0000-0000-000000000012', 25),
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000003', 'aaaa1111-0000-0000-0000-000000000013', 15),
-- Administração: UTI 20%, Internação 30%, CC 25%, PS 25%
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000004', 'aaaa1111-0000-0000-0000-000000000010', 20),
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000004', 'aaaa1111-0000-0000-0000-000000000011', 30),
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000004', 'aaaa1111-0000-0000-0000-000000000012', 25),
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000004', 'aaaa1111-0000-0000-0000-000000000013', 25),
-- TI: distribuição igual 25% cada
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000005', 'aaaa1111-0000-0000-0000-000000000010', 25),
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000005', 'aaaa1111-0000-0000-0000-000000000011', 25),
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000005', 'aaaa1111-0000-0000-0000-000000000012', 25),
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000005', 'aaaa1111-0000-0000-0000-000000000013', 25);

-- Lançamentos de exemplo (março/2026) — valores realistas em reais
DO $$
DECLARE
    t_id UUID := '11111111-1111-1111-1111-111111111111';
    acc_sal UUID; acc_plant UUID; acc_mat UUID; acc_med UUID;
    acc_en UUID; acc_alug UUID; acc_lav UUID; acc_lim UUID; acc_dep UUID;
    cc RECORD;
BEGIN
    SELECT id INTO acc_sal   FROM accounts WHERE tenant_id=t_id AND code='3.01.01';
    SELECT id INTO acc_plant FROM accounts WHERE tenant_id=t_id AND code='3.01.02';
    SELECT id INTO acc_mat   FROM accounts WHERE tenant_id=t_id AND code='3.02.01';
    SELECT id INTO acc_med   FROM accounts WHERE tenant_id=t_id AND code='3.03.01';
    SELECT id INTO acc_en    FROM accounts WHERE tenant_id=t_id AND code='3.04.01';
    SELECT id INTO acc_alug  FROM accounts WHERE tenant_id=t_id AND code='3.04.03';
    SELECT id INTO acc_lav   FROM accounts WHERE tenant_id=t_id AND code='3.05.01';
    SELECT id INTO acc_lim   FROM accounts WHERE tenant_id=t_id AND code='3.05.02';
    SELECT id INTO acc_dep   FROM accounts WHERE tenant_id=t_id AND code='3.06.01';

    -- UTI Adulto
    INSERT INTO entries (tenant_id, cost_center_id, account_id, period, amount) VALUES
    (t_id, 'aaaa1111-0000-0000-0000-000000000010', acc_sal,   '2026-03-01', 420000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000010', acc_plant, '2026-03-01',  85000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000010', acc_mat,   '2026-03-01', 180000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000010', acc_med,   '2026-03-01', 220000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000010', acc_en,    '2026-03-01',  45000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000010', acc_dep,   '2026-03-01',  38000);

    -- Internação Clínica
    INSERT INTO entries (tenant_id, cost_center_id, account_id, period, amount) VALUES
    (t_id, 'aaaa1111-0000-0000-0000-000000000011', acc_sal,   '2026-03-01', 380000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000011', acc_mat,   '2026-03-01', 120000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000011', acc_med,   '2026-03-01', 140000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000011', acc_en,    '2026-03-01',  32000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000011', acc_dep,   '2026-03-01',  22000);

    -- Centro Cirúrgico
    INSERT INTO entries (tenant_id, cost_center_id, account_id, period, amount) VALUES
    (t_id, 'aaaa1111-0000-0000-0000-000000000012', acc_sal,   '2026-03-01', 340000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000012', acc_plant, '2026-03-01',  95000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000012', acc_mat,   '2026-03-01', 260000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000012', acc_med,   '2026-03-01', 180000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000012', acc_dep,   '2026-03-01',  55000);

    -- Pronto-Socorro
    INSERT INTO entries (tenant_id, cost_center_id, account_id, period, amount) VALUES
    (t_id, 'aaaa1111-0000-0000-0000-000000000013', acc_sal,   '2026-03-01', 290000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000013', acc_plant, '2026-03-01', 120000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000013', acc_mat,   '2026-03-01', 140000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000013', acc_med,   '2026-03-01',  90000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000013', acc_en,    '2026-03-01',  22000);

    -- Auxiliares
    INSERT INTO entries (tenant_id, cost_center_id, account_id, period, amount) VALUES
    (t_id, 'aaaa1111-0000-0000-0000-000000000001', acc_sal,  '2026-03-01',  85000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000001', acc_lav,  '2026-03-01',  42000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000002', acc_sal,  '2026-03-01', 110000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000002', acc_mat,  '2026-03-01',  68000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000003', acc_sal,  '2026-03-01',  72000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000003', acc_mat,  '2026-03-01',  28000);

    -- Administrativos
    INSERT INTO entries (tenant_id, cost_center_id, account_id, period, amount) VALUES
    (t_id, 'aaaa1111-0000-0000-0000-000000000004', acc_sal,  '2026-03-01', 180000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000004', acc_alug, '2026-03-01',  95000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000004', acc_lim,  '2026-03-01',  35000),
    (t_id, 'aaaa1111-0000-0000-0000-000000000005', acc_sal,  '2026-03-01',  95000);
END $$;

-- Receita dos produtivos
INSERT INTO revenues (tenant_id, cost_center_id, period, gross_revenue, deductions, variable_cost, volume_units) VALUES
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000010', '2026-03-01', 1850000, 280000, 580000, 145),
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000011', '2026-03-01', 1420000, 200000, 380000, 520),
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000012', '2026-03-01', 2650000, 380000, 780000, 220),
('11111111-1111-1111-1111-111111111111', 'aaaa1111-0000-0000-0000-000000000013', '2026-03-01',  980000, 140000, 320000, 1850);
