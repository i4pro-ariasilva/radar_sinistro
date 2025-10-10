#!/usr/bin/env python3
"""
Script completo para gerar dados simulados e treinar modelos de cobertura.
Execute este script para preparar os modelos para uso na interface web.
"""

import sys
import os
from datetime import datetime

# Adicionar ao path
sys.path.append('.')

def main():
    """Execução completa: gerar dados + treinar modelos"""
    
    print("🚀 SISTEMA COMPLETO DE TREINAMENTO DE MODELOS")
    print("=" * 60)
    print(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Etapa 1: Gerar dados simulados
        print("📊 ETAPA 1: GERANDO DADOS SIMULADOS")
        print("-" * 40)
        
        from src.ml.data_simulator import generate_all_coverage_datasets
        generate_all_coverage_datasets(samples_per_coverage=3000)
        
        print("\n✅ Dados simulados gerados com sucesso!")
        print()
        
        # Etapa 2: Treinar modelos
        print("🤖 ETAPA 2: TREINANDO MODELOS")
        print("-" * 40)
        
        from src.ml.coverage_model_trainer import CoverageModelTrainer
        
        trainer = CoverageModelTrainer()
        results = trainer.train_all_models()
        
        print("\n✅ Modelos treinados com sucesso!")
        print()
        
        # Etapa 3: Validar modelos treinados
        print("🔍 ETAPA 3: VALIDANDO MODELOS")
        print("-" * 40)
        
        from src.ml.coverage_predictors import CoverageRiskManager
        
        # Teste rápido dos modelos
        manager = CoverageRiskManager()
        
        test_policy = {
            'numero_apolice': 'TEST-TRAINED-001',
            'cep': '01234567',
            'tipo_residencia': 'casa',
            'valor_segurado': 250000,
            'latitude': -23.5505,
            'longitude': -46.6333
        }
        
        print("  🧪 Testando modelos treinados...")
        analysis = manager.analyze_all_coverages(test_policy)
        
        print(f"  ✅ Teste concluído!")
        print(f"     - Coberturas analisadas: {len(analysis['coverage_analysis'])}")
        print(f"     - Score médio: {analysis['summary']['average_risk_score']:.1f}")
        print(f"     - Maior risco: {analysis['summary']['highest_risk_coverage']['name']}")
        
        # Verificar se modelos estão realmente treinados
        trained_models = 0
        for coverage, result in results.items():
            if 'error' not in result:
                trained_models += 1
        
        print(f"     - Modelos ativos: {trained_models}/4")
        print()
        
        # Resumo final
        print("🎉 PROCESSO CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print()
        print("📋 Resumo dos resultados:")
        
        for coverage, result in results.items():
            if 'error' not in result:
                print(f"✅ {coverage.replace('_', ' ').title()}: AUC = {result['auc_score']:.3f}")
            else:
                print(f"❌ {coverage.replace('_', ' ').title()}: {result['error']}")
        
        print()
        print("📁 Arquivos gerados:")
        print(f"   📊 Datasets: data/training/")
        print(f"   🤖 Modelos: models/")
        print(f"   📄 Relatórios: models/reports/")
        print()
        print("🌐 Os modelos estão prontos para uso na interface web!")
        print("   Execute: streamlit run app.py")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE O PROCESSO: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Verifique as dependências e tente novamente.")

if __name__ == "__main__":
    main()