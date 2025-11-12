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

async def showPeers(type, client):

    peers = {}

    # caso deseje-se saber todos os peers conectados, para cada cliente da lista, 
    # pega o id e separa em um dict, onde as chaves são os namespaces
    if type == "*":
        for peer in client.peersConnected:
            id = str(peer.split('@'))
            name, namespace = id[0], id[1]
            if namespace not in peers:
                peers[namespace] = [name]
            else:
                peers[namespace].append(name)

    # caso contrário, só pega os peers do namespace solicitado
    else:
        peers[namespace] = []
        for peer in client.peersConnected:
            id = str(peer.split('@'))
            name, namespace = id[0], id[1]
            if namespace == type[1:]:
                peers[namespace].append(name)

    # imprime os peers encontrados
    for nSpace in peers:
        print(f"# {nSpace} ({len(peers[nSpace])})")
        for p in peers[nSpace]:
            print(f"\t- {p}")
    return