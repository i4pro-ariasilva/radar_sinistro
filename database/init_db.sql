-- Schema do Banco de Dados para Sistema de Radar de Sinistro


-- Tabela de apólices
CREATE TABLE IF NOT EXISTS apolices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_apolice VARCHAR(50) UNIQUE NOT NULL,
    segurado VARCHAR(100) NOT NULL,
    cd_produto INTEGER, -- código do produto (referência aos produtos)
    cep VARCHAR(9) NOT NULL,
    latitude REAL,
    longitude REAL,
    tipo_residencia VARCHAR(20) NOT NULL CHECK(tipo_residencia IN ('casa', 'apartamento', 'sobrado')),
    valor_segurado DECIMAL(12,2) NOT NULL CHECK(valor_segurado > 0),
    data_contratacao DATE NOT NULL,
    data_inicio DATE, -- data de início da vigência (opcional)
    score_risco DECIMAL(5,2), -- score de risco (0-100)
    nivel_risco VARCHAR(10), -- baixo/medio/alto/critico (flexível)
    probabilidade_sinistro DECIMAL(6,4), -- probabilidade estimada
    ativa BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cd_produto) REFERENCES produtos(cd_produto)
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
CREATE INDEX IF NOT EXISTS idx_apolices_produto ON apolices(cd_produto);
CREATE INDEX IF NOT EXISTS idx_sinistros_data ON sinistros_historicos(data_sinistro);
CREATE INDEX IF NOT EXISTS idx_sinistros_apolice ON sinistros_historicos(apolice_id);
CREATE INDEX IF NOT EXISTS idx_previsoes_data ON previsoes_risco(data_previsao);
CREATE INDEX IF NOT EXISTS idx_previsoes_apolice ON previsoes_risco(apolice_id);
CREATE INDEX IF NOT EXISTS idx_previsoes_score ON previsoes_risco(score_risco);
CREATE INDEX IF NOT EXISTS idx_climaticos_coords ON dados_climaticos(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_climaticos_data ON dados_climaticos(data_coleta);

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

-- ==================== BLOQUEIO POR REGIÃO (PREFIXO CEP) ====================
-- Tabela para controlar bloqueios de emissão de novas apólices por prefixo de CEP.
-- Prefixo recomendado: 5 dígitos (ex.: '01234'). Pode suportar de 3 a 8 conforme evolução.
-- Campos adicionais para auditoria e severidade do bloqueio.
CREATE TABLE IF NOT EXISTS region_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cep_prefix TEXT NOT NULL,
    blocked INTEGER NOT NULL DEFAULT 1,           -- 1 = bloqueado, 0 = liberado
    reason TEXT,                                  -- motivo do bloqueio
    severity INTEGER,                             -- 1=normal,2=alto,3=critico (conceito inicial)
    scope TEXT,                                   -- ex.: 'residencial' ou NULL para global
    active INTEGER NOT NULL DEFAULT 1,            -- regra ativa (permite desativar sem remover)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_region_blocks_prefix ON region_blocks(cep_prefix);

-- Trigger para atualizar updated_at em region_blocks
CREATE TRIGGER IF NOT EXISTS trg_region_blocks_updated
AFTER UPDATE ON region_blocks
BEGIN
    UPDATE region_blocks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ==================== NOVAS TABELAS: PRODUTOS E COBERTURAS ====================

-- Tabela de produtos
CREATE TABLE IF NOT EXISTS produtos (
    cd_produto INTEGER PRIMARY KEY,
    cd_ramo INTEGER NOT NULL,
    nm_produto VARCHAR(100) NOT NULL,
    dt_criacao DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de coberturas
CREATE TABLE IF NOT EXISTS coberturas (
    cd_cobertura INTEGER PRIMARY KEY,
    cd_produto INTEGER NOT NULL,
    nm_cobertura VARCHAR(100) NOT NULL,
    dv_basica BOOLEAN NOT NULL DEFAULT 0, -- 0 = adicional, 1 = básica
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cd_produto) REFERENCES produtos(cd_produto) ON DELETE CASCADE
);

-- Tabela de relacionamento apólice-cobertura
CREATE TABLE IF NOT EXISTS apolice_cobertura (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cd_cobertura INTEGER NOT NULL,
    cd_produto INTEGER NOT NULL,
    nr_apolice VARCHAR(50) NOT NULL,
    dt_inclusao DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cd_cobertura) REFERENCES coberturas(cd_cobertura) ON DELETE CASCADE,
    FOREIGN KEY (cd_produto) REFERENCES produtos(cd_produto) ON DELETE CASCADE,
    FOREIGN KEY (nr_apolice) REFERENCES apolices(numero_apolice) ON DELETE CASCADE
);

-- Índices para as novas tabelas
CREATE INDEX IF NOT EXISTS idx_produtos_ramo ON produtos(cd_ramo);
CREATE INDEX IF NOT EXISTS idx_coberturas_produto ON coberturas(cd_produto);
CREATE INDEX IF NOT EXISTS idx_coberturas_basica ON coberturas(dv_basica);
CREATE INDEX IF NOT EXISTS idx_apolice_cobertura_apolice ON apolice_cobertura(nr_apolice);
CREATE INDEX IF NOT EXISTS idx_apolice_cobertura_produto ON apolice_cobertura(cd_produto);
CREATE INDEX IF NOT EXISTS idx_apolice_cobertura_cobertura ON apolice_cobertura(cd_cobertura);

-- Triggers para atualizar timestamps
CREATE TRIGGER IF NOT EXISTS update_produtos_timestamp 
    AFTER UPDATE ON produtos
BEGIN
    UPDATE produtos SET updated_at = CURRENT_TIMESTAMP WHERE cd_produto = NEW.cd_produto;
END;

CREATE TRIGGER IF NOT EXISTS update_coberturas_timestamp 
    AFTER UPDATE ON coberturas
BEGIN
    UPDATE coberturas SET updated_at = CURRENT_TIMESTAMP WHERE cd_cobertura = NEW.cd_cobertura;
END;
