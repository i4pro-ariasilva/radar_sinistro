-- Migration: Adicionar tabela para riscos por cobertura
-- Data: 2025-10-09
-- Propósito: Armazenar análises de risco detalhadas por cobertura individual

-- Tabela principal para riscos por cobertura
CREATE TABLE IF NOT EXISTS cobertura_risco (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nr_apolice VARCHAR(50) NOT NULL,
    cd_cobertura INTEGER NOT NULL,
    cd_produto INTEGER NOT NULL,
    
    -- Dados do risco calculado
    score_risco DECIMAL(5,2) NOT NULL CHECK(score_risco >= 0 AND score_risco <= 100),
    nivel_risco VARCHAR(15) NOT NULL CHECK(nivel_risco IN ('muito_baixo', 'baixo', 'medio', 'alto', 'critico')),
    probabilidade DECIMAL(6,4) NOT NULL CHECK(probabilidade >= 0 AND probabilidade <= 1),
    
    -- Detalhes da análise ML
    modelo_usado VARCHAR(50),                    -- ex: 'alagamento', 'vendaval', 'granizo'
    versao_modelo VARCHAR(20),                   -- versão do modelo ML
    fatores_risco TEXT,                          -- JSON com fatores que influenciaram o risco
    dados_climaticos TEXT,                       -- JSON com dados climáticos usados
    dados_propriedade TEXT,                      -- JSON com dados da propriedade usados
    
    -- Resultado detalhado da predição
    resultado_predicao TEXT,                     -- JSON completo do resultado do modelo
    confianca_modelo DECIMAL(4,3),               -- confiança do modelo (0-1)
    explicabilidade TEXT,                        -- JSON com explicações do modelo (SHAP, etc.)
    
    -- Metadados temporais
    data_calculo DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tempo_processamento_ms INTEGER,              -- tempo que levou para calcular
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints e relacionamentos
    FOREIGN KEY (nr_apolice) REFERENCES apolices(numero_apolice) ON DELETE CASCADE,
    FOREIGN KEY (cd_cobertura) REFERENCES coberturas(cd_cobertura) ON DELETE CASCADE,
    FOREIGN KEY (cd_produto) REFERENCES produtos(cd_produto) ON DELETE CASCADE,
    
    -- Constraint única: uma análise por cobertura por apólice por data
    UNIQUE(nr_apolice, cd_cobertura, data_calculo)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_cobertura_risco_apolice ON cobertura_risco(nr_apolice);
CREATE INDEX IF NOT EXISTS idx_cobertura_risco_cobertura ON cobertura_risco(cd_cobertura);
CREATE INDEX IF NOT EXISTS idx_cobertura_risco_score ON cobertura_risco(score_risco DESC);
CREATE INDEX IF NOT EXISTS idx_cobertura_risco_nivel ON cobertura_risco(nivel_risco);
CREATE INDEX IF NOT EXISTS idx_cobertura_risco_data ON cobertura_risco(data_calculo);
CREATE INDEX IF NOT EXISTS idx_cobertura_risco_modelo ON cobertura_risco(modelo_usado);
CREATE INDEX IF NOT EXISTS idx_cobertura_risco_composite ON cobertura_risco(nr_apolice, cd_cobertura, data_calculo DESC);

-- Trigger para atualizar updated_at
CREATE TRIGGER IF NOT EXISTS update_cobertura_risco_timestamp 
    AFTER UPDATE ON cobertura_risco
BEGIN
    UPDATE cobertura_risco SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- View para consultas frequentes: últimas análises por apólice
CREATE VIEW IF NOT EXISTS vw_ultima_analise_cobertura AS
SELECT 
    cr.*,
    c.nm_cobertura,
    c.dv_basica,
    p.nm_produto,
    a.segurado,
    a.cep,
    a.valor_segurado
FROM cobertura_risco cr
JOIN coberturas c ON cr.cd_cobertura = c.cd_cobertura
JOIN produtos p ON cr.cd_produto = p.cd_produto
JOIN apolices a ON cr.nr_apolice = a.numero_apolice
WHERE cr.data_calculo = (
    SELECT MAX(data_calculo)
    FROM cobertura_risco cr2
    WHERE cr2.nr_apolice = cr.nr_apolice 
    AND cr2.cd_cobertura = cr.cd_cobertura
);

-- View para ranking de riscos por cobertura
CREATE VIEW IF NOT EXISTS vw_ranking_risco_cobertura AS
SELECT 
    c.nm_cobertura,
    COUNT(*) as total_apolices,
    AVG(cr.score_risco) as score_medio,
    MAX(cr.score_risco) as score_maximo,
    MIN(cr.score_risco) as score_minimo,
    COUNT(CASE WHEN cr.nivel_risco IN ('alto', 'critico') THEN 1 END) as alto_risco_count,
    COUNT(CASE WHEN cr.nivel_risco = 'critico' THEN 1 END) as critico_count
FROM cobertura_risco cr
JOIN coberturas c ON cr.cd_cobertura = c.cd_cobertura
WHERE cr.data_calculo >= datetime('now', '-30 days')  -- últimos 30 dias
GROUP BY c.cd_cobertura, c.nm_cobertura
ORDER BY score_medio DESC;

-- View para histórico de análises
CREATE VIEW IF NOT EXISTS vw_historico_analise_cobertura AS
SELECT 
    cr.*,
    c.nm_cobertura,
    a.segurado,
    LAG(cr.score_risco) OVER (
        PARTITION BY cr.nr_apolice, cr.cd_cobertura 
        ORDER BY cr.data_calculo
    ) as score_anterior,
    (cr.score_risco - LAG(cr.score_risco) OVER (
        PARTITION BY cr.nr_apolice, cr.cd_cobertura 
        ORDER BY cr.data_calculo
    )) as variacao_score
FROM cobertura_risco cr
JOIN coberturas c ON cr.cd_cobertura = c.cd_cobertura
JOIN apolices a ON cr.nr_apolice = a.numero_apolice
ORDER BY cr.nr_apolice, cr.cd_cobertura, cr.data_calculo DESC;