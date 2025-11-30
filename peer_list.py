from logger import *

async def updatePeerList(client, peerList):
    """
    Atualiza a lista de peers locais baseada na resposta do servidor Rendezvous.
    CORREÇÃO: Atualiza o dicionário existente em vez de substituí-lo,
    preservando as conexões ativas (writers).
    """
    
    # Conjunto para rastrear quais peers vieram nesta atualização do servidor
    current_server_peers = set()

    for peer in peerList:
        # Pula a si mesmo
        if peer["name"] == client.name and peer["namespace"] == client.namespace:
            continue

        peer_id = f"{peer['name']}@{peer['namespace']}"
        current_server_peers.add(peer_id)

        # CENÁRIO 1: Peer já conhecido
        if peer_id in client.peersConnected:
            # Atualizamos IP e Porta caso tenham mudado (ex: reinício do peer)
            client.peersConnected[peer_id]["address"] = peer["ip"]
            client.peersConnected[peer_id]["port"] = peer["port"]
            
            # IMPORTANTE: NÃO alteramos o status se ele já estiver CONNECTED.
            # Isso preserva o objeto 'writer' e a conexão TCP ativa.
            
        # CENÁRIO 2: Novo Peer descoberto
        else:
            loggerInfo(f"Novo peer descoberto: {peer_id}")
            client.peersConnected[peer_id] = {
                "address": peer["ip"],
                "port": peer["port"],
                "status": "WAITING", # O clientLoop tentará conectar depois
                "writer": None
            }
            # Inicializa o backoff para este novo peer
            if hasattr(client, 'backoffTimer'):
                client.backoffTimer[peer_id] = [0, 0]

    # CENÁRIO 3: Limpeza (Garbage Collection)
    # Remove peers que estavam na memória local mas não vieram mais na lista do servidor.
    # Usamos list() para evitar erro de modificação durante iteração.
    local_peers = list(client.peersConnected.keys())
    
    for peer_id in local_peers:
        # Se o peer é do nosso namespace, mas não veio na lista do servidor...
        # (Verificação simples assumindo que o update é do mesmo namespace ou global)
        if peer_id not in current_server_peers:
            
            # Só removemos se NÃO estiver conectado. 
            # Se estiver conectado, mantemos a conexão viva (P2P direto) mesmo que o Rendezvous não o veja.
            if client.peersConnected[peer_id]["status"] != "CONNECTED":
                loggerDebug(f"Removendo peer obsoleto: {peer_id}")
                del client.peersConnected[peer_id]
                
                if hasattr(client, 'backoffTimer') and peer_id in client.backoffTimer:
                    del client.backoffTimer[peer_id]