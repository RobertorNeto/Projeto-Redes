import json
import asyncio
import logger
####    Abstração para REGISTER, UNREGISTER e DISCOVER  ####

async def registerPeer(peer, port):
    
    # cria a mensagem no formato REGISTER e a converte para objeto json
    jsonString = f'{{"type" : "REGISTER", "name" : {peer}, "port" : {port}, "ttl" : 7200}}' + '\n'
    message = json.dumps(jsonString)

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
        logger.error("Não foi possível se conectar ao servidor!", error)

    # fecha a conexão e espera o buffer
    writer.close()
    await writer.wait_closed()


async def unregister(namespace, peer, port):

    # cria a mensagem no formato UNREGISTER e a converte para objeto json
    jsonString = f'{{"type" : "UNREGISTER", "namespace" : {namespace}, "name" : {peer}, "port" : {port}, "ttl" : 7200}}' + '\n'
    message = json.dumps(jsonString)

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

        # decodifica a mensagem e recebe seu status
        responseMsg = response.decode('UTF-8')
        responseMsg = responseMsg.strip()

        responseMsg = json.loads(responseMsg)

        if responseMsg["status"] == "OK":
            return True
        else:
            return False
        
    except TimeoutError as error:
        logger.error("Não foi possível se conectar ao servidor!", error)

    # fecha a conexão e espera o buffer
    writer.close()
    await writer.wait_closed()

        
async def discoverPeers(receiver):

    # verifica se é um discover de namespace ou total
    if len(receiver) > 0:
        # cria a mensagem apropriada
        jsonString = f'{{"type" : "DISCOVER", "namespace" : {receiver[0]}}}' + '\n'
        message = json.dumps(jsonString)
        
        # le os parametros do servidor pelo arquivo 'configs.json' e abre a conexão
        with open("configs.json", "r") as configFile:
            configs = json.load(configFile)
        reader, writer = await asyncio.open_connection(configs["server_address"], configs["server_port"])

        # manda a mensagem de register e espera pela limpeza de buffer
        writer.write(message.encode('UTF-8'))
        await writer.drain()
        
    else:
        # cria a mensagem apropriada
        jsonString = '{"type" : "DISCOVER"}' + '\n'
        message = json.dumps(jsonString)
        
        # le os parametros do servidor pelo arquivo 'config.json' e abre a conexão
        with open("config.json", "r") as configFile:
            configs = json.load(configFile)
        reader, writer = await asyncio.open_connection(configs["server_address"], configs["server_port"])

        # manda a mensagem de register e espera pela limpeza de buffer
        writer.write(message.encode('UTF-8'))
        await writer.drain()

    
    # espera o retorno por 10 segundos
    try:
        response = await asyncio.wait_for(reader.read(32000), timeout=10)

        # decodifica a mensagem
        responseMsg = response.decode('UTF-8')
        # retorna a lista dos peers descobertos
        responseMsg = responseMsg.strip()

        responseMsg = json.loads(responseMsg)

        if responseMsg["status"] != "OK":
            logger.error("Não foi possível se conectar ao servidor!")
            return None

        return responseMsg["peers"]
    
    except TimeoutError as error:
            logger.error("Não foi possível se conectar ao servidor!", error)
            
    # fecha a conexão e espera o buffer
    writer.close()
    await writer.wait_closed()
    return None
