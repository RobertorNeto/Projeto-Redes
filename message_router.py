import asyncio
import json
import uuid
from logger import logger
from client import Client
import json
import uuid
####    Roteamento das mensagens (PUB, SUB, SEND)    ####

# 1. Funcionamento da conexão entre peers
#   a) Envio de mensagens ponto-a-ponto (unicast)
#   b) Envio de mensagens para os peers de um <namespace>
#   c) Envio de mensagens para todos os peers da rede (broadcast)

# 2. Detalhes de implementação
#   a) PONG a cada 30s
#   b) Desconexão se 30s sem um PONG de resposta
#   c) ttl das mensagens fixo em 1, com mensagem de erro caso contrário
#   d) Tamanho das mensagens fixo em 32kb, com mensagem de erro caso contrário

#   e) Quando do uso do SEND, deve-se
#       - Ter um campo 'require_ack' na solicitação do emissor, que exige um 'ack' do receptor
#       - Receptor deve enviar um 'ack' com o mesmo msg_id da requisição inicial (único)
#       - Caso não haja recebimento desse 'ack', a mensagem é considerada como não entregue

#   f) Sobre o msg_id (escolher 1 das opções de geração)
#       - Timestamp + número aleatório de n bits no fim (geração de id aleatório)
#       - Geração de um id com nome do emissor + número incrementado sequencialmente
#       - Todo peer deve guardar, sem repetição, os msg_ids já recebidos (evitar duplicatas)

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
        logger.info(f"Mensagem enviada para {target_peer_id}: {message}")

        # Lógica de espera pelo ACK
        if require_ack:
            # Cria um futuro (promessa) que será resolvido quando o ACK chegar
            ack_future = asyncio.get_running_loop().create_future()
            client.pending_acks[msg_id] = ack_future

            try:
                # Espera até 5 segundos pelo ACK
                await asyncio.wait_for(ack_future, timeout=5.0)
                print(f"✓ ACK recebido de {target_peer_id}")
            except asyncio.TimeoutError:
                logger.warning(f"Timeout: Não recebeu ACK de {target_peer_id} para msg {msg_id}")
                print(f"⚠ Timeout esperando confirmação de {target_peer_id}")
            finally:
                # Limpa a pendência
                if msg_id in client.pending_acks:
                    del client.pending_acks[msg_id]

    except Exception as e:
        logger.error(f"Falha ao enviar mensagem para {target_peer_id}", exception=e)

async def pubMessage(destination, message_text, client: Client):
    """
    Envia mensagem de difusão (PUB).
    destination: '*' para broadcast ou '#namespace' para multicast
    """
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

    # CRUCIAL: Usamos list() para criar uma cópia dos itens.
    # Se iterarmos direto no dicionário e um peer for removido no meio, dá erro.
    peers_snapshot = list(client.peersConnected.items())

    for peer_id, data in peers_snapshot:
        
        # Lógica de filtro:
        should_send = False
        if destination == "*":
            should_send = True
        elif destination.startswith("#"):
            target_ns = destination[1:] # remove o #
            try:
                peer_ns = peer_id.split('@')[1]
                if peer_ns == target_ns:
                    should_send = True
            except IndexError:
                continue # Pula se o ID do peer estiver malformado

        if should_send and data["status"] == "CONNECTED" and "writer" in data:
            try:
                data["writer"].write(json_msg)
                await data["writer"].drain()
                count += 1
            
            # Se o peer caiu durante o envio, capturamos aqui para não travar o loop
            except (ConnectionResetError, BrokenPipeError):
                logger.warning(f"Não foi possível enviar PUB para {peer_id}: Conexão perdida.")
                # Opcional: Marcar como perdido imediatamente
                if peer_id in client.peersConnected:
                    client.peersConnected[peer_id]["status"] = "LOST"

            # Erros genéricos de código ou lógica
            except Exception as e:
                # CORREÇÃO DO BUG: O argumento correto é exc_info=True
                logger.error(f"Erro inesperado ao publicar para {peer_id}: {e}", exc_info=True)

    print(f"Mensagem publicada para {count} peers.")

