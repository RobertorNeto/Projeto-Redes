import asyncio
import json
import uuid
from logger import *
from client import Client
import json
import uuid

async def sendMessage(target_peer_id, message, client : Client):
    if target_peer_id not in client.peersConnected:
        # verifica se o peer está na lista de peers conectados
        print(f"Erro: Peer {target_peer_id} não encontrado ou desconectado.")
        return

    # pega o peer_id do peer destinatário e vê se está conectado
    peer_data = client.peersConnected[target_peer_id]

    if peer_data["status"] != "CONNECTED" or "writer" not in peer_data:
        print(f"Erro: Sem conexão ativa com {target_peer_id}.")
        return

    # cria o ID único da mensagem e o payload, definindo que requer ACK
    msg_id = str(uuid.uuid4())
    require_ack = True

    payload = {
        "type": "SEND",
        "msg_id": msg_id,
        "src": f"{client.name}@{client.namespace}",
        "dst": target_peer_id,
        "payload": message,
        "require_ack": require_ack,
        "ttl": 1
    }

    try:
        # envia a mensagem para o peer destinatário usando o 'writer' armazenado (em clientLoop() na main.py)
        writer = peer_data["writer"]
        writer.write((json.dumps(payload) + '\n').encode('UTF-8'))
        await writer.drain()
        loggerInfo(f"Mensagem enviada para {target_peer_id}: {message}")

        if require_ack:
            # atualiza a estrutura para aguardar o ACK
            ack_future = asyncio.get_running_loop().create_future()
            client.pending_acks[msg_id] = ack_future

            try:
                # espera pelo ACK com timeout
                await asyncio.wait_for(ack_future, timeout=5.0)
                print(f"✓ ACK recebido de {target_peer_id}")

            except asyncio.TimeoutError:
                loggerWarning(f"Timeout: Não recebeu ACK de {target_peer_id} para msg {msg_id}")
                print(f"⚠ Timeout esperando confirmação de {target_peer_id}")
            finally:
                if msg_id in client.pending_acks:
                    # apaga a entrada de espera pelo ACK tanto em sucesso quanto em timeout
                    del client.pending_acks[msg_id]

    except Exception as e:
        loggerError(f"Falha ao enviar mensagem para {target_peer_id}", exception=e)

async def pubMessage(destination, message_text, client: Client):
    # cria o ID único da mensagem e o payload, sem ACK dessa vez
    msg_id = str(uuid.uuid4())
    
    payload = {
        "type": "PUB",
        "msg_id": msg_id,
        "src": f"{client.name}@{client.namespace}",
        "dst": destination,
        "payload": message_text,
        "require_ack": False, 
        "ttl": 1
    }

    json_msg = (json.dumps(payload) + '\n').encode('UTF-8')
    count = 0

    # faz uma cópia da lista de peers conectados para evitar modificação durante iteração
    peers_snapshot = list(client.peersConnected.items())

    for peer_id, data in peers_snapshot:
        
        # verifica se deve enviar a mensagem para o peer atual com base se é um pub global ou por namespace
        should_send = False
        if destination == "*":
            should_send = True
        elif destination.startswith("#"):
            # recebe namespace do destino (sem o '#') e compara com o namespace do peer
            target_ns = destination[1:]
            try:
                peer_ns = peer_id.split('@')[1]
                if peer_ns == target_ns:
                    should_send = True
            except IndexError:
                continue

        if should_send and data["status"] == "CONNECTED" and "writer" in data:
            try:
                # envia a mensagem PUB para o peer usando o 'writer' armazenado
                data["writer"].write(json_msg)
                await data["writer"].drain()
                count += 1
            
            except (ConnectionResetError, BrokenPipeError):
                loggerWarning(f"Não foi possível enviar PUB para {peer_id}: Conexão perdida.")
                if peer_id in client.peersConnected:
                    client.peersConnected[peer_id]["status"] = "LOST"

            except Exception as e:
                loggerError(f"Erro inesperado ao publicar para {peer_id}", e)

    print(f"Mensagem publicada para {count} peers.")

