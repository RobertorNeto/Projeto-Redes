async def updatePeerList(client, peerList):

    # atualiza as entradas na lista de peers conhecidos para o cliente (remove as que se foram e adiciona novas)
    clientList = {}

    for peer in peerList:

        if peer["name"] == client.name and peer["namespace"] == client.namespace:
            continue

        # primeiro copia as entradas da lista no rendezvous
        peer_id = f"{peer['name']}@{peer['namespace']}"
        clientList[peer_id] = {"address": peer["ip"], "port": peer["port"], "status": "WAITING"}

        # caso o status do cliente encontrado seja distinto do que está no rendezvous, altera-o
        if peer_id in client.peersConnected:
            clientList[peer_id]["status"] = client.peersConnected[peer_id]["status"]

        # inicializa um timer = 0, na iteração 0 para o contador de backoff no caso de reconexão
        client.backoffTimer[peer_id] = [0, 0]

    # atualiza a lista do cliente
    client.peersConnected = clientList