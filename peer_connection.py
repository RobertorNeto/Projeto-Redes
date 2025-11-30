import asyncio
from datetime import datetime
from logger import logger
import json
import time
import uuid

from client import Client

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

async def sendHello(client: Client, reader, writer, peer_id: str):

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
                logger.error(f"Resposta vazia do peer {peer_id}!")
                return
            
            # decodifica a mensagem e atualiza o status do cliente
            responseMsg = json.loads(responseMsg)

            if responseMsg["type"] == "HELLO_OK":
                client.peersConnected[peer_id]["status"] = "CONNECTED"
                client.outbound.add(responseMsg["peer_id"])  

        except TimeoutError as error:
            logger.error(f"Não foi possível completar HELLO com {peer_id}", error)
    return

async def sendHelloOk(peer_id: str, reader, writer):
    
    # carrega as informações de 'configs.json'
    with open("config.json", "r") as configsFile:
        configs = json.load(configsFile)
    
    # prepara a mensagem json
    jsonString = {"type" : "HELLO_OK", "peer_id" : peer_id, "version" : configs["version"], "features" : configs["features"]}
    message = json.dumps(jsonString)

    # abre a conexão e escreve a mensagem
    writer.write(message.encode('UTF-8') + b'\n')
    await writer.drain()

async def listenToPeer(client: Client, reader, peer_id: str, writer):
    
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
                await sendHelloOk(peer_id, reader, writer)
                if msg["peer_id"] not in client.outbound:
                    client.inbound.add(msg["peer_id"])
                    
            elif msg["type"] == "SEND":
                print(f"\n[DM de {msg['src']}]: {msg['payload']}")
                
                # Se exige ACK, envia resposta
                if msg.get("require_ack", False):
                    ack_packet = {
                        "type": "ACK",
                        "msg_id": msg["msg_id"], # Repete o ID da mensagem original
                        "timestamp": datetime.now().isoformat(),
                        "ttl": 1
                    }
                    writer.write((json.dumps(ack_packet) + '\n').encode('UTF-8'))
                    await writer.drain()
                    logger.debug(f"ACK enviado para {msg['src']} (msg_id: {msg['msg_id']})")

            # --- Tratamento de PUB (Recebendo broadcast) ---
            elif msg["type"] == "PUB":
                print(f"\n[PUB {msg['dst']} de {msg['src']}]: {msg['payload']}")

            # --- Tratamento de ACK (Recebendo confirmação) ---
            elif msg["type"] == "ACK":
                ack_id = msg["msg_id"]
                # Se estamos esperando por esse ACK, marcamos o futuro como resolvido
                if ack_id in client.pending_acks:
                    future = client.pending_acks[ack_id]
                    if not future.done():
                        future.set_result(True)
            

async def pingPeers(client: Client):
    """Rotina periódica simplificada de PING (placeholder)."""
    for peer_id, data in client.peersConnected.items():
        if data.get("status") == "CONNECTED" and peer_id in client.outbound and "writer" in data:
            try:
                packet = {
                    "type": "PING",
                    "msg_id": str(uuid.uuid4()),
                    "timestamp": time.time(),
                    "ttl": 1
                }
                data["writer"].write((json.dumps(packet) + '\n').encode('UTF-8'))
                await data["writer"].drain()
            except Exception as e:
                logger.warning(f"Falha ao enviar PING para {peer_id}: {e}")
    await asyncio.sleep(30)
    return