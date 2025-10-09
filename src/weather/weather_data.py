"""
Modelo de dados climáticos
Estrutura padronizada para informações meteorológicas
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import json

@dataclass
class WeatherData:
    """Classe para representar dados climáticos padronizados"""
    
    # Informações básicas
    location: str
    latitude: float
    longitude: float
    timestamp: datetime
    
    # Dados climáticos atuais
    temperature_c: float
    temperature_f: float
    humidity_percent: int
    pressure_mb: float
    wind_speed_kph: float
    wind_direction: str
    wind_degree: int
    precipitation_mm: float
    visibility_km: float
    uv_index: float
    
    # Condições
    condition: str
    condition_code: int
    is_day: bool
    
    # Dados adicionais
    feels_like_c: float
    dew_point_c: Optional[float] = None
    heat_index_c: Optional[float] = None
    wind_chill_c: Optional[float] = None
    gust_kph: Optional[float] = None
    
    # Metadados
    source: str = "weatherapi"
    raw_data: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_weatherapi_response(cls, data: Dict[str, Any], location: str) -> 'WeatherData':
        """Criar WeatherData a partir da resposta da WeatherAPI"""
        
        current = data.get('current', {})
        location_data = data.get('location', {})
        
        return cls(
            location=location,
            latitude=location_data.get('lat', 0.0),
            longitude=location_data.get('lon', 0.0),
            timestamp=datetime.now(),
            
            temperature_c=current.get('temp_c', 0.0),
            temperature_f=current.get('temp_f', 0.0),
            humidity_percent=current.get('humidity', 0),
            pressure_mb=current.get('pressure_mb', 0.0),
            wind_speed_kph=current.get('wind_kph', 0.0),
            wind_direction=current.get('wind_dir', 'N'),
            wind_degree=current.get('wind_degree', 0),
            precipitation_mm=current.get('precip_mm', 0.0),
            visibility_km=current.get('vis_km', 0.0),
            uv_index=current.get('uv', 0.0),
            
            condition=current.get('condition', {}).get('text', 'Unknown'),
            condition_code=current.get('condition', {}).get('code', 0),
            is_day=current.get('is_day', 1) == 1,
            
            feels_like_c=current.get('feelslike_c', 0.0),
            dew_point_c=current.get('dewpoint_c'),
            heat_index_c=current.get('heatindex_c'),
            wind_chill_c=current.get('windchill_c'),
            gust_kph=current.get('gust_kph'),
            
            source="weatherapi",
            raw_data=data
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário"""
        return {
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'timestamp': self.timestamp.isoformat(),
            'temperature_c': self.temperature_c,
            'temperature_f': self.temperature_f,
            'humidity_percent': self.humidity_percent,
            'pressure_mb': self.pressure_mb,
            'wind_speed_kph': self.wind_speed_kph,
            'wind_direction': self.wind_direction,
            'wind_degree': self.wind_degree,
            'precipitation_mm': self.precipitation_mm,
            'visibility_km': self.visibility_km,
            'uv_index': self.uv_index,
            'condition': self.condition,
            'condition_code': self.condition_code,
            'is_day': self.is_day,
            'feels_like_c': self.feels_like_c,
            'dew_point_c': self.dew_point_c,
            'heat_index_c': self.heat_index_c,
            'wind_chill_c': self.wind_chill_c,
            'gust_kph': self.gust_kph,
            'source': self.source
        }
    
    def to_json(self) -> str:
        """Converter para JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def get_risk_score(self) -> float:
        """Calcular score de risco baseado nas condições climáticas"""
        risk_score = 0.0
        
        # Temperatura extrema
        if self.temperature_c < 0 or self.temperature_c > 40:
            risk_score += 0.3
        
        # Precipitação
        if self.precipitation_mm > 50:
            risk_score += 0.4
        elif self.precipitation_mm > 20:
            risk_score += 0.2
        
        # Vento forte
        if self.wind_speed_kph > 60:
            risk_score += 0.4
        elif self.wind_speed_kph > 30:
            risk_score += 0.2
        
        # Umidade extrema
        if self.humidity_percent > 90:
            risk_score += 0.1
        
        # UV alto
        if self.uv_index > 8:
            risk_score += 0.1
        
        # Pressão baixa (indicativo de tempestade)
        if self.pressure_mb < 1000:
            risk_score += 0.2
        
        return min(risk_score, 1.0)
    
    def get_risk_level(self) -> str:
        """Obter nível de risco textual"""
        score = self.get_risk_score()
        
        if score < 0.25:
            return "Baixo"
        elif score < 0.5:
            return "Médio"
        elif score < 0.75:
            return "Alto"
        else:
            return "Crítico"
    
    def get_condition_emoji(self) -> str:
        """Obter emoji baseado na condição climática"""
        condition_lower = self.condition.lower()
        
        if 'sun' in condition_lower or 'clear' in condition_lower:
            return "☀️"
        elif 'cloud' in condition_lower:
            return "☁️"
        elif 'rain' in condition_lower or 'drizzle' in condition_lower:
            return "🌧️"
        elif 'storm' in condition_lower or 'thunder' in condition_lower:
            return "⛈️"
        elif 'snow' in condition_lower:
            return "❄️"
        elif 'mist' in condition_lower or 'fog' in condition_lower:
            return "🌫️"
        elif 'wind' in condition_lower:
            return "💨"
        else:
            return "🌤️"
    
    def __str__(self) -> str:
        """Representação string legível"""
        emoji = self.get_condition_emoji()
        risk_level = self.get_risk_level()
        
        return f"{emoji} {self.location}: {self.temperature_c}°C, {self.condition}, Risco: {risk_level}"