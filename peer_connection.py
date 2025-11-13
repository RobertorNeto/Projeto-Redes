import asyncio
import json
import time
from logger import logger

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

async def sendHello(client, reader, writer):

    # carrega as informações de 'configs.json'
    with open("oconfigs.json", "r") as configsFile:
        configs = json.load(configsFile)
        jsonString = {"type" : "HELLO", "peer_id" : client, "version" : configs["version"], "features" : configs["features"]} + '\n'
        message = json.dump(jsonString)

        writer.write(message.encode('UTF-8'))
        await writer.drain()

        # espera o retorno por 10 segundos
        try:
            response = await asyncio.wait_for(reader.read(32000), timeout=10)

        except TimeoutError as error:
            logger.error(f"Não foi possível se conectar ao peer {client['name']}!", error)

        # fecha a conexão e espera o buffer
        writer.close()
        await writer.wait_closed()

        # decodifica a mensagem e atualiza o status do cliente
        responseMsg = response.decode('UTF-8')
        if responseMsg["status"] == "HELLO_OK":
           client.peersConnected[client]["status"] = "CONNECTED"

            # adicionar inbound connection
        else:
            return False
    return

async def sendHelloOk(client, reader, writer):
    
    # carrega as informações de 'configs.json'
    with open("oconfigs.json", "r") as configsFile:
        configs = json.load(configsFile)
    
    # prepara a mensagem json
    jsonString = {"type" : "HELLO_OK", "peer_id" : client, "version" : configs["version"], "features" : configs["features"]} + '\n'
    message = json.dump(jsonString)

    # abre a conexão e escreve a mensagem
    writer.write(message.encode('UTF-8'))
    await writer.drain()

async def listenToPeer(reader, peer_id, writer):
    
    # implementa a escuta por mensagens vindas de cada peer
    try:
        while True:
            data = await reader.readline()
            msg = json.loads(data.decode())
            logger.info(f"[{peer_id}] Mensagem recebida: {msg}")
            
            # responde ao HELLO com um HELLO_OK
            if (msg["type"] == "HELLO"):
                sendHelloOk(peer_id, reader, writer)
        
    except asyncio.CancelledError as error:
        logger.error(f"Task de {peer_id} cancelada.", error)