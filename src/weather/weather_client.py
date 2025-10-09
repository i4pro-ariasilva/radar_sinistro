"""
Cliente para integração com WeatherAPI.com
Fornece dados climáticos em tempo real com cache inteligente
"""

import requests
import time
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import logging

from .weather_data import WeatherData
from .weather_cache import WeatherCache

class WeatherClient:
    """Cliente para API do WeatherAPI.com"""
    
    def __init__(self, api_key: str, use_cache: bool = True, cache_duration_hours: int = 1):
        """
        Inicializar cliente WeatherAPI
        
        Args:
            api_key: Chave da API do WeatherAPI.com
            use_cache: Se deve usar cache local
            cache_duration_hours: Duração do cache em horas
        """
        self.api_key = api_key
        self.base_url = "https://api.weatherapi.com/v1"
        self.use_cache = use_cache
        self.cache = WeatherCache(cache_duration_hours=cache_duration_hours) if use_cache else None
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'RadarClimatico/1.0'})
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1  # 1 segundo entre requests
        
        self.logger = logging.getLogger(__name__)
    
    def _wait_rate_limit(self):
        """Aguardar intervalo mínimo entre requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fazer request para API com tratamento de erros
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros da request
            
        Returns:
            Resposta da API ou None em caso de erro
        """
        try:
            # Rate limiting
            self._wait_rate_limit()
            
            # Adicionar chave da API
            params['key'] = self.api_key
            
            url = f"{self.base_url}/{endpoint}"
            
            self.logger.debug(f"Fazendo request para: {url}")
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Verificar se há erro na resposta
            if 'error' in data:
                self.logger.error(f"Erro da API: {data['error']}")
                return None
            
            return data
            
        except requests.exceptions.Timeout:
            self.logger.error("Timeout na request para WeatherAPI")
            return None
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro na request: {e}")
            return None
        
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            return None
    
    def get_current_weather(self, location: str, include_air_quality: bool = False) -> Optional[WeatherData]:
        """
        Obter dados climáticos atuais
        
        Args:
            location: Localização (CEP, cidade, coordenadas lat,lon)
            include_air_quality: Se deve incluir dados de qualidade do ar
            
        Returns:
            Objeto WeatherData com dados atuais ou None em caso de erro
        """
        try:
            # Verificar cache primeiro
            if self.use_cache and self.cache:
                cached_data = self.cache.get(location, "current")
                if cached_data:
                    self.logger.debug(f"Dados encontrados no cache para: {location}")
                    return WeatherData.from_weatherapi_response(cached_data, location)
            
            # Fazer request para API
            params = {
                'q': location,
                'aqi': 'yes' if include_air_quality else 'no'
            }
            
            data = self._make_request('current.json', params)
            
            if not data:
                return None
            
            # Salvar no cache
            if self.use_cache and self.cache:
                self.cache.set(location, data, "current")
            
            # Criar objeto WeatherData
            weather_data = WeatherData.from_weatherapi_response(data, location)
            
            self.logger.info(f"Dados climáticos obtidos para: {location}")
            return weather_data
            
        except Exception as e:
            self.logger.error(f"Erro ao obter dados climáticos para {location}: {e}")
            return None
    
    def get_weather_by_cep(self, cep: str) -> Optional[WeatherData]:
        """
        Obter dados climáticos para um CEP brasileiro
        
        Args:
            cep: CEP no formato XXXXX-XXX ou XXXXXXXX
            
        Returns:
            Objeto WeatherData ou None em caso de erro
        """
        # Normalizar CEP
        cep_clean = cep.replace('-', '').replace(' ', '')
        
        if len(cep_clean) != 8:
            self.logger.error(f"CEP inválido: {cep}")
            return None
        
        # Usar CEP diretamente (WeatherAPI suporta CEPs brasileiros)
        return self.get_current_weather(f"{cep_clean}, Brazil")
    
    def get_weather_by_coordinates(self, latitude: float, longitude: float) -> Optional[WeatherData]:
        """
        Obter dados climáticos para coordenadas específicas
        
        Args:
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            Objeto WeatherData ou None em caso de erro
        """
        location = f"{latitude},{longitude}"
        return self.get_current_weather(location)
    
    def get_weather_for_multiple_locations(self, locations: List[str]) -> Dict[str, Optional[WeatherData]]:
        """
        Obter dados climáticos para múltiplas localizações
        
        Args:
            locations: Lista de localizações
            
        Returns:
            Dicionário com localização como chave e WeatherData como valor
        """
        results = {}
        
        for location in locations:
            self.logger.debug(f"Obtendo dados para: {location}")
            results[location] = self.get_current_weather(location)
            
            # Pequena pausa entre requests para não sobrecarregar API
            time.sleep(0.5)
        
        return results
    
    def get_weather_for_apolices(self, apolices: List[Any]) -> Dict[str, Optional[WeatherData]]:
        """
        Obter dados climáticos para uma lista de apólices
        
        Args:
            apolices: Lista de objetos apólice com atributo 'cep'
            
        Returns:
            Dicionário com CEP como chave e WeatherData como valor
        """
        results = {}
        processed_ceps = set()
        
        for apolice in apolices:
            cep = getattr(apolice, 'cep', None)
            
            if not cep or cep in processed_ceps:
                continue
            
            self.logger.debug(f"Obtendo dados climáticos para CEP: {cep}")
            weather_data = self.get_weather_by_cep(cep)
            results[cep] = weather_data
            processed_ceps.add(cep)
            
            # Pausa entre requests
            time.sleep(0.5)
        
        return results
    
    def test_connection(self) -> bool:
        """
        Testar conexão com a API
        
        Returns:
            True se conexão OK, False caso contrário
        """
        try:
            # Testar com uma localização conhecida
            data = self.get_current_weather("São Paulo, Brazil")
            return data is not None
            
        except Exception as e:
            self.logger.error(f"Erro no teste de conexão: {e}")
            return False
    
    def get_api_usage(self) -> Optional[Dict[str, Any]]:
        """
        Obter informações de uso da API (se disponível)
        
        Returns:
            Informações de uso da API ou None
        """
        # WeatherAPI não fornece endpoint específico para usage
        # Mas podemos fazer uma request simples para testar
        try:
            data = self._make_request('current.json', {'q': 'London'})
            
            if data:
                return {
                    'status': 'active',
                    'last_call': datetime.now().isoformat(),
                    'message': 'API funcionando normalmente'
                }
            else:
                return {
                    'status': 'error',
                    'last_call': datetime.now().isoformat(),
                    'message': 'Erro na comunicação com API'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'last_call': datetime.now().isoformat(),
                'message': f'Erro: {str(e)}'
            }
    
    def clear_cache(self) -> int:
        """
        Limpar cache de dados climáticos
        
        Returns:
            Número de arquivos removidos
        """
        if self.cache:
            return self.cache.clear()
        return 0
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Obter informações sobre o cache
        
        Returns:
            Informações do cache
        """
        if self.cache:
            return self.cache.get_cache_info()
        return {'message': 'Cache não habilitado'}
    
    def __str__(self) -> str:
        """Representação string do cliente"""
        return f"WeatherClient(api_key={'*' * 8}, cache={self.use_cache})"