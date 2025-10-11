#!/usr/bin/env python3
"""
Gerenciador central para todos os modelos de predição de risco por cobertura.
Coordena análises de múltiplas coberturas e fornece relatórios consolidados.
"""

from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime
import numpy as np
import time
import sys
import os

# Adicionar path para DAO
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from .danos_eletricos import DanosEletricosPredictor
from .vendaval import VendavalPredictor
from .granizo import GranizoPredictor
from .alagamento import AlagamentoPredictor

# Importar DAO para persistência
try:
    from database.cobertura_risco_dao import CoberturaRiscoDAO, CoberturaRiscoData
    DAO_AVAILABLE = True
except ImportError as e:
    logger.warning(f"DAO não disponível: {e}")
    DAO_AVAILABLE = False

logger = logging.getLogger(__name__)

class CoverageRiskManager:
    """
    Gerenciador central para análise de risco por cobertura
    Implementa singleton para evitar múltiplas inicializações
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Implementação singleton"""
        if cls._instance is None:
            cls._instance = super(CoverageRiskManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Inicializa todos os modelos de cobertura (apenas uma vez)
        """
        # Evitar reinicialização
        if self._initialized:
            return
            
        self.predictors = {
            'danos_eletricos': DanosEletricosPredictor(),
            'vendaval': VendavalPredictor(),
            'granizo': GranizoPredictor(),
            'alagamento': AlagamentoPredictor()
        }
        
        # Carregar modelos salvos se disponíveis
        self._load_all_models()
        
        # Log apenas na primeira inicialização para reduzir verbosidade
        if not hasattr(CoverageRiskManager, '_first_init_logged'):
            logger.info(f"CoverageRiskManager inicializado com {len(self.predictors)} preditores")
            CoverageRiskManager._first_init_logged = True
        
        self._initialized = True
    
    def _load_all_models(self):
        """Carrega todos os modelos salvos"""
        # Controlar logging de carregamento para evitar spam
        if not hasattr(CoverageRiskManager, '_models_loaded_logged'):
            for name, predictor in self.predictors.items():
                try:
                    loaded = predictor.load_model()
                    if loaded:
                        logger.info(f"Modelo {name} carregado com sucesso")
                    else:
                        logger.info(f"Modelo {name} não encontrado - usando predição heurística")
                except Exception as e:
                    logger.warning(f"Erro ao carregar modelo {name}: {e}")
            CoverageRiskManager._models_loaded_logged = True
        else:
            # Carregamento silencioso nas próximas vezes
            for name, predictor in self.predictors.items():
                try:
                    predictor.load_model()
                except Exception:
                    pass  # Silencioso
    
    def analyze_all_coverages(self, policy_data: Dict, selected_coverages: List[str] = None, save_to_db: bool = True) -> Dict:
        """
        Analisa risco para todas as coberturas ou apenas as selecionadas
        
        Args:
            policy_data: Dados da apólice
            selected_coverages: Lista de coberturas a analisar (None = todas)
            save_to_db: Se deve salvar os resultados detalhados no banco
        
        Returns:
            Dicionário com análises por cobertura e resumo geral
        """
        analysis_start_time = time.time()
        
        if selected_coverages is None:
            selected_coverages = list(self.predictors.keys())
        
        results = {
            'policy_info': {
                'numero_apolice': policy_data.get('numero_apolice', 'N/A'),
                'cep': policy_data.get('cep', 'N/A'),
                'tipo_residencia': policy_data.get('tipo_residencia', 'N/A'),
                'valor_segurado': policy_data.get('valor_segurado', 0),
                'analysis_timestamp': datetime.now().isoformat()
            },
            'coverage_analysis': {},
            'summary': {},
            'recommendations': [],
            'has_specific_analysis': True
        }
        
        coverage_results = []
        all_recommendations = []
        riscos_para_salvar = []  # Lista para salvar no banco
        
        # Mapear coberturas para códigos (simplificado - idealmente buscar do banco)
        coverage_code_mapping = {
            'danos_eletricos': 1,
            'vendaval': 2,
            'granizo': 3,
            'alagamento': 4
        }
        
        # Analisar cada cobertura
        for coverage_key in selected_coverages:
            if coverage_key in self.predictors:
                try:
                    predictor_start_time = time.time()
                    predictor = self.predictors[coverage_key]
                    analysis = predictor.predict_risk(policy_data)
                    predictor_end_time = time.time()
                    processing_time_ms = int((predictor_end_time - predictor_start_time) * 1000)
                    
                    # Adicionar recomendações específicas se disponível
                    if hasattr(predictor, 'get_specific_recommendations'):
                        specific_recs = predictor.get_specific_recommendations(
                            analysis['risk_level'],
                            analysis['main_factors']
                        )
                        analysis['specific_recommendations'] = specific_recs
                        all_recommendations.extend(specific_recs)
                    
                    # Adicionar ajuste sazonal se disponível
                    if hasattr(predictor, 'calculate_seasonal_adjustment'):
                        seasonal_adj = predictor.calculate_seasonal_adjustment(datetime.now().month)
                        analysis['seasonal_adjustment'] = seasonal_adj
                        
                        # Aplicar ajuste sazonal ao score
                        adjusted_score = analysis['risk_score'] * seasonal_adj
                        analysis['adjusted_risk_score'] = min(adjusted_score, 100)
                        analysis['adjusted_risk_level'] = predictor._classify_risk_level(adjusted_score / 100)
                    
                    results['coverage_analysis'][coverage_key] = analysis
                    coverage_results.append(analysis)
                    
                    # Preparar dados para persistência
                    if save_to_db and DAO_AVAILABLE and policy_data.get('numero_apolice'):
                        try:
                            risco_data = CoberturaRiscoData(
                                nr_apolice=policy_data.get('numero_apolice'),
                                cd_cobertura=coverage_code_mapping.get(coverage_key, 0),
                                cd_produto=1,  # Default produto - idealmente buscar do contexto
                                score_risco=analysis['risk_score'],
                                nivel_risco=analysis['risk_level'],
                                probabilidade=analysis['probability'],
                                modelo_usado=coverage_key,
                                versao_modelo='1.0',
                                fatores_risco={
                                    'main_factors': analysis.get('main_factors', []),
                                    'seasonal_adjustment': analysis.get('seasonal_adjustment', 1.0)
                                },
                                dados_climaticos=analysis.get('climate_data', {}),
                                dados_propriedade=analysis.get('property_data', {}),
                                resultado_predicao=analysis,
                                confianca_modelo=analysis.get('confidence', 0.8),
                                tempo_processamento_ms=processing_time_ms
                            )
                            riscos_para_salvar.append(risco_data)
                        except Exception as e:
                            logger.warning(f"Erro ao preparar dados de {coverage_key} para persistência: {e}")
                    
                    logger.info(f"Análise de {coverage_key} concluída: {analysis['risk_level']}")
                    
                except Exception as e:
                    logger.error(f"Erro na análise de {coverage_key}: {e}")
                    # Análise de fallback
                    results['coverage_analysis'][coverage_key] = {
                        'coverage': coverage_key,
                        'probability': 0.5,
                        'risk_score': 50,
                        'risk_level': 'medio',
                        'error': str(e)
                    }
        
        # Salvar todos os riscos no banco em uma transação
        if save_to_db and DAO_AVAILABLE and riscos_para_salvar:
            try:
                dao = CoberturaRiscoDAO()
                saved_ids = dao.salvar_multiplos_riscos(riscos_para_salvar)
                results['persistence_info'] = {
                    'saved': True,
                    'records_saved': len(saved_ids),
                    'record_ids': saved_ids
                }
                logger.info(f"Salvos {len(saved_ids)} riscos detalhados no banco")
            except Exception as e:
                logger.error(f"Erro ao salvar riscos no banco: {e}")
                results['persistence_info'] = {
                    'saved': False,
                    'error': str(e)
                }
        
        # Gerar resumo geral
        results['summary'] = self._generate_summary(coverage_results)
        
        # Consolidar recomendações
        results['recommendations'] = list(set(all_recommendations))[:10]  # Top 10 únicas
        
        # Tempo total de processamento
        total_time = time.time() - analysis_start_time
        results['performance'] = {
            'total_time_seconds': round(total_time, 3),
            'coverages_analyzed': len(coverage_results)
        }
        
        return results
    
    def get_detailed_coverage_risks(self, nr_apolice: str, ultima_analise: bool = True) -> Dict:
        """
        Buscar riscos detalhados por cobertura salvos no banco
        
        Args:
            nr_apolice: Número da apólice
            ultima_analise: Se deve retornar apenas as análises mais recentes
            
        Returns:
            Dicionário com riscos detalhados por cobertura
        """
        if not DAO_AVAILABLE:
            return {'error': 'DAO não disponível', 'data': []}
        
        try:
            dao = CoberturaRiscoDAO()
            riscos = dao.buscar_riscos_por_apolice(nr_apolice, ultima_analise)
            
            # Reorganizar dados por cobertura
            coverage_risks = {}
            for risco in riscos:
                coverage_name = risco.get('nm_cobertura', f"Cobertura {risco['cd_cobertura']}")
                coverage_risks[coverage_name] = {
                    'id': risco['id'],
                    'codigo_cobertura': risco['cd_cobertura'],
                    'score_risco': risco['score_risco'],
                    'nivel_risco': risco['nivel_risco'],
                    'probabilidade': risco['probabilidade'],
                    'modelo_usado': risco['modelo_usado'],
                    'versao_modelo': risco['versao_modelo'],
                    'confianca_modelo': risco['confianca_modelo'],
                    'data_calculo': risco['data_calculo'],
                    'tempo_processamento_ms': risco['tempo_processamento_ms'],
                    'fatores_risco': risco.get('fatores_risco', {}),
                    'dados_climaticos': risco.get('dados_climaticos', {}),
                    'dados_propriedade': risco.get('dados_propriedade', {}),
                    'resultado_predicao': risco.get('resultado_predicao', {}),
                    'explicabilidade': risco.get('explicabilidade', {}),
                    'basica': risco.get('dv_basica', False)
                }
            
            # Calcular estatísticas
            scores = [risco['score_risco'] for risco in riscos]
            estatisticas = {
                'total_coberturas': len(riscos),
                'score_medio': sum(scores) / len(scores) if scores else 0,
                'score_maximo': max(scores) if scores else 0,
                'score_minimo': min(scores) if scores else 0,
                'coberturas_alto_risco': len([s for s in scores if s >= 70]),
                'data_ultima_analise': max([r['data_calculo'] for r in riscos]) if riscos else None
            }
            
            return {
                'success': True,
                'apolice': nr_apolice,
                'coverage_risks': coverage_risks,
                'estatisticas': estatisticas,
                'total_records': len(riscos)
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar riscos detalhados da apólice {nr_apolice}: {e}")
            return {'error': str(e), 'data': []}
    
    def get_coverage_ranking(self, limite: int = 10) -> Dict:
        """
        Obter ranking de coberturas por risco
        
        Args:
            limite: Número máximo de coberturas no ranking
            
        Returns:
            Dicionário com ranking de coberturas
        """
        if not DAO_AVAILABLE:
            return {'error': 'DAO não disponível', 'ranking': []}
        
        try:
            dao = CoberturaRiscoDAO()
            ranking = dao.buscar_ranking_coberturas(limite)
            
            return {
                'success': True,
                'ranking': ranking,
                'total_coberturas': len(ranking),
                'periodo': 'Últimos 30 dias'
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar ranking de coberturas: {e}")
            return {'error': str(e), 'ranking': []}
    
    def get_coverage_history(self, nr_apolice: str, cd_cobertura: int) -> Dict:
        """
        Obter histórico de análises de uma cobertura específica
        
        Args:
            nr_apolice: Número da apólice
            cd_cobertura: Código da cobertura
            
        Returns:
            Dicionário com histórico de análises
        """
        if not DAO_AVAILABLE:
            return {'error': 'DAO não disponível', 'historico': []}
        
        try:
            dao = CoberturaRiscoDAO()
            historico = dao.buscar_historico_risco(nr_apolice, cd_cobertura)
            
            # Calcular tendências
            if len(historico) >= 2:
                scores = [h['score_risco'] for h in historico]
                trend = 'crescente' if scores[0] > scores[-1] else 'decrescente' if scores[0] < scores[-1] else 'estavel'
                variacao_total = scores[0] - scores[-1]
            else:
                trend = 'indeterminado'
                variacao_total = 0
            
            return {
                'success': True,
                'apolice': nr_apolice,
                'cobertura': cd_cobertura,
                'historico': historico,
                'total_analises': len(historico),
                'tendencia': trend,
                'variacao_total_score': variacao_total
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar histórico da cobertura {cd_cobertura}: {e}")
            return {'error': str(e), 'historico': []}
    
    def _generate_summary(self, coverage_results: List[Dict]) -> Dict:
        """Gera resumo consolidado das análises"""
        if not coverage_results:
            return {
                'overall_risk_level': 'baixo',
                'average_risk_score': 0,
                'highest_risk_coverage': None,
                'total_coverages_analyzed': 0
            }
        
        # Calcular métricas gerais
        risk_scores = [result['risk_score'] for result in coverage_results]
        average_score = np.mean(risk_scores)
        max_score_idx = np.argmax(risk_scores)
        
        # Determinar nível de risco geral
        if average_score >= 70:
            overall_level = 'alto'
        elif average_score >= 40:
            overall_level = 'medio'
        elif average_score >= 20:
            overall_level = 'baixo'
        else:
            overall_level = 'muito_baixo'
        
        # Cobertura de maior risco
        highest_risk = coverage_results[max_score_idx]
        
        # Distribuição de riscos
        risk_distribution = {
            'alto': len([r for r in coverage_results if r['risk_score'] >= 70]),
            'medio': len([r for r in coverage_results if 40 <= r['risk_score'] < 70]),
            'baixo': len([r for r in coverage_results if 20 <= r['risk_score'] < 40]),
            'muito_baixo': len([r for r in coverage_results if r['risk_score'] < 20])
        }
        
        return {
            'overall_risk_level': overall_level,
            'average_risk_score': round(average_score, 1),
            'highest_risk_coverage': {
                'name': highest_risk['coverage'],
                'score': highest_risk['risk_score'],
                'level': highest_risk['risk_level']
            },
            'total_coverages_analyzed': len(coverage_results),
            'risk_distribution': risk_distribution,
            'critical_factors': self._identify_critical_factors(coverage_results)
        }
    
    def _identify_critical_factors(self, coverage_results: List[Dict]) -> List[str]:
        """Identifica fatores críticos comuns entre coberturas"""
        factor_counts = {}
        
        for result in coverage_results:
            main_factors = result.get('main_factors', [])
            for factor in main_factors[:3]:  # Top 3 de cada cobertura
                feature = factor['feature']
                if feature not in factor_counts:
                    factor_counts[feature] = 0
                factor_counts[feature] += factor['importance']
        
        # Ordenar por importância total
        sorted_factors = sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Retornar top 5 fatores críticos
        return [factor[0] for factor in sorted_factors[:5]]
    
    def get_coverage_comparison(self, policy_data: Dict, coverages: List[str]) -> Dict:
        """
        Compara riscos entre coberturas específicas
        
        Args:
            policy_data: Dados da apólice
            coverages: Lista de coberturas para comparar
        
        Returns:
            Comparação detalhada entre coberturas
        """
        analysis = self.analyze_all_coverages(policy_data, coverages)
        
        coverage_data = []
        for coverage, result in analysis['coverage_analysis'].items():
            coverage_data.append({
                'name': coverage,
                'display_name': result['coverage'],
                'risk_score': result['risk_score'],
                'risk_level': result['risk_level'],
                'probability': result['probability'],
                'main_factor': result['main_factors'][0]['feature'] if result['main_factors'] else 'N/A'
            })
        
        # Ordenar por risco (maior para menor)
        coverage_data.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return {
            'comparison': coverage_data,
            'summary': analysis['summary'],
            'policy_info': analysis['policy_info']
        }
    
    def get_weather_based_alerts(self, policy_data: Dict, alert_threshold: float = 0.7) -> List[Dict]:
        """
        Gera alertas baseados em condições climáticas atuais
        
        Args:
            policy_data: Dados da apólice
            alert_threshold: Limite de probabilidade para gerar alerta
        
        Returns:
            Lista de alertas por cobertura
        """
        alerts = []
        analysis = self.analyze_all_coverages(policy_data)
        
        for coverage, result in analysis['coverage_analysis'].items():
            if result['probability'] >= alert_threshold:
                alert = {
                    'coverage': result['coverage'],
                    'severity': 'ALTO' if result['probability'] >= 0.8 else 'MÉDIO',
                    'probability': result['probability'],
                    'risk_score': result['risk_score'],
                    'main_causes': [f['feature'] for f in result['main_factors'][:3]],
                    'recommendations': result.get('specific_recommendations', [])[:3],
                    'timestamp': datetime.now().isoformat()
                }
                alerts.append(alert)
        
        return sorted(alerts, key=lambda x: x['probability'], reverse=True)
    
    def batch_analyze_policies(self, policies_data: List[Dict]) -> Dict:
        """
        Analisa múltiplas apólices em lote
        
        Args:
            policies_data: Lista de dados de apólices
        
        Returns:
            Análise consolidada de todas as apólices
        """
        batch_results = {
            'total_policies': len(policies_data),
            'analysis_timestamp': datetime.now().isoformat(),
            'policy_results': [],
            'portfolio_summary': {},
            'high_risk_policies': []
        }
        
        all_coverages_results = []
        high_risk_threshold = 70
        
        for i, policy_data in enumerate(policies_data):
            try:
                policy_analysis = self.analyze_all_coverages(policy_data)
                batch_results['policy_results'].append({
                    'policy_id': policy_data.get('numero_apolice', f'Policy_{i+1}'),
                    'analysis': policy_analysis
                })
                
                # Coletar dados para análise de portfólio
                for coverage, result in policy_analysis['coverage_analysis'].items():
                    all_coverages_results.append({
                        'policy_id': policy_data.get('numero_apolice', f'Policy_{i+1}'),
                        'coverage': coverage,
                        'risk_score': result['risk_score'],
                        'risk_level': result['risk_level']
                    })
                
                # Identificar apólices de alto risco
                avg_score = policy_analysis['summary']['average_risk_score']
                if avg_score >= high_risk_threshold:
                    batch_results['high_risk_policies'].append({
                        'policy_id': policy_data.get('numero_apolice', f'Policy_{i+1}'),
                        'average_risk_score': avg_score,
                        'highest_risk_coverage': policy_analysis['summary']['highest_risk_coverage']
                    })
                    
            except Exception as e:
                logger.error(f"Erro na análise da apólice {i+1}: {e}")
        
        # Gerar resumo do portfólio
        batch_results['portfolio_summary'] = self._generate_portfolio_summary(all_coverages_results)
        
        return batch_results
    
    def _generate_portfolio_summary(self, all_results: List[Dict]) -> Dict:
        """Gera resumo do portfólio de apólices"""
        if not all_results:
            return {}
        
        # Análise por cobertura
        coverage_stats = {}
        for result in all_results:
            coverage = result['coverage']
            if coverage not in coverage_stats:
                coverage_stats[coverage] = []
            coverage_stats[coverage].append(result['risk_score'])
        
        # Calcular estatísticas por cobertura
        coverage_summary = {}
        for coverage, scores in coverage_stats.items():
            coverage_summary[coverage] = {
                'average_score': round(np.mean(scores), 1),
                'max_score': max(scores),
                'min_score': min(scores),
                'policies_count': len(scores),
                'high_risk_count': len([s for s in scores if s >= 70])
            }
        
        # Estatísticas gerais
        all_scores = [result['risk_score'] for result in all_results]
        
        return {
            'total_analyses': len(all_results),
            'average_portfolio_risk': round(np.mean(all_scores), 1),
            'coverage_breakdown': coverage_summary,
            'risk_distribution': {
                'alto': len([s for s in all_scores if s >= 70]),
                'medio': len([s for s in all_scores if 40 <= s < 70]),
                'baixo': len([s for s in all_scores if 20 <= s < 40]),
                'muito_baixo': len([s for s in all_scores if s < 20])
            }
        }
