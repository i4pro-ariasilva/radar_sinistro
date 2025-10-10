-- Schema do Banco de Dados para Sistema de Radar de Sinistro


-- Tabela de apólices
CREATE TABLE IF NOT EXISTS apolices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_apolice VARCHAR(50) UNIQUE NOT NULL,
    segurado VARCHAR(100) NOT NULL,
    email TEXT,
    telefone TEXT,
    cep VARCHAR(9) NOT NULL,
    latitude REAL,
    longitude REAL,
    tipo_residencia VARCHAR(20) NOT NULL CHECK(tipo_residencia IN ('casa', 'apartamento', 'sobrado', 'kitnet')),
    valor_segurado DECIMAL(12,2) NOT NULL CHECK(valor_segurado > 0),
    data_contratacao DATE NOT NULL,
    data_inicio DATE, -- Nova coluna para data efetiva de início
    score_risco DECIMAL(5,2), -- Score de risco atual
    nivel_risco VARCHAR(10) CHECK(nivel_risco IN ('baixo', 'medio', 'alto', 'critico')),
    probabilidade_sinistro DECIMAL(5,2),
    ativa BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de sinistros históricos
CREATE TABLE IF NOT EXISTS sinistros_historicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    apolice_id INTEGER,
    data_sinistro DATETIME NOT NULL,
    tipo_sinistro VARCHAR(50) NOT NULL,
    valor_prejuizo DECIMAL(12,2) CHECK(valor_prejuizo >= 0),
    causa VARCHAR(100),
    condicoes_climaticas TEXT,
    precipitacao_mm REAL,
    vento_kmh REAL,
    temperatura_c REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (apolice_id) REFERENCES apolices(id) ON DELETE CASCADE
);

-- Tabela de previsões de risco
CREATE TABLE IF NOT EXISTS previsoes_risco (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    apolice_id INTEGER NOT NULL,
    data_previsao DATETIME NOT NULL,
    score_risco DECIMAL(5,2) NOT NULL CHECK(score_risco >= 0 AND score_risco <= 100),
    nivel_risco VARCHAR(10) NOT NULL CHECK(nivel_risco IN ('baixo', 'medio', 'alto', 'critico')),
    fatores_risco TEXT,
    dados_climaticos TEXT,
    modelo_versao VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (apolice_id) REFERENCES apolices(id) ON DELETE CASCADE
);

-- Tabela de dados climáticos coletados
CREATE TABLE IF NOT EXISTS dados_climaticos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    data_coleta DATETIME NOT NULL,
    temperatura_c REAL,
    precipitacao_mm REAL,
    vento_kmh REAL,
    umidade_percent REAL,
    pressao_hpa REAL,
    fonte VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_apolices_cep ON apolices(cep);
CREATE INDEX IF NOT EXISTS idx_apolices_coords ON apolices(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_apolices_ativa ON apolices(ativa);
CREATE INDEX IF NOT EXISTS idx_apolices_score ON apolices(score_risco);
CREATE INDEX IF NOT EXISTS idx_sinistros_data ON sinistros_historicos(data_sinistro);
CREATE INDEX IF NOT EXISTS idx_sinistros_apolice ON sinistros_historicos(apolice_id);
CREATE INDEX IF NOT EXISTS idx_previsoes_data ON previsoes_risco(data_previsao);
CREATE INDEX IF NOT EXISTS idx_previsoes_apolice ON previsoes_risco(apolice_id);
CREATE INDEX IF NOT EXISTS idx_previsoes_score ON previsoes_risco(score_risco);
CREATE INDEX IF NOT EXISTS idx_climaticos_coords ON dados_climaticos(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_climaticos_data ON dados_climaticos(data_coleta);

-- Tabela de notificações de risco (log de envios simulados ou reais)
CREATE TABLE IF NOT EXISTS notificacoes_risco (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    apolice_id INTEGER NOT NULL,
    numero_apolice VARCHAR(50) NOT NULL,
    segurado VARCHAR(100),
    email TEXT,
    telefone TEXT,
    canal VARCHAR(20) NOT NULL, -- email, sms, ambos, outro
    mensagem TEXT NOT NULL,
    score_risco_enviado DECIMAL(5,2),
    nivel_risco_enviado VARCHAR(10),
    enviado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    simulacao BOOLEAN DEFAULT 1, -- 1=simulação, 0=real
    status VARCHAR(20) DEFAULT 'sucesso', -- sucesso, falha, pendente
    erro TEXT
    -- Unicidade diária será controlada em nível de aplicação (SELECT antes do INSERT)
);

CREATE INDEX IF NOT EXISTS idx_notificacoes_apolice ON notificacoes_risco(apolice_id);
CREATE INDEX IF NOT EXISTS idx_notificacoes_data ON notificacoes_risco(enviado_em);

-- Views úteis para consultas frequentes
CREATE VIEW IF NOT EXISTS vw_apolices_ativas AS
SELECT 
    a.*,
    COUNT(s.id) as total_sinistros,
    COALESCE(SUM(s.valor_prejuizo), 0) as valor_total_sinistros
FROM apolices a
LEFT JOIN sinistros_historicos s ON a.id = s.apolice_id
WHERE a.ativa = 1
GROUP BY a.id;

CREATE VIEW IF NOT EXISTS vw_previsoes_recentes AS
SELECT 
    p.*,
    a.numero_apolice,
    a.cep,
    a.tipo_residencia,
    a.valor_segurado
FROM previsoes_risco p
JOIN apolices a ON p.apolice_id = a.id
WHERE p.data_previsao >= datetime('now', '-1 day')
ORDER BY p.score_risco DESC;

-- Triggers para atualizar timestamp
CREATE TRIGGER IF NOT EXISTS update_apolices_timestamp 
    AFTER UPDATE ON apolices
BEGIN
    UPDATE apolices SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;