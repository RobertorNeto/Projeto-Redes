import asyncio
import json
import uuid
from logger import *
from client import Client
import json
import uuid

async def sendMessage(target_peer_id, message, client : Client):
    if target_peer_id not in client.peersConnected:
        print(f"Erro: Peer {target_peer_id} não encontrado ou desconectado.")
        return

    peer_data = client.peersConnected[target_peer_id]

    if peer_data["status"] != "CONNECTED" or "writer" not in peer_data:
        print(f"Erro: Sem conexão ativa com {target_peer_id}.")
        return

    msg_id = str(uuid.uuid4())
    require_ack = True;

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
        writer = peer_data["writer"]
        writer.write((json.dumps(payload) + '\n').encode('UTF-8'))
        await writer.drain()
        loggerInfo(f"Mensagem enviada para {target_peer_id}: {message}")

        if require_ack:
            ack_future = asyncio.get_running_loop().create_future()
            client.pending_acks[msg_id] = ack_future

            try:
                await asyncio.wait_for(ack_future, timeout=5.0)
                print(f"✓ ACK recebido de {target_peer_id}")
            except asyncio.TimeoutError:
                loggerWarning(f"Timeout: Não recebeu ACK de {target_peer_id} para msg {msg_id}")
                print(f"⚠ Timeout esperando confirmação de {target_peer_id}")
            finally:
                if msg_id in client.pending_acks:
                    del client.pending_acks[msg_id]

    except Exception as e:
        loggerError(f"Falha ao enviar mensagem para {target_peer_id}", exception=e)

async def pubMessage(destination, message_text, client: Client):
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

    peers_snapshot = list(client.peersConnected.items())

    for peer_id, data in peers_snapshot:
        
        should_send = False
        if destination == "*":
            should_send = True
        elif destination.startswith("#"):
            target_ns = destination[1:]
            try:
                peer_ns = peer_id.split('@')[1]
                if peer_ns == target_ns:
                    should_send = True
            except IndexError:
                continue

        if should_send and data["status"] == "CONNECTED" and "writer" in data:
            try:
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

