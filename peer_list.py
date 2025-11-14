async def updatePeerList(client, peerList):

    # atualiza as entradas na lista de peers conhecidos para o cliente (remove as que se foram e adiciona novas)
    clientList = {}

    for peer in peerList:

        # primeiro copia as entradas da lista no rendezvous
        id = f"{peer["name"]}@{peer["namespace"]}"
        clientList[id] = {"address" : peer["ip"], "port" : peer["port"] ,"status" : "WAITING"}

        # caso o status do cliente encontrado seja distinto do que está no rendezvous, altera-o
        if id in client.peersConnected:
            clientList[id]["status"] = client.peersConnected[id]["status"]

        # inicializa um timer = 0, na iteração 0 para o contador de backoff no caso de reconexão
        client.backoffTimer[id] = [0,0]
    
    # atualiza a lista do cliente
    client.peersConnected = clientList