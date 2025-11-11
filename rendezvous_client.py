import json
import asyncio
####    Abstração para REGISTER, UNREGISTER e DISCOVER  ####

# 1. Integração com o Rendezvous
#   a) Implementação do Register
#   b) Implementação do Discover
#   c) Implementação do Unregister

SERVER_ADDRESS = "pyp2p.mfcaetano.cc"
SERVER_PORT = 8080

async def registerPeer(peer, port):
    json_string = {"type" : "REGISTER", "name" : peer, "port" : port, "ttl" : 7200}
    message = json.dump(json_string)
    reader, writer = await asyncio.open_connection(SERVER_ADDRESS, SERVER_PORT)
    writer.write(message.encode('UTF-8'))
    await writer.drain()
    response = await asyncio.wait_for(reader.read(32000), timeout=10)
    writer.close()
    await writer.wait_closed()

    response_msg = response.decode('UTF-8')
    if response_msg["status"] == "OK":
        return True
    else:
        return False

async def unregister(namespace, peer, port):
    json_string = {"type" : "UNREGISTER", "namespace" : namespace, "name" : peer, "port" : port, "ttl" : 7200}
    message = json.dump(json_string)
    reader, writer = await asyncio.open_connection(SERVER_ADDRESS, SERVER_PORT)
    writer.write(message.encode('UTF-8'))
    await writer.drain()
    response = await asyncio.wait_for(reader.read(32000), timeout=10)
    writer.close()
    await writer.wait_closed()

    response_msg = response.decode('UTF-8')
    if response_msg["status"] == "OK":
        return True
    else:
        return False
        
async def discoverPeers(receiver):
    if len(receiver) > 0:
        json_string = {"type" : "DISCOVER", "namespace" : receiver[0]}
        message = json.dump(json_string)
        reader, writer = await asyncio.open_connection(SERVER_ADDRESS, SERVER_PORT)
        writer.write(message.encode('UTF-8'))
        await writer.drain()
        response = await asyncio.wait_for(reader.read(32000), timeout=10)
        writer.close()
        await writer.wait_closed()

        response_msg = response.decode('UTF-8')
        if len(response_msg["peers"]) == 0:
            print("Não há nenhum peer registrado ainda!")
        else:
            for peer in response_msg["peers"]:
                print(f"name: {peer["name"]}, address: {peer["ip"]}")
    
    else:
        json_string = {"type" : "DISCOVER"}
        message = json.dump(json_string)
        reader, writer = await asyncio.open_connection(SERVER_ADDRESS, SERVER_PORT)
        writer.write(message.encode('UTF-8'))
        await writer.drain()
        response = await asyncio.wait_for(reader.read(32000), timeout=10)
        writer.close()
        await writer.wait_closed()

        response_msg = response.decode('UTF-8')
        if len(response_msg["peers"]) == 0:
            print("Não há nenhum peer registrado ainda!")
        else:
            for peer in response_msg["peers"]:
                print(f"name: {peer["name"]}, namespace: {peer["namespace"]}, address: {peer["ip"]}")