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

async def showPeers(arg, client):

    peers = {}

    # caso deseje mostrar todos os peers
    if arg == "*":
        for peer_id in client.peersConnected:  # peer_id é a chave "nome@namespace"
            parts = peer_id.split('@')
            if len(parts) != 2:
                continue  # ignora ids malformados
            name, namespace = parts
            peers.setdefault(namespace, []).append(name)
    else:
        # espera formato '#namespace'
        if arg.startswith('#'):
            namespace = arg[1:]
        else:
            # se o usuário não colocar '#', assume que todo o argumento é o namespace
            namespace = arg
        peers[namespace] = []
        for peer_id in client.peersConnected:
            parts = peer_id.split('@')
            if len(parts) != 2:
                continue
            name, ns = parts
            if ns == namespace:
                peers[namespace].append(name)

    # imprime os peers encontrados
    for ns in peers:
        print(f"# {ns} ({len(peers[ns])})")
        for name in peers[ns]:
            print(f"\t- {name}")
    return

async def showConns(client):

    # imprime todas as conexões iniciadas pelo cliente (inbound) e recebidas pelo cliente (outbound)
    print(f"Inbound Connections ({len(client.inbound)})")
    for inbound in client.inbound:
        print(f"\t-{inbound}")

    print(f"Outbound Connections ({len(client.outbound)})")
    for outbound in client.outbound:
        print(f"\t-{outbound}")

async def updateRttTable(rtt, peerPair, client):
    return

async def showRtt(client):
    return