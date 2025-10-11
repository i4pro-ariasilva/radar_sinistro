"""
Script para executar todos os testes do projeto
Organiza e executa testes por categoria com relatórios detalhados
"""

import unittest
import sys
import os
from pathlib import Path
import time
from io import StringIO

# Adicionar path do projeto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Importar módulos de teste
from tests.test_api import *
from tests.test_web_modules import *
from tests.test_services import *
from tests.test_ml_modules import *
from tests.test_database import *


class TestResultCollector:
    """Coleta e organiza resultados dos testes"""
    
    def __init__(self):
        self.results = {
            'API': [],
            'Web Modules': [],
            'Services': [],
            'ML Modules': [],
            'Database': []
        }
        self.summary = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def add_result(self, category, test_name, result, details=None):
        """Adiciona resultado de teste"""
        self.results[category].append({
            'test': test_name,
            'result': result,
            'details': details or ''
        })
        
        self.summary['total_tests'] += 1
        if result == 'PASS':
            self.summary['passed'] += 1
        elif result == 'FAIL':
            self.summary['failed'] += 1
        elif result == 'SKIP':
            self.summary['skipped'] += 1
        elif result == 'ERROR':
            self.summary['errors'] += 1
    
    def print_summary(self):
        """Imprime resumo dos resultados"""
        print("\n" + "="*80)
        print("RESUMO DOS TESTES - RADAR DE SINISTRO")
        print("="*80)
        
        for category, tests in self.results.items():
            if tests:
                print(f"\n📁 {category}:")
                for test in tests:
                    status_icon = {
                        'PASS': '✅',
                        'FAIL': '❌', 
                        'SKIP': '⏭️',
                        'ERROR': '💥'
                    }.get(test['result'], '❓')
                    
                    print(f"  {status_icon} {test['test']}")
                    if test['details'] and test['result'] in ['FAIL', 'ERROR']:
                        print(f"      💬 {test['details'][:100]}...")
        
        print(f"\n📊 ESTATÍSTICAS FINAIS:")
        print(f"   Total de testes: {self.summary['total_tests']}")
        print(f"   ✅ Aprovados: {self.summary['passed']}")
        print(f"   ❌ Falhas: {self.summary['failed']}")
        print(f"   ⏭️ Ignorados: {self.summary['skipped']}")
        print(f"   💥 Erros: {self.summary['errors']}")
        
        success_rate = (self.summary['passed'] / max(1, self.summary['total_tests'])) * 100
        print(f"   📈 Taxa de sucesso: {success_rate:.1f}%")


def run_test_suite(test_class, category, collector):
    """Executa uma suite de testes e coleta resultados"""
    print(f"\n🔍 Executando testes: {category}")
    print("-" * 50)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(test_class)
    
    # Capturar output dos testes
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Processar resultados
    for test, error in result.failures:
        test_name = test._testMethodName
        collector.add_result(category, test_name, 'FAIL', str(error))
    
    for test, error in result.errors:
        test_name = test._testMethodName
        collector.add_result(category, test_name, 'ERROR', str(error))
    
    for test in result.skipped:
        test_name = test[0]._testMethodName
        collector.add_result(category, test_name, 'SKIP', test[1])
    
    # Calcular testes bem-sucedidos
    total_tests = result.testsRun
    failed_tests = len(result.failures) + len(result.errors) + len(result.skipped)
    passed_tests = total_tests - failed_tests
    
    for i in range(passed_tests):
        collector.add_result(category, f"test_{i+1}", 'PASS')
    
    print(f"⏱️ Tempo: {end_time - start_time:.2f}s")
    print(f"📊 Executados: {total_tests}, Falhas: {len(result.failures)}, Erros: {len(result.errors)}, Ignorados: {len(result.skipped)}")


def main():
    """Função principal para executar todos os testes"""
    print("🌦️ RADAR DE SINISTRO - SUITE DE TESTES AUTOMATIZADOS")
    print("="*80)
    print(f"📁 Projeto: {PROJECT_ROOT}")
    print(f"🐍 Python: {sys.version}")
    print(f"⏰ Início: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    collector = TestResultCollector()
    
    # Definir suites de teste
    test_suites = [
        # Testes de API
        (TestRiskAPI, "API"),
        (TestPoliciesAPI, "API"),
        (TestCoveragesAPI, "API"),
        
        # Testes de módulos web
        (TestPolicyManagement, "Web Modules"),
        (TestWebMLIntegration, "Web Modules"),
        (TestAppNavigationFunctions, "Web Modules"),
        (TestDataProcessingModules, "Web Modules"),
        (TestUtilityModules, "Web Modules"),
        
        # Testes de serviços
        (TestPolicyService, "Services"),
        (TestRiskService, "Services"),
        (TestCoverageService, "Services"),
        (TestServiceIntegration, "Services"),
        
        # Testes de ML
        (TestModelPredictor, "ML Modules"),
        (TestFeatureEngineer, "ML Modules"), 
        (TestModelEvaluator, "ML Modules"),
        (TestMLPipeline, "ML Modules"),
        (TestCoverageRiskModels, "ML Modules"),
        (TestModelFiles, "ML Modules"),
        
        # Testes de banco
        (TestDatabaseConnection, "Database"),
        (TestCRUDOperations, "Database"),
        (TestCoverageRiskOperations, "Database"),
        (TestDatabaseIntegrity, "Database")
    ]
    
    start_time = time.time()
    
    # Executar cada suite
    for test_class, category in test_suites:
        try:
            run_test_suite(test_class, category, collector)
        except Exception as e:
            print(f"❌ Erro ao executar {test_class.__name__}: {e}")
            collector.add_result(category, test_class.__name__, 'ERROR', str(e))
    
    end_time = time.time()
    
    # Mostrar resumo final
    collector.print_summary()
    
    print(f"\n⏰ Tempo total de execução: {end_time - start_time:.2f}s")
    print(f"🏁 Testes finalizados em: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Retornar código de saída baseado nos resultados
    if collector.summary['failed'] > 0 or collector.summary['errors'] > 0:
        print("\n⚠️ Alguns testes falharam. Verifique os detalhes acima.")
        return 1
    else:
        print("\n🎉 Todos os testes executados com sucesso!")
        return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)