"""
Módulo para geração automática de relatórios climáticos
Separado da interface Streamlit para permitir uso em scripts
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path

def auto_generate_weather_reports():
    """
    Função para gerar relatórios climáticos automaticamente
    Esta função pode ser chamada periodicamente para salvar relatórios
    """
    try:
        from src.weather.weather_cache import WeatherCache
        
        # Inicializar cache
        cache = WeatherCache()
        
        # Obter dados
        weather_df = cache.export_to_dataframe(include_expired=False)
        
        if weather_df is None or weather_df.empty:
            return False, "Nenhum dado disponível"
        
        # Criar diretório de relatórios automáticos
        reports_dir = Path("data/reports/auto")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Gerar relatório
        weather_stats = cache.get_summary_statistics()
        
        # Criar relatório resumido
        auto_report = {
            'timestamp': datetime.now().isoformat(),
            'total_records': len(weather_df),
            'unique_locations': weather_df['location'].nunique() if 'location' in weather_df else 0,
            'date_range': {
                'start': str(weather_df['timestamp'].min()) if 'timestamp' in weather_df and not weather_df['timestamp'].isna().all() else None,
                'end': str(weather_df['timestamp'].max()) if 'timestamp' in weather_df and not weather_df['timestamp'].isna().all() else None
            },
            'statistics': weather_stats,
            'top_locations': weather_df['location'].value_counts().head(5).to_dict() if 'location' in weather_df else {},
            'risk_summary': {
                'high_risk_count': len(weather_df[weather_df.get('risk_score', 0) > 7]) if 'risk_score' in weather_df else 0,
                'medium_risk_count': len(weather_df[(weather_df.get('risk_score', 0) >= 4) & (weather_df.get('risk_score', 0) <= 7)]) if 'risk_score' in weather_df else 0,
                'low_risk_count': len(weather_df[weather_df.get('risk_score', 0) < 4]) if 'risk_score' in weather_df else 0
            }
        }
        
        # Salvar relatório automático
        report_file = reports_dir / f"weather_auto_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(auto_report, f, ensure_ascii=False, indent=2)
        
        # Salvar dados detalhados em CSV
        csv_file = reports_dir / f"weather_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        weather_df.to_csv(csv_file, index=False, encoding='utf-8')
        
        return True, f"Relatórios salvos: {report_file.name}, {csv_file.name}"
        
    except Exception as e:
        return False, f"Erro ao gerar relatório automático: {e}"

def get_weather_cache_summary():
    """
    Obter resumo dos dados em cache
    """
    try:
        from src.weather.weather_cache import WeatherCache
        
        cache = WeatherCache()
        stats = cache.get_summary_statistics()
        
        return {
            'success': True,
            'total_records': stats.get('total_records', 0),
            'unique_locations': stats.get('unique_locations', 0),
            'weather_stats': stats.get('weather_stats', {}),
            'date_range': stats.get('date_range', {}),
            'message': f"Cache contém {stats.get('total_records', 0)} registros"
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f"Erro ao acessar cache: {e}"
        }

def cleanup_expired_cache():
    """
    Limpar dados expirados do cache
    """
    try:
        from src.weather.weather_cache import WeatherCache
        
        cache = WeatherCache()
        removed = cache.cleanup_expired()
        
        return {
            'success': True,
            'removed_files': removed,
            'message': f"Removidos {removed} arquivos expirados"
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f"Erro ao limpar cache: {e}"
        }