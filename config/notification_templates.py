# notification_templates.py
# Centraliza os templates de mensagens de notificação

NOTIFICATION_TEMPLATES = {
    "sinistro_aberto": {
        "subject": "Sinistro aberto com sucesso",
        "body": "Olá {nome}, seu sinistro foi aberto com sucesso. Em breve entraremos em contato."
    },
    "sinistro_em_analise": {
        "subject": "Sinistro em análise",
        "body": "Olá {nome}, seu sinistro está em análise. Aguarde novas informações."
    },
    # Adicione outros tipos de notificação conforme necessário
}
