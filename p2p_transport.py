import asyncio
import json
import time

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

async def connectPeers(command):
    json_string = {"type" : "HELLO", "peer_id" : f"{command}", "version" : 1.0, "features" : ["metrics", "ack"]}
    message = json.dump(json_string)
    reader, writer = await asyncio.open_connection(host, port)
    writer.write(message.encode('UTF-8'))
    await writer.drain()
    try:
        response = await asyncio.wait_for(reader.read(32000), timeout=10)
        writer.close()
        await writer.wait_closed()

    
    except TimeoutError:
        print("Não foi possível estabelecer conexão!")
        return False