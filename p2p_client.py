import json
import asyncio
from logger import *

async def registerPeer(peerName, peerNamespace, port):
    
    jsonString = {"type" : "REGISTER", "namespace" : peerNamespace, "name" : peerName, "port" : port, "ttl" : 7200}
    message = json.dumps(jsonString) + '\n'

    with open("config.json", "r") as configFile:
        configs = json.load(configFile)
    reader, writer = await asyncio.open_connection(configs["server_address"], configs["server_port"])

    writer.write(message.encode('UTF-8'))
    await writer.drain()

    try:
        response = await asyncio.wait_for(reader.read(32000), timeout=10)

        responseMsg = response.decode('UTF-8')
        responseMsg = responseMsg.strip()

        responseMsg = json.loads(responseMsg)

        if responseMsg["status"] == "OK":
            return True
        else:
            return False

    except TimeoutError as error:
        loggerError("Não foi possível se conectar ao servidor!", error)

    writer.close()
    await writer.wait_closed()


async def unregister(namespace, peer, port):
    json_dict = {
        "type": "UNREGISTER",
        "namespace": namespace,
        "name": peer,
        "port": port,
        "ttl": 7200
    }
    message = json.dumps(json_dict) + '\n'

    with open("config.json", "r") as configFile:
        configs = json.load(configFile)
    reader, writer = await asyncio.open_connection(configs["server_address"], configs["server_port"])

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
    if len(receiver) > 0:
        jsonString = {"type" : "DISCOVER", "namespace" : receiver[0]}
        message = json.dumps(jsonString)
        
        with open("config.json", "r") as configFile:
            configs = json.load(configFile)
        reader, writer = await asyncio.open_connection(configs["server_address"], configs["server_port"])

        writer.write(message.encode('UTF-8') + b'\n')
        await writer.drain()
        
    else:
        jsonString = {"type" : "DISCOVER"}
        message = json.dumps(jsonString)
        
        with open("config.json", "r") as configFile:
            configs = json.load(configFile)
        reader, writer = await asyncio.open_connection(configs["server_address"], configs["server_port"])

        writer.write(message.encode('UTF-8') + b'\n')
        await writer.drain()

    try:
        response = await asyncio.wait_for(reader.readline(), timeout=10)

        responseMsg = response.decode('UTF-8')
        responseMsg = responseMsg.strip()

        responseMsg = json.loads(responseMsg)

        if responseMsg["status"] != "OK":
            loggerError("Não foi possível se conectar ao servidor!")
            return None

        return responseMsg["peers"]
    
    except TimeoutError as error:
            loggerError("Não foi possível se conectar ao servidor!", error)
            
    writer.close()
    await writer.wait_closed()
    return None
