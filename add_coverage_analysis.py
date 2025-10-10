"""
Script simplificado para inserir análises de cobertura nas apólices existentes
"""

import sqlite3
import random
from datetime import datetime

def add_coverage_analysis():
    """Adiciona análises de cobertura para as apólices existentes"""
    
    conn = sqlite3.connect('database/radar_sinistro.db')
    cursor = conn.cursor()
    
    # Buscar apólices existentes
    cursor.execute('SELECT numero_apolice, cep, tipo_residencia, valor_segurado FROM apolices')
    policies = cursor.fetchall()
    
    print(f"📋 Encontradas {len(policies)} apólices. Criando análises de cobertura...")
    
    # Definir análises por apólice
    coverage_plans = {
        "POL-2024-001": [("vendaval", 85), ("granizo", 82), ("alagamento", 78)],  # Alto risco
        "POL-2024-002": [("danos_eletricos", 80), ("vendaval", 76)],              # Alto risco
        "POL-2024-003": [("granizo", 65), ("alagamento", 59)],                    # Médio risco
        "POL-2024-004": [("vendaval", 58)],                                       # Médio risco  
        "POL-2024-005": [("danos_eletricos", 68), ("granizo", 64)],              # Médio risco
        "POL-2024-006": [("alagamento", 35)],                                     # Baixo risco
        "POL-2024-007": [("vendaval", 42)],                                       # Baixo risco
        "POL-2024-008": [("danos_eletricos", 28)],                               # Baixo risco
        "POL-2024-009": [("granizo", 45)],                                        # Baixo risco
        "POL-2024-010": [("alagamento", 38)]                                      # Baixo risco
    }
    
    # Mapear coberturas para cd_cobertura
    cobertura_codes = {
        "vendaval": 1,
        "granizo": 2, 
        "alagamento": 3,
        "danos_eletricos": 4
    }
    
    for numero_apolice, cep, tipo_residencia, valor_segurado in policies:
        if numero_apolice in coverage_plans:
            coverages = coverage_plans[numero_apolice]
            
            for coverage_type, risk_score in coverages:
                # Determinar nível de risco
                if risk_score >= 75:
                    risk_level = "alto"
                    fatores = f"RISCO ELEVADO: Condições climáticas severas detectadas em {cep}. " \
                             f"Análise ML indica alta probabilidade de sinistro para {coverage_type}."
                elif risk_score >= 50:
                    risk_level = "medio"
                    fatores = f"MONITORAMENTO: Condições moderadas em {cep}. " \
                             f"Acompanhar evolução climática para {coverage_type}."
                else:
                    risk_level = "baixo"
                    fatores = f"SITUAÇÃO CONTROLADA: Condições estáveis em {cep}. " \
                             f"Baixa probabilidade de sinistro para {coverage_type}."
                
                # Inserir análise de cobertura
                cursor.execute('''
                    INSERT INTO cobertura_risco (
                        nr_apolice, cd_cobertura, cd_produto, score_risco, nivel_risco, probabilidade,
                        modelo_usado, versao_modelo, fatores_risco, resultado_predicao,
                        confianca_modelo, data_calculo, tempo_processamento_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    numero_apolice,
                    cobertura_codes.get(coverage_type, 1),
                    1,  # cd_produto padrão
                    risk_score,
                    risk_level,
                    risk_score / 100.0,  # Converter para probabilidade 0-1
                    f"{coverage_type}_model",
                    "v3.0",
                    fatores,
                    f"Score: {risk_score}, Nível: {risk_level}",
                    0.85 + random.uniform(-0.1, 0.1),  # Confiança entre 0.75-0.95
                    datetime.now().isoformat(),  # Converter para string ISO
                    random.randint(50, 200)  # Tempo de processamento em ms
                ))
                
                print(f"✅ {numero_apolice}: {coverage_type} -> {risk_level.upper()} (Score: {risk_score})")
    
    conn.commit()
    conn.close()
    print(f"\n🎉 Análises de cobertura criadas com sucesso!")

def verify_results():
    """Verifica os resultados finais"""
    conn = sqlite3.connect('database/radar_sinistro.db')
    cursor = conn.cursor()
    
    # Contar análises por nível
    cursor.execute('''
        SELECT nivel_risco, COUNT(*) 
        FROM cobertura_risco 
        GROUP BY nivel_risco
    ''')
    risk_counts = dict(cursor.fetchall())
    
    # Apólices com análises
    cursor.execute('''
        SELECT a.numero_apolice, a.cep, a.tipo_residencia,
               COUNT(cr.id) as total_coberturas,
               AVG(cr.score_risco) as score_medio,
               MAX(CASE WHEN cr.nivel_risco = 'alto' THEN 1 ELSE 0 END) as tem_alto_risco
        FROM apolices a
        LEFT JOIN cobertura_risco cr ON a.numero_apolice = cr.nr_apolice
        GROUP BY a.numero_apolice
        ORDER BY score_medio DESC
    ''')
    results = cursor.fetchall()
    
    conn.close()
    
    print(f"\n📊 RESUMO FINAL:")
    print(f"{'='*60}")
    print(f"Análises por nível de risco:")
    for level, count in risk_counts.items():
        emoji = "🔴" if level == "alto" else "🟡" if level == "medio" else "🟢"
        print(f"  {emoji} {level.title()}: {count}")
    
    print(f"\n📋 APÓLICES COM ANÁLISES:")
    print(f"{'Apólice':<15} {'CEP':<10} {'Tipo':<12} {'Coberturas':<10} {'Score Médio':<12} {'Alto Risco'}")
    print(f"{'-'*80}")
    
    for apolice, cep, tipo, total_cob, score_medio, tem_alto in results:
        score_str = f"{score_medio:.1f}" if score_medio else "N/A"
        alto_emoji = "🔴" if tem_alto else "🟢"
        print(f"{apolice:<15} {cep:<10} {tipo:<12} {total_cob:<10} {score_str:<12} {alto_emoji}")
    
    # Verificar se temos as 2 apólices de alto risco solicitadas
    alto_risco_apolices = [r for r in results if r[5] == 1]  # tem_alto_risco = 1
    print(f"\n🎯 VERIFICAÇÃO: {len(alto_risco_apolices)} apólices com alto risco (objetivo: 2)")

if __name__ == "__main__":
    print("🚀 Adicionando análises de cobertura...")
    add_coverage_analysis()
    verify_results()
    print(f"\n💡 Execute 'streamlit run app.py' para visualizar no dashboard!")