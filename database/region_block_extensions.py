"""Extensões futuras para o sistema de bloqueio por região (prefixo CEP).

Este arquivo serve como referência conceitual para evoluções planejadas:

1. Expiração de Bloqueios (valid_until)
   - Adicionar campos: valid_from (DATETIME), valid_until (DATETIME)
   - Regra de aplicação: bloquear somente se NOW BETWEEN valid_from AND valid_until
   - Handling de expirados: processo periódico que marca active=0 quando expirado

2. Origem do Bloqueio (source)
   - Campo source: 'manual' | 'auto'
   - 'auto' gerado por job de risco que avalia score médio da região
   - metadata JSON: {"score":82.4,"model_run":"2025-10-09-01"}

3. Cache em Memória
   - Carregar todos os prefixos ativos em dict
   - Invalidation: após create/remove/set_block_status
   - TTL simples: recarregar a cada N minutos

4. Intervalos de CEP (start_cep/end_cep)
   - Nova tabela region_blocks_ranges
   - Query: WHERE cep_digits BETWEEN start_cep AND end_cep
   - Combinar com prefixos (mais específico sempre ganha)

5. Geoespacial (futuro avançado)
   - Migrar para banco com suporte (PostGIS)
   - Polígonos para áreas de risco climático
   - Função: is_coord_blocked(latitude, longitude)

6. Observabilidade ampliada
   - Métricas Prometheus: blocked_attempts_total, active_blocks_gauge
   - Dashboard com apólices bloqueadas vs potenciais prêmios perdidos

7. API REST dedicada
   - Endpoint GET /region-blocks
   - POST /region-blocks {prefix, reason, severity}
   - PATCH /region-blocks/{prefix} {blocked:false}

8. Reavaliação automática
   - Job diário reprocessa scores e ajusta severidade
   - Se score < threshold de desbloqueio -> set_block_status(blocked=False)

9. Estrutura de auditoria
   - Tabela region_block_events(id, prefix, action, timestamp, user, old_values, new_values)
   - Registro em cada mudança crítica

10. Simulação e impacto
   - Calcular quantas apólices teriam sido emitidas sem bloqueio (impacto financeiro)
   - Relatório: bloqueios por severidade e duração média

Essas extensões NÃO estão implementadas, servem como orientação de roadmap.
"""
