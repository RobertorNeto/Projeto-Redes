import asyncio
from logger import logger
import json
import time
import uuid

####    Gestão da camada TCP (HELLO, BYE, PING/PONG)    ####

# 1. Implementar conexão entre peers
#   a) Estabelecer e manter túneis de TCP persistentes (PING & PONG)
#       - Implementação de comandos de manutenção da conexão (HELLO / HELLO_OK, BYE/BYE_OK, PING, PONG)
#       - Implementação de comandos de comunicação (PUB, SUB)
#   b) Detectar falhas e realizar tentativas de reconexão
#       - Necessário handshake antes do início de qualquer comunicação, marcado por HELLO/HELLO_OK
#       - Tempo de espera entre passos do handshake = 10s
#   c) Implementar 'features' como campo do Handshake positivo entre peers, especificando:
#       - Possibilidade de ack
#       - Possibildiade de métricas
#       - Vazio, se nenhuma das acima se aplica

#   d) Quando do uso do BYE, o receptor deve:
#       - Guardar no log o encerramento solicitado
#       - responder com BYE_OK
#       - Encerrar a conexão e liberar os recursos

async def sendHello(client, reader, writer, peer):

    # carrega as informações de 'config.json'
    with open("config.json", "r") as configsFile:
        configs = json.load(configsFile)
        jsonString = {"type" : "HELLO", "peer_id" : f"{client.name}@{client.namespace}", "version" : configs["version"], "features" : configs["features"]}
        message = json.dumps(jsonString)

        writer.write(message.encode('UTF-8') + b'\n')
        await writer.drain()

        # espera o retorno por 10 segundos
        try:
            response = await asyncio.wait_for(reader.readline(), timeout=10)
            responseMsg = response.decode('UTF-8')
            responseMsg = responseMsg.strip()

            if responseMsg == '':
                logger.error(f"Resposta vazia do peer {peer}!")
                return
            
            # decodifica a mensagem e atualiza o status do cliente
            responseMsg = json.loads(responseMsg)

            if responseMsg["type"] == "HELLO_OK":
                client.peersConnected[peer]["status"] = "CONNECTED"

                # adiciona o peer conectado aos inbounds caso faça contato
                if responseMsg["peer_id"] not in client.inbound:
                    client.outbound.add(responseMsg["peer_id"])  

        except TimeoutError as error:
            logger.error(f"Não foi possível se conectar ao peer {client['name']}!", error)
            
        # fecha a conexão e espera o buffer
        writer.close()
        await writer.wait_closed()
    return

async def sendHelloOk(client, reader, writer):
    
    # carrega as informações de 'configs.json'
    with open("config.json", "r") as configsFile:
        configs = json.load(configsFile)
    
    # prepara a mensagem json
    jsonString = {"type" : "HELLO_OK", "peer_id" : client, "version" : configs["version"], "features" : configs["features"]}
    message = json.dumps(jsonString)

    # abre a conexão e escreve a mensagem
    writer.write(message.encode('UTF-8') + b'\n')
    await writer.drain()

async def listenToPeer(client, reader, peer_id, writer):
    
    # implementa a escuta por mensagens vindas de cada peer
        while True:
            data = await reader.readline()
            msg = (data.decode())
            msg = msg.strip()

            if msg == '':
                logger.warning(f"Resposta vazia do peer {peer_id}!")
                return
            
            msg = json.loads(msg)
            print(f"[{peer_id}] Mensagem recebida:", msg)
            
            # responde ao HELLO com um HELLO_OK e adiciona o peer à lista de inbounds do cliente
            if (msg["type"] == "HELLO"):
                sendHelloOk(peer_id, reader, writer)
                if msg["peer_id"] not in client.outbound:
                    client.inbound.add(msg["peer_id"])
            

async def pingPeers(client, reader, writer):

    # para cada entrada na lista de peers, envia um ping / pong caso o peer esteja disponível
    for peer in client.peersConnected:
        if peer["status"] == "CONNECTED":

            # ve se o emissor da mensagem requer um PING (outbound) ou PONG (inbound)
            if peer in client.outbound:
                currentTime = time.time()
                json_string = {"type" : "PING", "msg_id" : {str(uuid.UUID)}, "timestamp" : {currentTime}, "ttl" : 1}
                message = json.dumps(json_string)
                message = message.encode('UTF-8') + b'\n'

                try:
                    response = await asyncio.wait_for(reader.readline(), timeout=10)
                    response = response.decode('UTF-8')
                    response = response.strip()

                    # decodifica a mensagem e retorna o cálculo do RTT para atualização
                    response = json.loads(response)

                except TimeoutError as error:
                    logger.error(f"Não foi possível se conectar ao peer {client['name']}!", error)

    await asyncio.sleep(30)
    return