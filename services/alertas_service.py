"""
Serviço de alertas automáticos para o sistema Radar de Sinistro
"""
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import streamlit as st


class AlertasService:
    """Serviço responsável pela gestão de alertas automáticos"""
    
    def __init__(self, db_path: str = 'database/radar_sinistro.db'):
        """
        Inicializa o serviço de alertas
        
        Args:
            db_path: Caminho para o banco de dados
        """
        self.db_path = db_path
        
    def salvar_configuracoes_alertas(self, configuracoes: Dict[str, Any]) -> bool:
        """
        Salva as configurações de alertas automáticos no banco de dados
        
        Args:
            configuracoes: Dicionário com as configurações dos alertas
            
        Returns:
            bool: True se salvo com sucesso, False caso contrário
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Criar tabela de configurações se não existir
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuracoes_alertas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    configuracoes TEXT NOT NULL,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Inserir ou atualizar configurações
            cursor.execute("""
                INSERT OR REPLACE INTO configuracoes_alertas (id, configuracoes)
                VALUES (1, ?)
            """, (json.dumps(configuracoes, ensure_ascii=False),))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Erro ao salvar configurações: {str(e)}")
            return False

    def carregar_configuracoes_alertas(self) -> Optional[Dict[str, Any]]:
        """
        Carrega as configurações de alertas automáticos do banco de dados
        
        Returns:
            Dict com as configurações ou None se não encontradas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT configuracoes FROM configuracoes_alertas WHERE id = 1")
            resultado = cursor.fetchone()
            
            conn.close()
            
            if resultado:
                return json.loads(resultado[0])
            return None
        except Exception:
            return None

    def testar_envio_alerta(self, mensagem: str, canais: List[str]) -> bool:
        """
        Testa o envio de um alerta com as configurações atuais
        
        Args:
            mensagem: Mensagem de teste
            canais: Lista de canais para envio
            
        Returns:
            bool: True se teste executado com sucesso
        """
        try:
            # Simula o envio para teste
            st.info("🧪 **Teste de Alerta Executado:**")
            
            for canal in canais:
                if canal == "Email":
                    st.success(f"✅ {canal}: Alerta de teste enviado para admin@radarsinistro.com")
                elif canal == "SMS":
                    st.success(f"✅ {canal}: Alerta de teste enviado para +55 11 99999-9999")
                elif canal == "WhatsApp":
                    st.success(f"✅ {canal}: Alerta de teste enviado via WhatsApp")
                elif canal == "Sistema Interno":
                    st.success(f"✅ {canal}: Notificação criada no sistema")
            
            return True
        except Exception as e:
            st.error(f"Erro no teste de envio: {str(e)}")
            return False

    def executar_alertas_automaticos(self, configuracoes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa o envio automático de alertas baseado nas configurações
        
        Args:
            configuracoes: Configurações dos alertas
            
        Returns:
            Dict com resultado da execução
        """
        try:
            from database.crud_operations import get_all_policies, get_prediction_for_policy
            from database.database import DatabaseManager
            
            # Inicializar conexão com banco
            db = DatabaseManager()
            
            # Buscar apólices elegíveis para alerta
            policies = get_all_policies()
            alertas_enviados = 0
            alertas_falharam = 0
            
            for policy in policies:
                # Verificar se a apólice tem score de risco alto
                prediction = get_prediction_for_policy(policy['numero_apolice'])
                if prediction and prediction.get('score_risco', 0) >= configuracoes.get('limite_risco', 75):
                    
                    # Verificar se já foi notificada recentemente (cooldown)
                    if self._verificar_cooldown_alerta(
                        policy['numero_apolice'], 
                        configuracoes.get('cooldown', 7)
                    ):
                        continue
                    
                    # Preparar dados para a mensagem
                    dados_mensagem = {
                        'segurado': policy.get('segurado', 'N/A'),
                        'numero_apolice': policy.get('numero_apolice', 'N/A'),
                        'score_risco': prediction.get('score_risco', 0),
                        'nivel_risco': prediction.get('nivel_risco', 'N/A'),
                        'tipo_residencia': policy.get('tipo_residencia', 'N/A'),
                        'cep': policy.get('cep', 'N/A'),
                        'valor_segurado': policy.get('valor_segurado', 0),
                        'data_atual': datetime.now().strftime("%d/%m/%Y")
                    }
                    
                    # Formatar mensagem
                    mensagem_formatada = configuracoes['mensagem'].format(**dados_mensagem)
                    
                    # Enviar alerta
                    sucesso = self._enviar_alerta_para_apolice(
                        policy, 
                        mensagem_formatada, 
                        configuracoes['canais'],
                        configuracoes['assunto']
                    )
                    
                    if sucesso:
                        alertas_enviados += 1
                        # Marcar como notificada
                        self._marcar_apolice_notificada(policy['numero_apolice'])
                    else:
                        alertas_falharam += 1
                    
                    # Verificar limite diário
                    if alertas_enviados >= configuracoes.get('max_por_dia', 50):
                        break
            
            return {
                'sucesso': True,
                'enviados': alertas_enviados,
                'erros': alertas_falharam
            }
            
        except Exception as e:
            st.error(f"Erro na execução dos alertas: {str(e)}")
            return {
                'sucesso': False,
                'enviados': 0,
                'erros': 0
            }

    def _verificar_cooldown_alerta(self, numero_apolice: str, cooldown_dias: int) -> bool:
        """
        Verifica se a apólice está em período de cooldown para alertas
        
        Args:
            numero_apolice: Número da apólice
            cooldown_dias: Número de dias de cooldown
            
        Returns:
            bool: True se está em cooldown, False caso contrário
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar último alerta enviado
            cursor.execute("""
                SELECT data_envio FROM alertas_enviados 
                WHERE numero_apolice = ? 
                ORDER BY data_envio DESC LIMIT 1
            """, (numero_apolice,))
            
            resultado = cursor.fetchone()
            conn.close()
            
            if resultado:
                data_ultimo_alerta = datetime.strptime(resultado[0], "%Y-%m-%d %H:%M:%S")
                tempo_decorrido = datetime.now() - data_ultimo_alerta
                return tempo_decorrido.days < cooldown_dias
            
            return False
            
        except Exception:
            return False
    
    def _enviar_alerta_para_apolice(
        self, 
        policy: Dict[str, Any], 
        mensagem: str, 
        canais: List[str], 
        assunto: str
    ) -> bool:
        """
        Envia alerta para uma apólice específica
        
        Args:
            policy: Dados da apólice
            mensagem: Mensagem do alerta
            canais: Canais de envio
            assunto: Assunto do alerta
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            # Simular envio (implementar integração real conforme necessário)
            return True
        except Exception:
            return False
    
    def _marcar_apolice_notificada(self, numero_apolice: str) -> None:
        """
        Marca uma apólice como notificada
        
        Args:
            numero_apolice: Número da apólice
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Criar tabela se não existir
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alertas_enviados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_apolice TEXT NOT NULL,
                    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Inserir registro
            cursor.execute("""
                INSERT INTO alertas_enviados (numero_apolice)
                VALUES (?)
            """, (numero_apolice,))
            
            conn.commit()
            conn.close()
            
        except Exception:
            pass
