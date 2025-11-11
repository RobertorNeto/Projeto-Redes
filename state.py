import asyncio
####    Memória de peers/rotas/mensagens deduplicadas   ####

# 1. Diagnóstico / Estatísticas
#   a) Peers conectados (n° e nome)
#   b) Rotas conhecidas (inbound, outbound)
#   c) Latência (RTT) e tempos de comunicação
#   OBS: Implementação de comandos para visualização dessas informações
#   d) Sobre 'metrics'
#       - Só disponível sob demanda, e quando ambas partes da comunicação suportarem a operação
#       - Requisitadas com uma mensagem METRICS_REQ, cuja resposta é um METRICS com os dados
#       - Dados sugeridos : 'rtts_ms', 'sent_count', 'recv_count', 'last_seen' (todos relativos ao emissor)

async def showPeers():
    return