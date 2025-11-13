import json
import asyncio
from logger import logger
####    Abstração para REGISTER, UNREGISTER e DISCOVER  ####

async def registerPeer(peer, port):
    
    # cria a mensagem no formato REGISTER e a converte para objeto json
    jsonString = {"type" : "REGISTER", "name" : peer, "port" : port, "ttl" : 7200} + '\n'
    message = json.dump(jsonString)

    # le os parametros do servidor pelo arquivo 'configs.json' e abre a conexão
    with open("configs.json", "r") as configFile:
        configs = json.load(configFile)
    reader, writer = await asyncio.open_connection(configs["server_address"], configs["server_port"])

    # manda a mensagem de register e espera pela limpeza de buffer
    writer.write(message.encode('UTF-8'))
    await writer.drain()

    # espera o retorno por 10 segundos
    try:
        response = await asyncio.wait_for(reader.read(32000), timeout=10)

    except TimeoutError as error:
        logger.error("Não foi possível se conectar ao servidor!", error)

    # fecha a conexão e espera o buffer
    writer.close()
    await writer.wait_closed()

    # decodifica a mensagem e recebe seu status
    responseMsg = response.decode('UTF-8')
    if responseMsg["status"] == "OK":
        return True
    else:
        return False

async def unregister(namespace, peer, port):

    # cria a mensagem no formato UNREGISTER e a converte para objeto json
    jsonString = {"type" : "UNREGISTER", "namespace" : namespace, "name" : peer, "port" : port, "ttl" : 7200} + '\n'
    message = json.dump(jsonString)

    # le os parametros do servidor pelo arquivo 'configs.json' e abre a conexão
    with open("configs.json", "r") as configFile:
        configs = json.load(configFile)
    reader, writer = await asyncio.open_connection(configs["server_address"], configs["server_port"])

    # manda a mensagem de register e espera pela limpeza de buffer
    writer.write(message.encode('UTF-8'))
    await writer.drain()

    # espera o retorno por 10 segundos
    try:
        response = await asyncio.wait_for(reader.read(32000), timeout=10)

    except TimeoutError as error:
        logger.error("Não foi possível se conectar ao servidor!", error)

    # fecha a conexão e espera o buffer
    writer.close()
    await writer.wait_closed()

    # decodifica a mensagem e recebe seu status
    responseMsg = response.decode('UTF-8')
    if responseMsg["status"] == "OK":
        return True
    else:
        return False
        
async def discoverPeers(receiver):

    # verifica se é um discover de namespace ou total
    if len(receiver) > 0:
        # cria a mensagem apropriada
        jsonString = {"type" : "DISCOVER", "namespace" : receiver[0]} + '\n'
        message = json.dump(jsonString)
        
        # le os parametros do servidor pelo arquivo 'configs.json' e abre a conexão
        with open("configs.json", "r") as configFile:
            configs = json.load(configFile)
        reader, writer = await asyncio.open_connection(configs["server_address"], configs["server_port"])

        # manda a mensagem de register e espera pela limpeza de buffer
        writer.write(message.encode('UTF-8'))
        await writer.drain()

        # espera o retorno por 10 segundos
        try:
            response = await asyncio.wait_for(reader.read(32000), timeout=10)

        except TimeoutError as error:
            logger.error("Não foi possível se conectar ao servidor!", error)

        # fecha a conexão e espera o buffer
        writer.close()
        await writer.wait_closed()

        # decodifica a mensagem
        responseMsg = response.decode('UTF-8')
        
    else:
        # cria a mensagem apropriada
        jsonString = {"type" : "DISCOVER"} + '\n'
        message = json.dump(jsonString)
        
        # le os parametros do servidor pelo arquivo 'configs.json' e abre a conexão
        with open("configs.json", "r") as configFile:
            configs = json.load(configFile)
        reader, writer = await asyncio.open_connection(configs["server_address"], configs["server_port"])

        # manda a mensagem de register e espera pela limpeza de buffer
        writer.write(message.encode('UTF-8'))
        await writer.drain()

        # espera o retorno por 10 segundos
        try:
            response = await asyncio.wait_for(reader.read(32000), timeout=10)

        except TimeoutError as error:
            logger.error("Não foi possível se conectar ao servidor!", error)

        # fecha a conexão e espera o buffer
        writer.close()
        await writer.wait_closed()

        # decodifica a mensagem e recebe seu status
        responseMsg = response.decode('UTF-8')
    
    # retorna a lista dos peers descobertos
    return responseMsg["peers"]