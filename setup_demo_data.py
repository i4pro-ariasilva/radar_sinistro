"""
Script para limpar dados e inserir 10 apólices de demonstração
com análises de cobertura e níveis de risco variados
"""

import sqlite3
import random
from datetime import datetime, timedelta
import sys
import os

def clean_database():
    """Limpa todas as tabelas relacionadas a apólices e coberturas"""
    conn = sqlite3.connect('database/radar_sinistro.db')
    cursor = conn.cursor()
    
    # Limpar tabelas em ordem para respeitar foreign keys
    tables_to_clean = [
        'notificacoes_risco',
        'cobertura_risco',
        'apolice_coberturas_bloqueadas',
        'apolice_cobertura',
        'previsoes_risco',
        'apolices'
    ]
    
    for table in tables_to_clean:
        try:
            cursor.execute(f'DELETE FROM {table}')
            print(f'✅ Tabela {table} limpa')
        except Exception as e:
            print(f'⚠️ Erro ao limpar {table}: {e}')
    
    conn.commit()
    conn.close()
    print("\n🧹 Limpeza do banco concluída!")

def calculate_risk_score(coverage_type, climate_data, policy_data, target_risk):
    """Calcula score de risco baseado em dados climáticos e da apólice"""
    
    base_score = 30  # Score base
    
    # Fatores de risco por cobertura
    if coverage_type == "vendaval":
        base_score += climate_data["velocidade_vento"] * 0.8
        base_score += climate_data["rajadas_vento"] * 0.6
        base_score += (1040 - climate_data["pressao_atmosferica"]) * 2
        
    elif coverage_type == "granizo":
        base_score += climate_data["diferencial_temperatura"] * 3
        base_score += climate_data["umidade"] * 0.3
        base_score += climate_data["cobertura_nuvens"] * 0.2
        
    elif coverage_type == "alagamento":
        base_score += climate_data["precipitacao"] * 0.7
        base_score += climate_data["umidade"] * 0.4
        if policy_data["tipo_residencia"] == "Casa":
            base_score += 10  # Casas têm maior risco de alagamento
            
    elif coverage_type == "danos_eletricos":
        base_score += climate_data["precipitacao"] * 0.5
        base_score += climate_data["velocidade_vento"] * 0.4
        base_score += climate_data["umidade"] * 0.3
        base_score += climate_data["cobertura_nuvens"] * 0.2
    
    # Ajustar pelo valor segurado (valores maiores = maior risco)
    if policy_data["valor_segurado"] > 800000:
        base_score += 15
    elif policy_data["valor_segurado"] > 500000:
        base_score += 8
    
    # Ajustar para atingir target_risk aproximado
    adjustment_factor = target_risk / max(base_score, 1)
    final_score = base_score * adjustment_factor
    
    # Adicionar variação aleatória
    final_score += random.uniform(-5, 5)
    
    # Garantir que está na faixa correta
    return max(10, min(95, final_score))

def create_sample_policies():
    """Cria 10 apólices de demonstração com análises de cobertura"""
    
    # Dados das apólices (2 alto risco, 3 médio risco, 5 baixo risco)
    policies_data = [
        # ALTO RISCO (≥75)
        {
            "numero_apolice": "POL-2024-001",
            "cep": "01310-100", # São Paulo - região de risco
            "tipo_residencia": "casa",
            "valor_segurado": 800000.00,
            "coberturas": ["vendaval", "granizo", "alagamento"],
            "latitude": -23.5505,
            "longitude": -46.6333,
            "target_risk": 85  # Alto risco
        },
        {
            "numero_apolice": "POL-2024-002", 
            "cep": "22071-900", # Rio de Janeiro - região de risco
            "tipo_residencia": "apartamento",
            "valor_segurado": 1200000.00,
            "coberturas": ["danos_eletricos", "vendaval"],
            "latitude": -22.9068,
            "longitude": -43.1729,
            "target_risk": 78  # Alto risco
        },
        
        # MÉDIO RISCO (50-74)
        {
            "numero_apolice": "POL-2024-003",
            "cep": "30112-000", # Belo Horizonte
            "tipo_residencia": "casa",
            "valor_segurado": 600000.00,
            "coberturas": ["granizo", "alagamento"],
            "latitude": -19.9167,
            "longitude": -43.9345,
            "target_risk": 62
        },
        {
            "numero_apolice": "POL-2024-004",
            "cep": "80010-000", # Curitiba
            "tipo_residencia": "apartamento", 
            "valor_segurado": 450000.00,
            "coberturas": ["vendaval"],
            "latitude": -25.4284,
            "longitude": -49.2733,
            "target_risk": 58
        },
        {
            "numero_apolice": "POL-2024-005",
            "cep": "90010-150", # Porto Alegre
            "tipo_residencia": "casa",
            "valor_segurado": 750000.00,
            "coberturas": ["danos_eletricos", "granizo"],
            "latitude": -30.0346,
            "longitude": -51.2177,
            "target_risk": 66
        },
        
        # BAIXO RISCO (<50)
        {
            "numero_apolice": "POL-2024-006",
            "cep": "40070-110", # Salvador
            "tipo_residencia": "apartamento",
            "valor_segurado": 350000.00,
            "coberturas": ["alagamento"],
            "latitude": -12.9714,
            "longitude": -38.5014,
            "target_risk": 35
        },
        {
            "numero_apolice": "POL-2024-007",
            "cep": "50030-230", # Recife
            "tipo_residencia": "casa",
            "valor_segurado": 400000.00,
            "coberturas": ["vendaval"],
            "latitude": -8.0476,
            "longitude": -34.8770,
            "target_risk": 42
        },
        {
            "numero_apolice": "POL-2024-008",
            "cep": "60165-081", # Fortaleza
            "tipo_residencia": "apartamento",
            "valor_segurado": 320000.00,
            "coberturas": ["danos_eletricos"],
            "latitude": -3.7172,
            "longitude": -38.5433,
            "target_risk": 28
        },
        {
            "numero_apolice": "POL-2024-009",
            "cep": "70040-010", # Brasília
            "tipo_residencia": "casa",
            "valor_segurado": 550000.00,
            "coberturas": ["granizo"],
            "latitude": -15.7801,
            "longitude": -47.9292,
            "target_risk": 45
        },
        {
            "numero_apolice": "POL-2024-010",
            "cep": "69900-000", # Rio Branco
            "tipo_residencia": "casa",
            "valor_segurado": 280000.00,
            "coberturas": ["alagamento"],
            "latitude": -9.9754,
            "longitude": -67.8249,
            "target_risk": 38
        }
    ]
    
    conn = sqlite3.connect('database/radar_sinistro.db')
    cursor = conn.cursor()
    
    print("\n📝 Criando apólices de demonstração...")
    
    for i, policy in enumerate(policies_data, 1):
        try:
            # Inserir apólice
            cursor.execute('''
                INSERT INTO apolices (
                    numero_apolice, segurado, cep, tipo_residencia, valor_segurado,
                    latitude, longitude, data_contratacao, ativa
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                policy["numero_apolice"],
                f"Segurado {i:02d}",  # Nome do segurado
                policy["cep"],
                policy["tipo_residencia"], 
                policy["valor_segurado"],
                policy["latitude"],
                policy["longitude"],
                datetime.now().date()
            ))
            
            apolice_id = cursor.lastrowid
            
            # Inserir coberturas para a apólice
            for cobertura in policy["coberturas"]:
                cursor.execute('''
                    INSERT INTO apolice_cobertura (apolice_id, cobertura_nome)
                    VALUES (?, ?)
                ''', (apolice_id, cobertura))
            
            # Gerar análise de cobertura para cada cobertura da apólice
            for cobertura in policy["coberturas"]:
                try:
                    # Simular dados climáticos baseados na região
                    climate_data = generate_climate_data(policy["cep"], policy["target_risk"])
                    
                    # Calcular risco usando função simplificada
                    risk_score = calculate_risk_score(
                        coverage_type=cobertura,
                        climate_data=climate_data,
                        policy_data={
                            'cep': policy["cep"],
                            'tipo_residencia': policy["tipo_residencia"],
                            'valor_segurado': policy["valor_segurado"],
                            'latitude': policy["latitude"],
                            'longitude': policy["longitude"]
                        },
                        target_risk=policy["target_risk"]
                    )
                    
                    # Garantir que atinge o target risk
                    if policy["target_risk"] >= 75:  # Alto risco
                        risk_score = max(risk_score, 75)
                    elif policy["target_risk"] >= 50:  # Médio risco
                        risk_score = max(50, min(risk_score, 74))
                    else:  # Baixo risco
                        risk_score = min(risk_score, 49)
                    
                    # Classificar risco
                    if risk_score >= 75:
                        risk_level = "alto"
                        recommendations = f"ATENÇÃO: Risco elevado para {cobertura}. Considere medidas preventivas imediatas."
                    elif risk_score >= 50:
                        risk_level = "medio"
                        recommendations = f"Monitoramento recomendado para {cobertura}. Acompanhar condições climáticas."
                    else:
                        risk_level = "baixo"
                        recommendations = f"Situação controlada para {cobertura}. Manter monitoramento rotineiro."
                    
                    # Inserir análise de cobertura
                    cursor.execute('''
                        INSERT INTO cobertura_risco (
                            nr_apolice, cd_cobertura, score_risco, nivel_risco,
                            fatores_risco, data_calculo, modelo_usado
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        policy["numero_apolice"],
                        1,  # cd_cobertura padrão
                        round(risk_score, 1),
                        risk_level,
                        f"Análise baseada em condições climáticas de {policy['cep']}. Cobertura: {cobertura}",
                        datetime.now(),
                        "ML_Model"
                    ))
                    
                except Exception as e:
                    print(f"⚠️ Erro ao analisar cobertura {cobertura}: {e}")
                    # Inserir análise básica em caso de erro
                    basic_score = policy["target_risk"] + random.randint(-5, 5)
                    basic_level = "alto" if basic_score >= 75 else "medio" if basic_score >= 50 else "baixo"
                    
                    cursor.execute('''
                        INSERT INTO cobertura_risco (
                            nr_apolice, cd_cobertura, score_risco, nivel_risco,
                            fatores_risco, data_calculo, modelo_usado
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        policy["numero_apolice"],
                        1,  # cd_cobertura padrão
                        basic_score,
                        basic_level,
                        f"Análise básica para {policy['cep']}. Cobertura: {cobertura}",
                        datetime.now(),
                        "Basic_Analysis"
                    ))
            
            # Determinar status da apólice
            risk_counts = {"alto": 0, "medio": 0, "baixo": 0}
            for cob in policy["coberturas"]:
                if policy["target_risk"] >= 75:
                    risk_counts["alto"] += 1
                elif policy["target_risk"] >= 50:
                    risk_counts["medio"] += 1 
                else:
                    risk_counts["baixo"] += 1
            
            status_emoji = "🔴" if risk_counts["alto"] > 0 else "🟡" if risk_counts["medio"] > 0 else "🟢"
            
            print(f"{status_emoji} Apólice {i}/10: {policy['numero_apolice']} - {len(policy['coberturas'])} coberturas")
            
        except Exception as e:
            print(f"❌ Erro ao criar apólice {policy['numero_apolice']}: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Criação de apólices concluída!")

def generate_climate_data(cep, target_risk):
    """Gera dados climáticos simulados baseados no CEP e nível de risco desejado"""
    # Dados base por região (simulados)
    base_data = {
        "temperatura_atual": random.uniform(15, 35),
        "umidade": random.uniform(40, 90),
        "pressao_atmosferica": random.uniform(980, 1030),
        "cobertura_nuvens": random.uniform(0, 100)
    }
    
    # Ajustar dados para simular risco
    if target_risk >= 75:  # Alto risco
        base_data.update({
            "velocidade_vento": random.uniform(60, 120),  # Vento forte
            "precipitacao": random.uniform(50, 150),      # Chuva intensa
            "rajadas_vento": random.uniform(80, 150),
            "diferencial_temperatura": random.uniform(15, 25)
        })
    elif target_risk >= 50:  # Médio risco
        base_data.update({
            "velocidade_vento": random.uniform(30, 60),
            "precipitacao": random.uniform(10, 50),
            "rajadas_vento": random.uniform(40, 80),
            "diferencial_temperatura": random.uniform(8, 15)
        })
    else:  # Baixo risco
        base_data.update({
            "velocidade_vento": random.uniform(5, 30),
            "precipitacao": random.uniform(0, 10),
            "rajadas_vento": random.uniform(10, 40),
            "diferencial_temperatura": random.uniform(2, 8)
        })
    
    return base_data

def verify_data():
    """Verifica os dados inseridos"""
    conn = sqlite3.connect('database/radar_sinistro.db')
    cursor = conn.cursor()
    
    # Contar apólices
    cursor.execute('SELECT COUNT(*) FROM apolices')
    apolices_count = cursor.fetchone()[0]
    
    # Contar análises por nível de risco
    cursor.execute('''
        SELECT nivel_risco, COUNT(*) 
        FROM cobertura_risco 
        GROUP BY nivel_risco
    ''')
    risk_counts = dict(cursor.fetchall())
    
    # Listar apólices com detalhes
    cursor.execute('''
        SELECT a.numero_apolice, a.cep, a.tipo_residencia, a.valor_segurado,
               COUNT(cr.id) as num_coberturas,
               AVG(cr.score_risco) as score_medio,
               MAX(CASE WHEN cr.nivel_risco = 'alto' THEN 1 
                        WHEN cr.nivel_risco = 'medio' THEN 2 
                        ELSE 3 END) as maior_risco_num
        FROM apolices a
        LEFT JOIN cobertura_risco cr ON a.numero_apolice = cr.nr_apolice
        GROUP BY a.numero_apolice
        ORDER BY score_medio DESC
    ''')
    policies = cursor.fetchall()
    
    conn.close()
    
    print(f"\n📊 RESUMO DOS DADOS INSERIDOS")
    print(f"{'='*50}")
    print(f"Total de apólices: {apolices_count}")
    print(f"Análises por nível:")
    for level, count in risk_counts.items():
        emoji = "🔴" if level == "alto" else "🟡" if level == "medio" else "🟢"
        print(f"  {emoji} {level.title()}: {count}")
    
    print(f"\n📋 DETALHES DAS APÓLICES:")
    print(f"{'Apólice':<15} {'CEP':<10} {'Tipo':<12} {'Valor':<12} {'Score':<6} {'Risco':<6} {'Coberturas'}")
    print(f"{'-'*90}")
    
    for policy in policies:
        numero, cep, tipo, valor, num_cob, score, risco_num = policy
        valor_fmt = f"R${valor:,.0f}" if valor else "N/A"
        score_fmt = f"{score:.1f}" if score else "N/A"
        
        # Converter número de risco para emoji
        if risco_num == 1:  # alto
            risco_emoji = "�"
        elif risco_num == 2:  # medio  
            risco_emoji = "🟡"
        else:  # baixo
            risco_emoji = "🟢"
        
        coberturas_fmt = f"{num_cob} cobertura(s)" if num_cob else "N/A"
        
        print(f"{numero:<15} {cep:<10} {tipo:<12} {valor_fmt:<12} {score_fmt:<6} {risco_emoji:<6} {coberturas_fmt}")

if __name__ == "__main__":
    print("🧹 Iniciando limpeza e criação de dados de demonstração...")
    
    # Limpar dados existentes
    clean_database()
    
    # Criar novas apólices
    create_sample_policies()
    
    # Verificar resultados
    verify_data()
    
    print(f"\n🎉 Processo concluído com sucesso!")
    print(f"💡 Execute 'streamlit run app.py' para ver os resultados na interface!")