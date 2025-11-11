from logger import *
from cli import *
from message_router import *
from p2p_transport import *
from rendezvous_client import *
from state import *
import asyncio
import aioconsole

class Client:

    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.peersConnected = []
        self.messages = set()
    
    def addPeer(port, id, self):
        newPeer = tuple(port, id)
        self.peersConnected.add(newPeer)

    def removePeer(port, id, self):
        newPeer = tuple(port, id)
        self.peersConnected.remove(newPeer)


async def main():

    client = Client("Davi", 8080)

    await initialScreen()
    asyncio.create_task(clientLoop(client))
    ans = 0
    while not ans:
        ans = await commandRedirection(client)


async def clientLoop(client):
    pingPeers(client)
    while True:
        await checkMessages(client)
        await asyncio.sleep(2)

async def commandRedirection(client):
    commands = (await aioconsole.ainput()).split(' ')
    if commands[0] == "/peers":
        showPeers()
    elif commands[0] == "/connect":
        connectPeers(commands[1], client)
    elif commands[0] == "/discover":
        discoverPeers(commands)
    elif commands[0] == "/register":
        registerPeer(commands[1], commands[2])
    elif commands[0] == "/unregister":
        unregister(commands[0], commands[1], commands[2])
    elif commands[0] == "/msg":
        commands.remove("/msg")
        sendMessage(commands, client)
    elif commands[0] == "/watch":
        logEnable()
    elif commands[0] == "/quit":
        print("Terminando execução...")
        return 1
    elif commands[0] == "/help":
        initialScreen()
    else:
        print("Comando inválido! Digite '/help' para saber comandos disponíveis.")
    return 0

asyncio.run(main())