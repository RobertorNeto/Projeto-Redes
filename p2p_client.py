import json
import asyncio
from logger import *
####    Abstração para REGISTER, UNREGISTER e DISCOVER  ####

async def registerPeer(peerName, peerNamespace, port):
    
    # cria a mensagem no formato REGISTER e a converte para objeto json
    jsonString = {"type" : "REGISTER", "namespace" : peerNamespace, "name" : peerName, "port" : port, "ttl" : 7200}
    message = json.dumps(jsonString) + '\n'

    # le os parametros do servidor pelo arquivo 'configs.json' e abre a conexão
    with open("config.json", "r") as configFile:
        configs = json.load(configFile)
    reader, writer = await asyncio.open_connection(configs["server_address"], configs["server_port"])

    # manda a mensagem de register e espera pela limpeza de buffer
    writer.write(message.encode('UTF-8'))
    await writer.drain()

    # espera o retorno por 10 segundos
    try:
        response = await asyncio.wait_for(reader.read(32000), timeout=10)

        # decodifica a mensagem e recebe seu status
        responseMsg = response.decode('UTF-8')
        responseMsg = responseMsg.strip()

        responseMsg = json.loads(responseMsg)

        if responseMsg["status"] == "OK":
            return True
        else:
            return False

    except TimeoutError as error:
        loggerError("Não foi possível se conectar ao servidor!", error)

    # fecha a conexão e espera o buffer
    writer.close()
    await writer.wait_closed()


async def unregister(namespace, peer, port):
    # cria a mensagem no formato UNREGISTER como dict
    json_dict = {
        "type": "UNREGISTER",
        "namespace": namespace,
        "name": peer,
        "port": port,
        "ttl": 7200
    }
    message = json.dumps(json_dict) + '\n'

    # lê parâmetros do servidor
    with open("config.json", "r") as configFile:
        configs = json.load(configFile)
    reader, writer = await asyncio.open_connection(configs["server_address"], configs["server_port"])

    # envia
    writer.write(message.encode('UTF-8'))
    await writer.drain()

    try:
        response = await asyncio.wait_for(reader.read(32000), timeout=10)
        responseMsg = response.decode('UTF-8').strip()
        responseJson = json.loads(responseMsg)
        return responseJson.get("status") == "OK"
    except TimeoutError as error:
        loggerError("Timeout ao tentar UNREGISTER no servidor", error)
        return False
    finally:
        writer.close()
        await writer.wait_closed()

        
async def discoverPeers(receiver):

    # verifica se é um discover de namespace ou total
    if len(receiver) > 0:
        # cria a mensagem apropriada
        jsonString = {"type" : "DISCOVER", "namespace" : receiver[0]}
        message = json.dumps(jsonString)
        
        # le os parametros do servidor pelo arquivo 'configs.json' e abre a conexão
        with open("config.json", "r") as configFile:
            configs = json.load(configFile)
        reader, writer = await asyncio.open_connection(configs["server_address"], configs["server_port"])

        # manda a mensagem de register e espera pela limpeza de buffer
        writer.write(message.encode('UTF-8') + b'\n')
        await writer.drain()
        
    else:
        # cria a mensagem apropriada
        jsonString = {"type" : "DISCOVER"}
        message = json.dumps(jsonString)
        
        # le os parametros do servidor pelo arquivo 'config.json' e abre a conexão
        with open("config.json", "r") as configFile:
            configs = json.load(configFile)
        reader, writer = await asyncio.open_connection(configs["server_address"], configs["server_port"])

        # manda a mensagem de register e espera pela limpeza de buffer
        writer.write(message.encode('UTF-8') + b'\n')
        await writer.drain()

    
    # espera o retorno por 10 segundos
    try:
        response = await asyncio.wait_for(reader.readline(), timeout=10)

        # decodifica a mensagem
        responseMsg = response.decode('UTF-8')
        # retorna a lista dos peers descobertos
        responseMsg = responseMsg.strip()

        responseMsg = json.loads(responseMsg)

        if responseMsg["status"] != "OK":
            loggerError("Não foi possível se conectar ao servidor!")
            return None

        return responseMsg["peers"]
    
    except TimeoutError as error:
            loggerError("Não foi possível se conectar ao servidor!", error)
            
    # fecha a conexão e espera o buffer
    writer.close()
    await writer.wait_closed()
    return None
