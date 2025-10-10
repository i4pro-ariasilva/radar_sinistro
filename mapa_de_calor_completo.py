"""
🗺️ MÓDULO COMPLETO DE MAPA DE CALOR - RADAR DE SINISTRO v4.0
Sistema Avançado de Visualização Geográfica de Riscos por CEP

MELHORIAS v4.0:
- Cache inteligente com TTL e compressão
- Geocodificação assíncrona e paralela
- Validação robusta de CEPs brasileiros
- Múltiplos provedores de geocodificação
- Analytics e métricas detalhadas
- Performance otimizada para grandes volumes
- Fallbacks inteligentes e recuperação de erros

Este módulo contém TODA a funcionalidade necessária para:
- Geocodificação de CEPs brasileiros (múltiplas APIs)
- Criação de mapas de calor interativos
- Visualização de riscos por região
- Cache inteligente para performance
- Analytics de uso e estatísticas

Autor: Sistema Radar de Sinistro v4.0
Data: Outubro 2025
"""

import os
import json
import time
import logging
import requests
import folium
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import hashlib
import gzip
import pickle
from typing import Optional, Tuple, Dict, Any, List, Union
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
import threading
import re


@dataclass
class GeocodingProvider:
    """Configuração de provedores de geocodificação"""
    name: str
    base_url: str
    format_url: str
    rate_limit: float = 1.0  # segundos entre requisições
    max_retries: int = 3
    timeout: int = 10
    active: bool = True
    
    def format_request(self, cep: str) -> str:
        """Formata URL da requisição para o CEP"""
        return self.format_url.format(cep=cep)


@dataclass
class CacheEntry:
    """Entrada do cache com metadados"""
    coordinates: Tuple[float, float]
    timestamp: datetime
    provider: str
    hit_count: int = 0
    
    def is_expired(self, ttl_hours: int = 24) -> bool:
        """Verifica se entrada está expirada"""
        return datetime.now() - self.timestamp > timedelta(hours=ttl_hours)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário serializável"""
        return {
            'coordinates': list(self.coordinates),
            'timestamp': self.timestamp.isoformat(),
            'provider': self.provider,
            'hit_count': self.hit_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Cria instância a partir de dicionário"""
        return cls(
            coordinates=tuple(data['coordinates']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            provider=data['provider'],
            hit_count=data.get('hit_count', 0)
        )


# Importações para melhorias v4.0
from pathlib import Path

# Verificar se plotly está disponível para analytics
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class CEPValidator:
    """Validador avançado de CEPs brasileiros"""
    
    def __init__(self):
        self.cep_pattern = re.compile(r'^\d{5}-?\d{3}$')
        self.state_ranges = self._load_state_ranges()
    
    def _load_state_ranges(self) -> Dict[str, List[Tuple[int, int]]]:
        """Carrega faixas de CEP por estado brasileiro"""
        return {
            'SP': [(1000, 19999)],
            'RJ': [(20000, 28999)],
            'ES': [(29000, 29999)],
            'MG': [(30000, 39999)],
            'BA': [(40000, 48999)],
            'SE': [(49000, 49999)],
            'PE': [(50000, 56999)],
            'AL': [(57000, 57999)],
            'PB': [(58000, 58999)],
            'RN': [(59000, 59999)],
            'CE': [(60000, 63999)],
            'PI': [(64000, 64999)],
            'MA': [(65000, 65999)],
            'PA': [(66000, 68999)],
            'AP': [(68900, 68999)],
            'AM': [(69000, 69999), (69400, 69899)],
            'RR': [(69300, 69399)],
            'AC': [(69900, 69999)],
            'DF': [(70000, 72799), (73000, 73699)],
            'GO': [(72800, 72999), (73700, 76999)],
            'TO': [(77000, 77999)],
            'MT': [(78000, 78899)],
            'RO': [(76800, 76999)],
            'MS': [(79000, 79999)],
            'PR': [(80000, 87999)],
            'SC': [(88000, 89999)],
            'RS': [(90000, 99999)]
        }
    
    def clean_cep(self, cep: str) -> str:
        """Remove formatação do CEP mantendo apenas números"""
        if not isinstance(cep, str):
            return ""
        return ''.join(filter(str.isdigit, cep))
    
    def format_cep(self, cep: str) -> str:
        """Formata CEP no padrão 12345-678"""
        clean = self.clean_cep(cep)
        if len(clean) == 8:
            return f"{clean[:5]}-{clean[5:]}"
        return clean
    
    def validate_cep(self, cep: str) -> Dict[str, Any]:
        """
        Validação completa de CEP brasileiro
        
        Returns:
            Dict com: is_valid, formatted_cep, state, errors
        """
        result = {
            'is_valid': False,
            'formatted_cep': '',
            'state': None,
            'errors': []
        }
        
        if not cep:
            result['errors'].append("CEP vazio")
            return result
        
        # Limpar e validar formato
        clean_cep = self.clean_cep(cep)
        
        if len(clean_cep) != 8:
            result['errors'].append(f"CEP deve ter 8 dígitos, encontrados {len(clean_cep)}")
            return result
        
        if not clean_cep.isdigit():
            result['errors'].append("CEP deve conter apenas números")
            return result
        
        # Formatar
        formatted = self.format_cep(clean_cep)
        result['formatted_cep'] = formatted
        
        # Validar faixa por estado
        cep_num = int(clean_cep)
        state = self._get_state_by_cep(cep_num)
        
        if state:
            result['is_valid'] = True
            result['state'] = state
        else:
            result['errors'].append(f"CEP {formatted} não corresponde a nenhum estado brasileiro")
        
        return result
    
    def _get_state_by_cep(self, cep_num: int) -> Optional[str]:
        """Determina estado baseado no número do CEP"""
        for state, ranges in self.state_ranges.items():
            for min_cep, max_cep in ranges:
                if min_cep <= cep_num <= max_cep:
                    return state
        return None


class AdvancedCache:
    """Cache avançado com TTL, compressão e analytics"""
    
    def __init__(self, cache_dir: str = "cache", ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / "geocoding_cache_v4.pkl.gz"
        self.ttl_hours = ttl_hours
        self.cache: Dict[str, CacheEntry] = {}
        self.stats = {
            'hits': 0,
            'misses': 0,
            'expired': 0,
            'saves': 0,
            'loads': 0
        }
        self._lock = threading.Lock()
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Carrega cache do disco com descompressão"""
        try:
            if self.cache_file.exists():
                with gzip.open(self.cache_file, 'rb') as f:
                    data = pickle.load(f)
                    self.cache = {
                        k: CacheEntry.from_dict(v) if isinstance(v, dict) else v
                        for k, v in data.items()
                    }
                self.stats['loads'] += 1
                self._cleanup_expired()
        except Exception as e:
            logging.warning(f"Erro ao carregar cache: {e}")
            self.cache = {}
    
    def _save_cache(self) -> None:
        """Salva cache no disco com compressão"""
        try:
            self.cache_dir.mkdir(exist_ok=True)
            
            # Converter para formato serializável
            data = {k: v.to_dict() for k, v in self.cache.items()}
            
            with gzip.open(self.cache_file, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            self.stats['saves'] += 1
        except Exception as e:
            logging.warning(f"Erro ao salvar cache: {e}")
    
    def _cleanup_expired(self) -> None:
        """Remove entradas expiradas do cache"""
        expired_keys = [
            k for k, v in self.cache.items() 
            if v.is_expired(self.ttl_hours)
        ]
        
        for key in expired_keys:
            del self.cache[key]
            self.stats['expired'] += 1
    
    def get(self, key: str) -> Optional[Tuple[float, float]]:
        """Recupera coordenadas do cache"""
        with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                if not entry.is_expired(self.ttl_hours):
                    entry.hit_count += 1
                    self.stats['hits'] += 1
                    return entry.coordinates
                else:
                    del self.cache[key]
                    self.stats['expired'] += 1
            
            self.stats['misses'] += 1
            return None
    
    def set(self, key: str, coordinates: Tuple[float, float], provider: str) -> None:
        """Armazena coordenadas no cache"""
        with self._lock:
            entry = CacheEntry(
                coordinates=coordinates,
                timestamp=datetime.now(),
                provider=provider
            )
            self.cache[key] = entry
            
            # Salvar a cada 10 novas entradas
            if len(self.cache) % 10 == 0:
                self._save_cache()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        total_requests = self.stats['hits'] + self.stats['misses']
        
        return {
            'total_entries': len(self.cache),
            'total_requests': total_requests,
            'hit_rate': (self.stats['hits'] / max(total_requests, 1)) * 100,
            'expired_entries': self.stats['expired'],
            'cache_size_mb': self.cache_file.stat().st_size / 1024 / 1024 if self.cache_file.exists() else 0,
            **self.stats
        }
    
    def cleanup(self) -> int:
        """Limpa cache expirado manualmente"""
        initial_size = len(self.cache)
        self._cleanup_expired()
        self._save_cache()
        return initial_size - len(self.cache)
class OSMGeocoder:
    """
    Geocodificador Avançado v4.0 usando Multiple Providers
    
    MELHORIAS v4.0:
    - Múltiplos provedores com fallback automático
    - Cache inteligente com TTL e compressão
    - Validação robusta de CEPs brasileiros
    - Geocodificação paralela para melhor performance
    - Analytics detalhadas de uso
    - Rate limiting inteligente por provedor
    - Recuperação automática de falhas
    """
    
    def __init__(self, cache_dir: str = "cache", parallel_workers: int = 3):
        """
        Inicializa o geocodificador avançado
        
        Args:
            cache_dir: Diretório para cache
            parallel_workers: Número de workers para processamento paralelo
        """
        # Configurar provedores múltiplos
        self.providers = self._setup_providers()
        self.current_provider_idx = 0
        
        # Componentes avançados
        self.validator = CEPValidator()
        self.cache = AdvancedCache(cache_dir)
        self.parallel_workers = parallel_workers
        
        # Configurar session HTTP otimizada
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RadarSinistro/4.0 (sistema.radar@empresa.com)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # Estatísticas avançadas
        self.stats = {
            'total_requests': 0,
            'successful_geocoding': 0,
            'failed_geocoding': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'validation_errors': 0,
            'provider_usage': {p.name: 0 for p in self.providers},
            'response_times': [],
            'error_types': {}
        }
        
        # Thread safety
        self._lock = threading.Lock()
    
    def _setup_providers(self) -> List[GeocodingProvider]:
        """Configura múltiplos provedores de geocodificação"""
        return [
            GeocodingProvider(
                name="OpenStreetMap",
                base_url="https://nominatim.openstreetmap.org",
                format_url="https://nominatim.openstreetmap.org/search?q={cep}, Brasil&format=json&countrycodes=br&limit=1&addressdetails=1",
                rate_limit=1.0,
                timeout=10
            ),
            GeocodingProvider(
                name="OSM_Mirror",
                base_url="https://nominatim.osm.org",
                format_url="https://nominatim.osm.org/search?q={cep}, Brasil&format=json&countrycodes=br&limit=1",
                rate_limit=0.8,
                timeout=8
            ),
            GeocodingProvider(
                name="MapQuest_OSM",
                base_url="https://open.mapquestapi.com",
                format_url="https://open.mapquestapi.com/nominatim/v1/search.php?q={cep}, Brasil&format=json&countrycodes=br&limit=1",
                rate_limit=0.5,
                timeout=12
            )
        ]
    
    def _get_next_provider(self) -> GeocodingProvider:
        """Retorna próximo provedor ativo com load balancing"""
        active_providers = [p for p in self.providers if p.active]
        
        if not active_providers:
            # Reativar todos se nenhum estiver ativo
            for p in self.providers:
                p.active = True
            active_providers = self.providers
        
        provider = active_providers[self.current_provider_idx % len(active_providers)]
        self.current_provider_idx += 1
        
        return provider
    
    def _record_error(self, error_type: str, provider_name: Optional[str] = None) -> None:
        """Registra erro para analytics"""
        with self._lock:
            self.stats['error_types'][error_type] = self.stats['error_types'].get(error_type, 0) + 1
            if provider_name and error_type == 'api_error':
                # Marcar provedor como temporariamente inativo após muitos erros
                provider = next((p for p in self.providers if p.name == provider_name), None)
                if provider:
                    error_count = self.stats['error_types'].get(f'{provider_name}_errors', 0)
                    if error_count > 5:  # Após 5 erros, desativar temporariamente
                        provider.active = False
    
    def _geocode_single_with_provider(self, cep: str, provider: GeocodingProvider) -> Optional[Tuple[float, float]]:
        """Geocodifica CEP usando provedor específico"""
        try:
            start_time = time.time()
            
            url = provider.format_request(cep)
            response = self.session.get(url, timeout=provider.timeout)
            response.raise_for_status()
            
            response_time = time.time() - start_time
            self.stats['response_times'].append(response_time)
            
            data = response.json()
            
            if data and len(data) > 0:
                result = data[0]
                lat = float(result['lat'])
                lon = float(result['lon'])
                
                coords = (lat, lon)
                
                # Salvar no cache
                self.cache.set(cep, coords, provider.name)
                
                # Estatísticas
                with self._lock:
                    self.stats['provider_usage'][provider.name] += 1
                    self.stats['api_calls'] += 1
                    self.stats['successful_geocoding'] += 1
                
                return coords
            
            return None
            
        except Exception as e:
            self._record_error('api_error', provider.name)
            return None
        
        finally:
            # Rate limiting por provedor
            time.sleep(provider.rate_limit)
    
    def geocode_cep(self, cep: str) -> Optional[Tuple[float, float]]:
        """
        Geocodifica CEP com validação e múltiplos provedores
        
        Args:
            cep: CEP no formato "12345-678" ou "12345678"
            
        Returns:
            Tupla (latitude, longitude) ou None se não encontrado
        """
        with self._lock:
            self.stats['total_requests'] += 1
        
        # Validar CEP
        validation = self.validator.validate_cep(cep)
        if not validation['is_valid']:
            with self._lock:
                self.stats['validation_errors'] += 1
            return None
        
        clean_cep = validation['formatted_cep']
        
        # Verificar cache primeiro
        cached_result = self.cache.get(clean_cep)
        if cached_result:
            with self._lock:
                self.stats['cache_hits'] += 1
            return cached_result
        
        # Tentar com múltiplos provedores
        for attempt in range(len(self.providers)):
            provider = self._get_next_provider()
            
            coords = self._geocode_single_with_provider(clean_cep, provider)
            if coords:
                return coords
        
        # Se chegou aqui, falhou com todos os provedores
        with self._lock:
            self.stats['failed_geocoding'] += 1
        
        return None
    
    def geocode_batch(self, ceps: List[str], show_progress: bool = True) -> Dict[str, Optional[Tuple[float, float]]]:
        """
        Geocodifica múltiplos CEPs em paralelo
        
        Args:
            ceps: Lista de CEPs para geocodificar
            show_progress: Mostrar barra de progresso no Streamlit
            
        Returns:
            Dicionário {cep: (lat, lon)} ou {cep: None}
        """
        results = {}
        
        # Filtrar CEPs únicos válidos
        unique_ceps = list(set(ceps))
        valid_ceps = []
        
        for cep in unique_ceps:
            validation = self.validator.validate_cep(cep)
            if validation['is_valid']:
                valid_ceps.append(validation['formatted_cep'])
            else:
                results[cep] = None
        
        if not valid_ceps:
            return results
        
        # Configurar barra de progresso
        progress_bar = None
        status_text = None
        
        if show_progress and hasattr(st, 'progress'):
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        # Processar em paralelo
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            # Submeter todas as tarefas
            future_to_cep = {
                executor.submit(self.geocode_cep, cep): cep 
                for cep in valid_ceps
            }
            
            completed = 0
            total = len(valid_ceps)
            
            # Coletar resultados conforme completam
            for future in as_completed(future_to_cep):
                cep = future_to_cep[future]
                
                try:
                    result = future.result()
                    results[cep] = result
                except Exception as e:
                    results[cep] = None
                    self._record_error('batch_error')
                
                completed += 1
                
                # Atualizar progresso
                if progress_bar is not None and status_text is not None:
                    progress = completed / total
                    progress_bar.progress(progress)
                    status_text.text(f"Geocodificado: {completed}/{total} CEPs")
        
        # Limpar interface de progresso
        if progress_bar is not None and status_text is not None:
            progress_bar.empty()
            status_text.empty()
        
        return results
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas completas do geocodificador"""
        cache_stats = self.cache.get_stats()
        
        total_requests = self.stats['total_requests']
        success_rate = (self.stats['successful_geocoding'] / max(total_requests, 1)) * 100
        
        avg_response_time = (
            sum(self.stats['response_times']) / len(self.stats['response_times'])
            if self.stats['response_times'] else 0
        )
        
        return {
            'geocoding_stats': {
                'total_requests': total_requests,
                'successful_geocoding': self.stats['successful_geocoding'],
                'failed_geocoding': self.stats['failed_geocoding'],
                'success_rate': success_rate,
                'validation_errors': self.stats['validation_errors']
            },
            'performance_stats': {
                'avg_response_time_ms': avg_response_time * 1000,
                'cache_hit_rate': cache_stats['hit_rate'],
                'api_calls': self.stats['api_calls'],
                'cache_hits': self.stats['cache_hits']
            },
            'provider_stats': {
                'provider_usage': self.stats['provider_usage'],
                'active_providers': [p.name for p in self.providers if p.active],
                'total_providers': len(self.providers)
            },
            'cache_stats': cache_stats,
            'error_stats': self.stats['error_types']
        }
    
    def cleanup_cache(self) -> Dict[str, int]:
        """Limpa cache expirado"""
        removed = self.cache.cleanup()
        return {
            'removed_entries': removed,
            'remaining_entries': len(self.cache.cache)
        }
    
    def reset_providers(self) -> None:
        """Reativa todos os provedores"""
        for provider in self.providers:
            provider.active = True
        self.current_provider_idx = 0


class MapaCalorRiscos:
    """
    Gerador de Mapas de Calor para Visualização de Riscos
    
    Funcionalidades:
    - Mapas interativos com Folium
    - Classificação visual por níveis de risco
    - Popups informativos por região
    - Legenda automática
    - Múltiplas camadas de visualização
    """
    
    def __init__(self, geocoder: Optional[OSMGeocoder] = None):
        """
        Inicializa o gerador de mapas
        
        Args:
            geocoder: Instância do geocodificador (opcional)
        """
        self.geocoder = geocoder or OSMGeocoder()
        
        # Configurações de risco
        self.risk_levels = {
            'muito_baixo': {'min': 0, 'max': 25, 'color': '#388e3c', 'label': 'Muito Baixo'},
            'baixo': {'min': 25, 'max': 50, 'color': '#fbc02d', 'label': 'Baixo'},
            'medio': {'min': 50, 'max': 75, 'color': '#f57c00', 'label': 'Médio'},
            'alto': {'min': 75, 'max': 100, 'color': '#d32f2f', 'label': 'Alto'}
        }
        
        # Configurações do mapa
        self.map_config = {
            'center_brazil': [-15.7942, -47.8822],
            'default_zoom': 5,
            'tiles': ['OpenStreetMap', 'CartoDB positron'],
            'popup_width': 300,
            'min_marker_size': 8,
            'max_marker_size': 25
        }
    
    def _get_risk_config(self, score: float) -> Dict[str, Any]:
        """
        Retorna configuração de cor e label baseada no score de risco
        
        Args:
            score: Score de risco (0-100)
            
        Returns:
            Dicionário com configurações do risco
        """
        for level, config in self.risk_levels.items():
            if config['min'] <= score < config['max']:
                return config
        
        # Fallback para scores >= 100
        return self.risk_levels['alto']
    
    def _calculate_marker_size(self, count: int, max_count: int) -> int:
        """
        Calcula tamanho do marcador baseado na quantidade de apólices
        
        Args:
            count: Número de apólices no CEP
            max_count: Máximo de apólices em qualquer CEP
            
        Returns:
            Tamanho do marcador em pixels
        """
        min_size = self.map_config['min_marker_size']
        max_size = self.map_config['max_marker_size']
        
        if max_count <= 1:
            return min_size
        
        normalized = (count - 1) / (max_count - 1)
        return int(min_size + (max_size - min_size) * normalized)
    
    def _create_popup_html(self, cep: str, data: Dict[str, Any]) -> str:
        """
        Cria HTML personalizado para popup do marcador
        
        Args:
            cep: CEP da região
            data: Dados agregados do CEP
            
        Returns:
            HTML formatado para popup
        """
        risk_config = self._get_risk_config(data['risk_score'])
        
        html = f"""
        <div style='min-width: 250px; font-family: Arial, sans-serif;'>
            <h4 style='margin: 0 0 10px 0; color: #1e3c72; border-bottom: 2px solid #1e3c72; padding-bottom: 5px;'>
                📍 CEP: {cep}
            </h4>
            
            <div style='margin: 8px 0;'>
                <span style='font-weight: bold; color: {risk_config["color"]};'>🎯 Nível de Risco:</span><br>
                <span style='color: {risk_config["color"]}; font-size: 16px; font-weight: bold;'>
                    {data['risk_score']:.1f} - {risk_config["label"]}
                </span>
            </div>
            
            <div style='margin: 8px 0;'>
                <span style='font-weight: bold; color: #424242;'>📋 Apólices:</span><br>
                <span style='font-size: 16px;'>{data['policy_count']} apólices cadastradas</span>
            </div>
            
            <div style='margin: 8px 0;'>
                <span style='font-weight: bold; color: #424242;'>💰 Valor Total:</span><br>
                <span style='font-size: 16px; color: #2e7d32;'>R$ {data['total_value']:,.0f}</span>
            </div>
            
            <div style='margin: 8px 0;'>
                <span style='font-weight: bold; color: #424242;'>📊 Valor Médio:</span><br>
                <span style='font-size: 14px;'>R$ {data['avg_value']:,.0f} por apólice</span>
            </div>
        </div>
        """
        
        return html
    
    def _create_legend_html(self) -> str:
        """
        Cria HTML da legenda do mapa
        
        Returns:
            HTML formatado para legenda
        """
        legend_items = []
        
        for level, config in self.risk_levels.items():
            legend_items.append(
                f"<p style='margin: 3px 0;'>"
                f"<span style='color:{config['color']}; font-size: 16px; font-weight: bold;'>●</span> "
                f"{config['label']} ({config['min']}-{config['max']})"
                f"</p>"
            )
        
        html = f"""
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 220px; height: 140px; 
                    background-color: white; border: 2px solid grey; z-index: 9999; 
                    font-size: 14px; padding: 10px; box-shadow: 0 0 15px rgba(0,0,0,0.2);
                    border-radius: 5px;">
            <h4 style='margin: 0 0 10px 0; color: #1e3c72; text-align: center;'>
                🎯 Classificação de Risco
            </h4>
            {''.join(legend_items)}
        </div>
        """
        
        return html
    
    def criar_mapa_calor(self, policies_df: pd.DataFrame) -> str:
        """
        Cria mapa de calor interativo baseado nos dados das apólices
        
        Args:
            policies_df: DataFrame com colunas: cep, risk_score, insured_value
            
        Returns:
            HTML do mapa para renderização no Streamlit
        """
        if policies_df.empty:
            return self._create_empty_map_html()
        
        # Validar colunas necessárias
        required_columns = ['cep', 'risk_score', 'insured_value']
        missing_columns = [col for col in required_columns if col not in policies_df.columns]
        
        if missing_columns:
            st.error(f"Colunas obrigatórias faltando: {missing_columns}")
            return self._create_empty_map_html()
        
        # Agregar dados por CEP
        cep_data = self._aggregate_data_by_cep(policies_df)
        
        if cep_data.empty:
            return self._create_empty_map_html()
        
        # Criar mapa base
        mapa = self._create_base_map()
        
        # Adicionar marcadores
        success_count = self._add_markers_to_map(mapa, cep_data)
        
        # Adicionar legenda
        legend_html = self._create_legend_html()
        mapa.get_root().add_child(folium.Element(legend_html))
        
        # Adicionar controle de camadas
        folium.LayerControl().add_to(mapa)
        
        # Exibir estatísticas no Streamlit
        self._show_geocoding_stats(len(cep_data), success_count)
        
        return mapa._repr_html_()
    
    def _aggregate_data_by_cep(self, policies_df: pd.DataFrame) -> pd.DataFrame:
        """Agrega dados das apólices por CEP"""
        try:
            # Limpar dados
            df_clean = policies_df.dropna(subset=['cep', 'risk_score', 'insured_value'])
            df_clean = df_clean[df_clean['cep'] != '']
            
            # Converter tipos
            df_clean['risk_score'] = pd.to_numeric(df_clean['risk_score'], errors='coerce')
            df_clean['insured_value'] = pd.to_numeric(df_clean['insured_value'], errors='coerce')
            
            # Remover valores inválidos
            df_clean = df_clean.dropna(subset=['risk_score', 'insured_value'])
            
            # Agregar por CEP
            cep_aggregated = df_clean.groupby('cep').agg({
                'risk_score': 'mean',
                'insured_value': ['sum', 'mean', 'count']
            }).round(2)
            
            # Flatten colunas
            cep_aggregated.columns = ['risk_score', 'total_value', 'avg_value', 'policy_count']
            cep_aggregated = cep_aggregated.reset_index()
            
            return cep_aggregated
            
        except Exception as e:
            st.error(f"Erro ao agregar dados: {e}")
            return pd.DataFrame()
    
    def _create_base_map(self) -> folium.Map:
        """Cria mapa base do Brasil"""
        mapa = folium.Map(
            location=self.map_config['center_brazil'],
            zoom_start=self.map_config['default_zoom'],
            tiles=self.map_config['tiles'][0]
        )
        
        # Adicionar tiles alternativos
        for tile_name in self.map_config['tiles'][1:]:
            folium.TileLayer(tile_name, name=tile_name).add_to(mapa)
        
        return mapa
    
    def _get_fallback_coordinates(self) -> Dict[str, Tuple[float, float]]:
        """Coordenadas fixas para CEPs verificados como fallback"""
        return {
            # São Paulo
            '01310-100': (-23.5615, -46.6563),  # Av. Paulista
            '04038-001': (-23.5933, -46.6831),  # Vila Olímpia
            
            # Rio de Janeiro
            '20040-020': (-22.9068, -43.1729),  # Centro RJ
            '22071-900': (-22.9711, -43.1822),  # Copacabana
            
            # Belo Horizonte
            '30112-000': (-19.9167, -43.9345),  # Centro BH
            '31270-901': (-19.9394, -43.9381),  # Savassi
            
            # Curitiba
            '80010-000': (-25.4284, -49.2733),  # Centro Curitiba
            '80230-130': (-25.4419, -49.2769),  # Batel
            
            # Porto Alegre
            '90010-150': (-30.0346, -51.2177),  # Centro POA
            '91040-001': (-29.9927, -51.1786),  # Zona Norte
            
            # Outras capitais
            '40070-110': (-12.9714, -38.5014),  # Salvador
            '50030-230': (-8.0476, -34.8770),   # Recife
            '60160-230': (-3.7172, -38.5433),   # Fortaleza
            '70040-010': (-15.7942, -47.8822),  # Brasília
            '69020-160': (-3.1190, -60.0217),   # Manaus
            '66000-000': (-1.4558, -48.5044),   # Belém
            '88000-000': (-27.5954, -48.5480),  # Florianópolis
            '29000-000': (-20.3155, -40.3128),  # Vitória
            '73000-000': (-16.6864, -49.2643),  # Goiânia
            '78000-000': (-15.6014, -56.0979),  # Cuiabá
        }
    
    def _add_markers_to_map(self, mapa: folium.Map, cep_data: pd.DataFrame) -> int:
        """Adiciona marcadores ao mapa com fallback para coordenadas fixas"""
        success_count = 0
        max_policies = cep_data['policy_count'].max()
        
        # Obter coordenadas de fallback - CORRIGIR AQUI
        fallback_coords = self._get_fallback_coordinates()  # Adicionar self.
        
        # Primeira tentativa: geocodificação normal
        ceps_to_geocode = cep_data['cep'].tolist()
        
        #st.info("🔄 Tentando geocodificação online...")
        geocoding_results = self.geocoder.geocode_batch(ceps_to_geocode, show_progress=True)
        
        # Verificar sucessos da geocodificação online
        online_sucessos = sum(1 for v in geocoding_results.values() if v is not None)
        
        if online_sucessos == 0:
            #st.warning("⚠️ Geocodificação online falhou. Usando coordenadas de fallback...")
            
            # Usar coordenadas de fallback
            for _, row in cep_data.iterrows():
                cep = row['cep']
                
                # Tentar fallback primeiro
                coords = fallback_coords.get(cep)
                
                if coords:
                    success_count += 1
                    risk_config = self._get_risk_config(row['risk_score'])
                    marker_size = self._calculate_marker_size(row['policy_count'], max_policies)
                    
                    popup_html = self._create_popup_html(cep, row.to_dict())
                    
                    folium.CircleMarker(
                        location=coords,
                        radius=marker_size,
                        popup=folium.Popup(popup_html, max_width=self.map_config['popup_width']),
                        tooltip=f"CEP {cep} - Risco: {row['risk_score']:.1f} (Fallback)",
                        color=risk_config['color'],
                        fillColor=risk_config['color'],
                        fillOpacity=0.7,
                        weight=2
                    ).add_to(mapa)
                else:
                    # CEP não tem fallback - usar coordenada genérica do centro do Brasil
                    coords = (-15.7942, -47.8822)  # Brasília
                    success_count += 1
                    
                    risk_config = self._get_risk_config(row['risk_score'])
                    marker_size = self._calculate_marker_size(row['policy_count'], max_policies)
                    
                    popup_html = self._create_popup_html(cep, row.to_dict())
                    
                    folium.CircleMarker(
                        location=coords,
                        radius=marker_size,
                        popup=folium.Popup(popup_html, max_width=self.map_config['popup_width']),
                        tooltip=f"CEP {cep} - Risco: {row['risk_score']:.1f} (Genérico)",
                        color=risk_config['color'],
                        fillColor=risk_config['color'],
                        fillOpacity=0.6,
                        weight=1
                    ).add_to(mapa)
            
            # Adicionar aviso no mapa
            #if success_count > 0:
            #    st.success(f"✅ Mapa gerado com coordenadas de fallback para {success_count} CEPs")
            #    st.info("ℹ️ **Modo Fallback:** Usando coordenadas conhecidas devido a falha na geocodificação online")
        
        else:
            # Usar resultados da geocodificação online
            for _, row in cep_data.iterrows():
                coords = geocoding_results.get(row['cep'])
                
                if coords:
                    success_count += 1
                    risk_config = self._get_risk_config(row['risk_score'])
                    marker_size = self._calculate_marker_size(row['policy_count'], max_policies)
                    
                    popup_html = self._create_popup_html(row['cep'], row.to_dict())
                    
                    folium.CircleMarker(
                        location=coords,
                        radius=marker_size,
                        popup=folium.Popup(popup_html, max_width=self.map_config['popup_width']),
                        tooltip=f"CEP {row['cep']} - Risco: {row['risk_score']:.1f}",
                        color=risk_config['color'],
                        fillColor=risk_config['color'],
                        fillOpacity=0.7,
                        weight=2
                    ).add_to(mapa)
        
        return success_count
    
    def _create_empty_map_html(self) -> str:
        """Retorna HTML para mapa vazio"""
        return """
        <div style='text-align: center; padding: 50px; background: #f5f5f5; border-radius: 10px;'>
            <h3 style='color: #666;'>🗺️ Mapa não disponível</h3>
            <p style='color: #888;'>
                Nenhuma apólice com CEP válido encontrada.<br>
                Adicione apólices em 'Gerenciar Apólices' para visualizar o mapa.
            </p>
        </div>
        """
    
    def _show_geocoding_stats(self, total_ceps: int, geocoded_ceps: int) -> None:
        """Exibe estatísticas de geocodificação no Streamlit"""
        failed_ceps = total_ceps - geocoded_ceps
        
        if failed_ceps > 0:
            st.info(
                f"📊 **Geocodificação:** {geocoded_ceps} sucessos, {failed_ceps} falhas "
                f"({geocoded_ceps/total_ceps*100:.1f}% de sucesso)"
            )
        
        # Mostrar estatísticas avançadas do geocodificador v4.0
        stats = self.geocoder.get_comprehensive_stats()
        
        if stats['geocoding_stats']['total_requests'] > 0:
            # Métricas de performance
            perf_stats = stats['performance_stats']
            st.caption(
                f"⚡ **Performance:** {perf_stats['cache_hit_rate']:.1f}% cache hits, "
                f"{perf_stats['avg_response_time_ms']:.0f}ms tempo médio de resposta"
            )
            
            # Informações dos provedores
            provider_stats = stats['provider_stats']
            active_providers = provider_stats['active_providers']
            st.caption(f"🌐 **Provedores ativos:** {', '.join(active_providers)}")
            
            # Botão para analytics detalhadas
            if st.button("📊 Ver Analytics Detalhadas", key="analytics_btn"):
                self._show_detailed_analytics(stats)
    
    def _show_detailed_analytics(self, stats: Dict[str, Any]) -> None:
        """Exibe analytics detalhadas em expander"""
        with st.expander("📈 Analytics Detalhadas do Geocodificador v4.0", expanded=True):
            
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Taxa de Sucesso",
                    f"{stats['geocoding_stats']['success_rate']:.1f}%",
                    delta=None
                )
            
            with col2:
                st.metric(
                    "Cache Hit Rate", 
                    f"{stats['performance_stats']['cache_hit_rate']:.1f}%",
                    delta=None
                )
            
            with col3:
                st.metric(
                    "Tempo Médio",
                    f"{stats['performance_stats']['avg_response_time_ms']:.0f}ms",
                    delta=None
                )
            
            with col4:
                st.metric(
                    "Entradas no Cache",
                    f"{stats['cache_stats']['total_entries']:,}",
                    delta=None
                )
            
            # Gráficos de uso por provedor
            if stats['provider_stats']['provider_usage']:
                st.subheader("📊 Uso por Provedor")
                
                provider_df = pd.DataFrame([
                    {'Provedor': name, 'Uso': count}
                    for name, count in stats['provider_stats']['provider_usage'].items()
                    if count > 0
                ])
                
                if not provider_df.empty:
                    import plotly.express as px
                    fig = px.pie(
                        provider_df, 
                        values='Uso', 
                        names='Provedor',
                        title="Distribuição de Uso por Provedor"
                    )
                    st.plotly_chart(fig, width='stretch')
            
            # Informações do cache
            st.subheader("💾 Informações do Cache")
            cache_info = stats['cache_stats']
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Tamanho do cache:** {cache_info['cache_size_mb']:.2f} MB")
                st.write(f"**Entradas expiradas:** {cache_info['expired_entries']}")
            
            with col2:
                st.write(f"**Total de hits:** {cache_info['hits']:,}")
                st.write(f"**Total de misses:** {cache_info['misses']:,}")
            
            # Limpeza de cache
            if st.button("🧹 Limpar Cache Expirado"):
                with st.spinner("Limpando cache..."):
                    cleanup_result = self.geocoder.cleanup_cache()
                    st.success(
                        f"✅ Cache limpo! Removidas {cleanup_result['removed_entries']} entradas. "
                        f"Restam {cleanup_result['remaining_entries']} entradas."
                    )


def criar_interface_streamlit(policies_df: Optional[pd.DataFrame] = None) -> None:
    """Cria interface completa do mapa no Streamlit v4.0"""
    
    # Header principal
    st.header("🗺️ Mapa de Calor - Distribuição de Riscos por CEP")
    st.markdown(
        "Visualização geográfica interativa dos riscos de sinistros "
        "baseada nos CEPs das apólices cadastradas."
    )
    
    # Controles principais
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.info("🎯 **Mapa Interativo v4.0:** Performance otimizada com geocodificação paralela")
    
    with col2:
        show_analytics = st.checkbox("📊 Analytics", value=False, help="Mostrar métricas detalhadas")
    
    with col3:
        # NOVA OPÇÃO: Usar dados de exemplo
        usar_exemplo = st.checkbox("🧪 Dados Exemplo", value=True, help="Usar dados de exemplo em vez dos dados reais")
    
    with col4:
        if st.button("🔄 Atualizar", width='stretch'):
            st.rerun()
    
    # LÓGICA SIMPLES: Decidir qual fonte de dados usar
    if usar_exemplo:
        # Usuário optou por dados de exemplo
        st.info("🧪 **Modo Exemplo Ativado:** Usando dados de teste com CEPs verificados")
        policies_df = _gerar_dados_exemplo()
        
    elif policies_df is None or len(policies_df) == 0:
        # Não há dados do app.py, usar exemplo como fallback
        st.warning("📊 Nenhum dado recebido do sistema. Usando dados de exemplo.")
        policies_df = _gerar_dados_exemplo()
        
    elif policies_df['cep'].nunique() == 1:
        # Detectou problema nos dados (só 1 CEP), sugerir exemplo
        cep_unico = policies_df['cep'].iloc[0]
        st.warning(f"⚠️ Detectado apenas 1 CEP único nos dados: {cep_unico}")
        
        col_suggest1, col_suggest2 = st.columns(2)
        with col_suggest1:
            st.markdown("**Opções:**")
            st.markdown("1. ✅ Marque '🧪 Dados Exemplo' acima")
            st.markdown("2. 📋 Adicione mais apólices no sistema")
        
        with col_suggest2:
            if st.button("🔄 Usar Exemplo Automaticamente"):
                usar_exemplo = True
                st.rerun()
    
    # Usar dados conforme decidido
    if policies_df.empty:
        st.warning("📭 Nenhuma apólice encontrada")
        return
    
    # Mostrar informação sobre fonte dos dados
    if usar_exemplo:
        st.success(f"🧪 **Dados de Exemplo:** {len(policies_df)} apólices, {policies_df['cep'].nunique()} CEPs únicos")
    else:
        st.info(f"📊 **Dados do Sistema:** {len(policies_df)} apólices, {policies_df['cep'].nunique()} CEPs únicos")
    
    # Resto da função continua exatamente igual...
    _exibir_metricas_resumo(policies_df)
    
    # Filtros avançados v4.0 (opcionais)
    if show_analytics:
        st.markdown("### 🎛️ Controles Avançados")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            risk_filter = st.selectbox(
                "Filtrar por Risco",
                ["Todos", "Alto (75+)", "Médio (50-75)", "Baixo (<50)"],
                help="Filtrar apólices por nível de risco"
            )
        
        with col2:
            value_filter = st.selectbox(
                "Filtrar por Valor",
                ["Todos", "Até 200k", "200k-500k", "500k+"],
                help="Filtrar por valor segurado"
            )
        
        with col3:
            map_style = st.selectbox(
                "Estilo do Mapa",
                ["OpenStreetMap", "CartoDB Positron", "CartoDB Dark Matter"],
                help="Escolher estilo visual do mapa"
            )
    else:
        # Valores padrão quando analytics não está ativo
        risk_filter = "Todos"
        value_filter = "Todos"
        map_style = "OpenStreetMap"
    
    # Aplicar filtros
    if risk_filter != "Todos":
        if "Alto" in risk_filter:
            policies_df = policies_df[policies_df['risk_score'] >= 75]
        elif "Médio" in risk_filter:
            policies_df = policies_df[(policies_df['risk_score'] >= 50) & (policies_df['risk_score'] < 75)]
        elif "Baixo" in risk_filter:
            policies_df = policies_df[policies_df['risk_score'] < 50]

    if value_filter != "Todos":
        if "Até 200k" in value_filter:
            policies_df = policies_df[policies_df['insured_value'] <= 200000]
        elif "200k-500k" in value_filter:
            policies_df = policies_df[(policies_df['insured_value'] > 200000) & (policies_df['insured_value'] <= 500000)]
        elif "500k+" in value_filter:
            policies_df = policies_df[policies_df['insured_value'] > 500000]
    
    if policies_df.empty:
        st.warning("⚠️ Nenhuma apólice corresponde aos filtros selecionados")
        return
    
    # Gerar e exibir mapa
    st.markdown("---")
    
    with st.spinner("🔄 Gerando mapa de calor v4.0..."):
        try:
            geocoder = OSMGeocoder(parallel_workers=5)
            mapa_generator = MapaCalorRiscos(geocoder)
            
            # ✅ CORREÇÃO: Mapear estilo ANTES de gerar mapa
            style_mapping = {
                "OpenStreetMap": "OpenStreetMap",
                "CartoDB Positron": "CartoDB positron", 
                "CartoDB Dark Matter": "CartoDB dark_matter"
            }
            
            folium_style = style_mapping.get(map_style, "OpenStreetMap")
            mapa_generator.map_config['tiles'] = [folium_style]
            
            mapa_html = mapa_generator.criar_mapa_calor(policies_df)
            
            components.html(mapa_html, height=650, scrolling=False)
            
            #st.success(f"✅ Mapa v4.0 gerado com sucesso para {len(policies_df)} apólices")
            
            #if show_analytics:
            #    stats = geocoder.get_comprehensive_stats()
                
                #with st.expander("📊 Métricas de Performance v4.0"):
                #    col1, col2, col3 = st.columns(3)
                #    
                #    with col1:
                #        st.metric("Taxa de Sucesso", f"{stats['geocoding_stats']['success_rate']:.1f}%")
                #    
                #    with col2:
                #        st.metric("Cache Hit Rate", f"{stats['performance_stats']['cache_hit_rate']:.1f}%")
                #    
                #    with col3:
                #        st.metric("Tempo Médio", f"{stats['performance_stats']['avg_response_time_ms']:.0f}ms")
                #    
                #    st.write("**Provedores Ativos:**", ", ".join(stats['provider_stats']['active_providers']))
            
        except Exception as e:
            st.error(f"❌ Erro ao gerar mapa: {e}")
            _exibir_fallback_tabela(policies_df)


def _gerar_dados_exemplo() -> pd.DataFrame:
    """Gera dados de exemplo para demonstração - INDEPENDENTE do app.py"""
    import numpy as np
    
    # Seed fixo para resultados consistentes
    np.random.seed(12345)
    
    # CEPs verificados que têm coordenadas de fallback
    ceps_verificados = [
        '01310-100', '04038-001', '20040-020', '22071-900', '30112-000',
        '31270-901', '80010-000', '80230-130', '90010-150', '91040-001',
        '40070-110', '50030-230', '60160-230', '70040-010', '69020-160',
        '66000-000', '88000-000', '29000-000', '73000-000', '78000-000'
    ]
    
    # Garantir distribuição pelos CEPs
    dados = []
    
    # Pelo menos 1 apólice por CEP
    for cep in ceps_verificados:
        dados.append({
            'cep': cep,
            'risk_score': np.random.uniform(10, 90),
            'insured_value': np.random.uniform(100000, 800000),
            'policy_id': f'EXEMPLO-{len(dados)+1:04d}'
        })
    
    # Apólices adicionais aleatórias
    for i in range(30):
        cep = np.random.choice(ceps_verificados)
        dados.append({
            'cep': cep,
            'risk_score': np.random.uniform(10, 90),
            'insured_value': np.random.uniform(100000, 800000),
            'policy_id': f'EXEMPLO-{len(dados)+1:04d}'
        })
    
    return pd.DataFrame(dados)


def _exibir_metricas_resumo(policies_df: pd.DataFrame) -> None:
    """Exibe métricas resumidas dos dados"""
    st.markdown("### 📊 Resumo dos Dados")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_policies = len(policies_df)
    unique_ceps = policies_df['cep'].nunique()
    avg_risk = policies_df['risk_score'].mean()
    high_risk_ceps = len(policies_df[policies_df['risk_score'] >= 75]['cep'].unique())
    
    with col1:
        st.metric("📋 Total de Apólices", f"{total_policies:,}")
    
    with col2:
        st.metric("📍 CEPs Únicos", f"{unique_ceps:,}")
    
    with col3:
        st.metric("🎯 Risco Médio", f"{avg_risk:.1f}")
    
    with col4:
        st.metric("🔴 CEPs Alto Risco", f"{high_risk_ceps:,}")


def _exibir_fallback_tabela(policies_df: pd.DataFrame) -> None:
    """Exibe dados em tabela como alternativa ao mapa"""
    st.markdown("### 📊 Dados das Apólices (Visualização Alternativa)")
    
    # Agregar dados por CEP
    summary_df = policies_df.groupby('cep').agg({
        'risk_score': 'mean',
        'insured_value': ['sum', 'count']
    }).round(2)
    
    # Flatten colunas
    summary_df.columns = ['risk_medio', 'valor_total', 'num_apolices']
    summary_df = summary_df.reset_index()
    
    # Adicionar classificação de risco
    def classify_risk(score):
        if score >= 75: return '🔴 Alto'
        elif score >= 50: return '🟡 Médio'
        elif score >= 25: return '🔵 Baixo'
        else: return '🟢 Muito Baixo'
    
    summary_df['nivel_risco'] = summary_df['risk_medio'].apply(classify_risk)
    
    # Ordenar por risco
    summary_df = summary_df.sort_values('risk_medio', ascending=False)
    
    # Exibir tabela
    st.dataframe(
        summary_df[['cep', 'nivel_risco', 'risk_medio', 'num_apolices', 'valor_total']],
        column_config={
            'cep': 'CEP',
            'nivel_risco': 'Nível de Risco',
            'risk_medio': 'Score Médio',
            'num_apolices': 'Nº Apólices',
            'valor_total': 'Valor Total (R$)'
        },
        width='stretch'
    )


# Função principal para teste standalone
def main():
    """Função principal para executar o módulo como aplicação standalone"""
    st.set_page_config(
        page_title="Mapa de Calor - Radar de Sinistro",
        page_icon="🗺️",
        layout="wide"
    )
    
    st.title("🗺️ Módulo de Mapa de Calor - Radar de Sinistro")
    st.markdown("---")
    
    # Interface principal
    criar_interface_streamlit()
    
    # Informações técnicas
    with st.expander("ℹ️ Informações Técnicas"):
        st.markdown("""
        ### 🔧 Funcionalidades:
        - **Geocodificação**: Conversão automática de CEPs em coordenadas
        - **Cache Inteligente**: Armazena resultados para melhor performance
        - **Mapas Interativos**: Visualização com Folium e OpenStreetMap
        - **Classificação Visual**: Cores representam níveis de risco
        - **Popups Informativos**: Detalhes completos por região
        
        ### 📋 Dados Necessários:
        - `cep`: CEP da propriedade (formato: "12345-678")
        - `risk_score`: Score de risco (0-100)
        - `insured_value`: Valor segurado (numérico)
        
        ### 🎯 Classificação de Riscos:
        - **🟢 Muito Baixo**: 0-25
        - **🔵 Baixo**: 25-50  
        - **🟡 Médio**: 50-75
        - **🔴 Alto**: 75-100
        """)


if __name__ == "__main__":
    main()
