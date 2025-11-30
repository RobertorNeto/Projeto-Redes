from logger import *

async def updatePeerList(client, peerList):
    
    current_server_peers = set()

    for peer in peerList:
        if peer["name"] == client.name and peer["namespace"] == client.namespace:
            continue

        peer_id = f"{peer['name']}@{peer['namespace']}"
        current_server_peers.add(peer_id)

        if peer_id in client.peersConnected:
            client.peersConnected[peer_id]["address"] = peer["ip"]
            client.peersConnected[peer_id]["port"] = peer["port"]
            
        else:
            loggerInfo(f"Novo peer descoberto: {peer_id}")
            client.peersConnected[peer_id] = {
                "address": peer["ip"],
                "port": peer["port"],
                "status": "WAITING",
                "writer": None
            }
            if hasattr(client, 'backoffTimer'):
                client.backoffTimer[peer_id] = [0, 0]

    local_peers = list(client.peersConnected.keys())
    
    for peer_id in local_peers:
        if peer_id not in current_server_peers:
            if client.peersConnected[peer_id]["status"] != "CONNECTED":
                loggerDebug(f"Removendo peer obsoleto: {peer_id}")
                del client.peersConnected[peer_id]
                
                if hasattr(client, 'backoffTimer') and peer_id in client.backoffTimer:
                    del client.backoffTimer[peer_id]