import asyncio
import json
import time
import uuid
from datetime import datetime
from logger import *
from client import Client
from state import updateRttTable  
from p2p_client import registerPeer


async def sendHello(client: Client, reader, writer, peer_id: str):
    try:
        # cria a mensagem HELLO em JSON e envia para o peer
        with open("config.json", "r") as configsFile:
            configs = json.load(configsFile)
            
        jsonString = {
            "type" : "HELLO", 
            "peer_id" : f"{client.name}@{client.namespace}", 
            "version" : configs["version"], 
            "features" : configs["features"]
        }
        message = json.dumps(jsonString)

        writer.write(message.encode('UTF-8') + b'\n')
        await writer.drain()

        try:
            # espera a resposta HELLO_OK do peer com timeout de 10 segundos, e atualiza o status da conexão (CONNECTED e outbound)
            response = await asyncio.wait_for(reader.readline(), timeout=10)
            if not response:
                loggerError(f"Conexão fechada por {peer_id} durante handshake.")
                return

            responseMsg = response.decode('UTF-8').strip()
            
            responseMsg = json.loads(responseMsg)

            if responseMsg["type"] == "HELLO_OK":
                client.peersConnected[peer_id]["status"] = "CONNECTED"
                client.outbound.add(peer_id)
                loggerInfo(f"Handshake concluído com sucesso: {peer_id}")

        except asyncio.TimeoutError:
            loggerError(f"Timeout: Não recebeu HELLO_OK de {peer_id}")
            
    except Exception as e:
        loggerError(f"Erro ao enviar HELLO para {peer_id}", e)

async def sendHelloOk(peer_id: str, reader, writer):
    try:
        # cria a mensagem HELLO_OK em JSON e envia para o peer, quando recebe HELLO na rotina handle_incoming_connection()
        with open("config.json", "r") as configsFile:
            configs = json.load(configsFile)
        
        # cria a mensagem HELLO_OK em JSON e envia para o peer
        jsonString = {
            "type" : "HELLO_OK", 
            "peer_id" : peer_id, 
            "version" : configs["version"], 
            "features" : configs["features"]
        }
        message = json.dumps(jsonString)

        writer.write(message.encode('UTF-8') + b'\n')
        await writer.drain()

    except Exception as e:
        loggerError(f"Erro ao enviar HELLO_OK para {peer_id}", e)

async def handle_incoming_connection(reader, writer, client: Client):
    addr = writer.get_extra_info('peername')
    
    try:
        # rotina para tratar das tentativas de conexão INBOUND de outros peers
        data = await asyncio.wait_for(reader.readline(), timeout=10.0)
        if not data:
            writer.close()
            await writer.wait_closed()
            return

        msg = json.loads(data.decode('UTF-8').strip())

        if msg.get("type") != "HELLO":
            writer.close()
            await writer.wait_closed()
            return

        remote_peer_id = msg.get("peer_id")
        
        # caso o peer não esteja na tabela, adiciona com status CONNECTED, caso contrário, atualiza o 'writer' e status
        if remote_peer_id not in client.peersConnected:
            client.peersConnected[remote_peer_id] = {
                "address": addr[0],
                "port": addr[1],
                "status": "CONNECTED",
                "writer": writer
            }
        else:
            client.peersConnected[remote_peer_id]["writer"] = writer
            client.peersConnected[remote_peer_id]["status"] = "CONNECTED"

        # adiciona o peer à lista de conexões INBOUND (recebidas)
        client.inbound.add(remote_peer_id)

        # envia a mensagem HELLO_OK como resposta para finalizar a tentativa de conexão com sucesso
        await sendHelloOk(remote_peer_id, reader, writer)
        loggerInfo(f"Conexão INBOUND estabelecida com {remote_peer_id}")
        asyncio.create_task(listenToPeer(client, reader, remote_peer_id, writer))

    except Exception as e:
        loggerError(f"Erro no handshake INBOUND com {addr}", e)
        writer.close()
        await writer.wait_closed()

async def listenToPeer(client: Client, reader, peer_id: str, writer):
    try:
        while True:
            # tenta ler mensagens do peer conectado
            data = await reader.readline()
            if not data:
                loggerWarning(f"Conexão fechada pelo peer {peer_id}")
                break
            
            msg_str = data.decode('UTF-8').strip()
            if not msg_str:
                continue
                
            try:
                msg = json.loads(msg_str)
            except json.JSONDecodeError:
                loggerWarning(f"Mensagem inválida recebida de {peer_id}")
                continue

            msg_type = msg.get("type")

            # trata os diferentes tipos de mensagens recebidas
            if msg_type == "HELLO":
                await sendHelloOk(peer_id, reader, writer)

            elif msg_type == "PING":
                pong_packet = {
                    "type": "PONG",
                    "msg_id": msg["msg_id"],
                    "timestamp": time.time(),
                    "ttl": 1
                }
                writer.write((json.dumps(pong_packet) + '\n').encode('UTF-8'))
                await writer.drain()

            elif msg_type == "PONG":
                msg_id = msg.get("msg_id")
                
                # caso esteja recebendo um PONG, calcula o RTT e atualiza a tabela de RTTs
                if hasattr(client, "ping_timestamps") and msg_id in client.ping_timestamps:
                    start_time = client.ping_timestamps.pop(msg_id)
                    end_time = time.time()
                    
                    rtt_ms = (end_time - start_time) * 1000
                    
                    my_id = f"{client.name}@{client.namespace}"
                    await updateRttTable(rtt_ms, (my_id, peer_id), client)
                    
                    loggerDebug(f"RTT atualizado para {peer_id}: {rtt_ms:.2f}ms")

            elif msg_type == "SEND":
                # no SEND, trata da emissão de ACKs e exibição da mensagem
                print(f"\n[DM de {msg.get('src', '?')}]: {msg.get('payload', '')}")
                
                if msg.get("require_ack", False):
                    ack_packet = {
                        "type": "ACK",
                        "msg_id": msg["msg_id"],
                        "timestamp": datetime.now().isoformat(),
                        "ttl": 1
                    }
                    writer.write((json.dumps(ack_packet) + '\n').encode('UTF-8'))
                    await writer.drain()

            elif msg_type == "PUB":
                # no PUB, apenas exibe a mensagem pública
                print(f"\n[PUB {msg.get('dst')} de {msg.get('src')}]: {msg.get('payload')}")

            elif msg_type == "ACK":
                # no ACK, verifica se há uma espera por esse ACK e a completa
                ack_id = msg.get("msg_id")
                if ack_id in client.pending_acks:
                    future = client.pending_acks[ack_id]
                    if not future.done():
                        future.set_result(True)
            
            elif msg_type == "BYE":
                # ao receber BYE, envia BYE_OK e encerra a conexão
                loggerInfo(f"Recebido BYE de {peer_id}. Encerrando conexão.")
                bye_packet = {
                    "type": "BYE_OK",
                    "msg_id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "ttl": 1,
                    "src": f"{client.name}@{client.namespace}",
                    "dest": peer_id,
                }
                writer.write((json.dumps(bye_packet) + '\n').encode('UTF-8'))
                await writer.drain()

                client.removePeer(peer_id)
                break

    except (ConnectionResetError, asyncio.IncompleteReadError):
        loggerWarning(f"Conexão perdida com {peer_id}")
    except Exception as e:
        loggerError(f"Erro escutando peer {peer_id}", e)
    finally:
        if peer_id in client.peersConnected:
             pass

async def pingPeers(client: Client):
    if not hasattr(client, "ping_timestamps"):
        # inicializa o dicionário de timestamps de ping se não existir
        client.ping_timestamps = {}

    for peer_id, data in list(client.peersConnected.items()):
        # envia PING apenas para peers conectados
        if data.get("status") == "CONNECTED" and "writer" in data and data["writer"]:
            try:
                msg_id = str(uuid.uuid4())
                current_time = time.time()
                
                # registra o timestamp do ping para cálculo de RTT ao receber o PONG
                client.ping_timestamps[msg_id] = current_time
                
                packet = {
                    "type": "PING",
                    "msg_id": msg_id,
                    "timestamp": current_time,
                    "ttl": 1
                }
                
                data["writer"].write((json.dumps(packet) + '\n').encode('UTF-8'))
                await data["writer"].drain()
                
            except Exception as e:
                loggerWarning(f"Falha ao enviar PING para {peer_id}: {e}")
                client.ping_timestamps.pop(msg_id, None)
                
    return

async def reconnectPeers(client: Client):
    # rotina para forçar a reconexão com todos os peers conectados (backoff exponencial)
    print("\n🔄 Iniciando protocolo de reconexão forçada...")
    loggerInfo("Usuário solicitou /reconnect.")

    try:
        reg_success = await registerPeer(client.name, client.namespace, client.port)
        if reg_success:
            print("✅ Registro no servidor Rendezvous atualizado.")
        else:
            print("❌ Falha ao contatar servidor Rendezvous. Verifique sua internet.")
    except Exception as e:
        print(f"❌ Erro ao conectar ao servidor: {e}")

    closed_count = 0
    
    for peer_id, data in list(client.peersConnected.items()):
        
        # reseta o estado de cada peer para forçar nova conexão, por meio de um backoff exponencial
        exponential_backoff = 1
        if data.get("writer"):
            while True:
                try:
                    data["writer"].close()
                    await data["writer"].wait_closed()
                    break
                except Exception as e:
                    loggerWarning(f"Erro ao fechar socket de {peer_id}, tentando novamente: {e}")
                    await asyncio.sleep(exponential_backoff * 10)
                    exponential_backoff = min(exponential_backoff * 2, 40)  # limita o backoff máximo a 40 segundos

        data["writer"] = None
        data["status"] = "WAITING"

        closed_count += 1

    client.outbound.clear()
    client.inbound.clear()
    
    if hasattr(client, 'rtt_table'):
            client.rtt_table.clear()

    print(f"⚠️ {closed_count} conexões foram reiniciadas.")
    print("⏳ O sistema tentará reconectar automaticamente em instantes.\n")

async def sendBye(client: Client):
    # envia mensagem de BYE para todos os peers conectados antes de sair
    print("\n👋 Enviando mensagens de BYE para peers conectados...")
    
    for peer_id, data in list(client.peersConnected.items()):
        if data.get("status") == "CONNECTED" and "writer" in data and data["writer"]:
            try:
                bye_packet = {
                    "type": "BYE",
                    "msg_id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "ttl": 1,
                    "src": f"{client.name}@{client.namespace}",
                    "dest": peer_id,
                    "reason": "Encerrando conexão"
                }
                data["writer"].write((json.dumps(bye_packet) + '\n').encode('UTF-8'))
                await data["writer"].drain()
                loggerInfo(f"Mensagem BYE enviada para {peer_id}")
            except Exception as e:
                loggerWarning(f"Falha ao enviar BYE para {peer_id}: {e}")
    
    print("✅ Mensagens de BYE enviadas.\n")