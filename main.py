from logger import *
from cli import *
from message_router import *
from peer_connection import *
from p2p_client import *
from peer_list import *
from state import *
import asyncio

# classe padrão para tratar do cliente 
class Client:

    def __init__(self, name, port, namespace):
        self.name = name
        self.port = port
        self.namespace = namespace
        self.peersConnected = {}
        self.inbound = set()
        self.outbound = set()
        self.backoffTimer = {}

    # remove um peer da lista do cliente quando da conexão perdida no PING
    def removePeerPing(id, self):
        self.peersConnected[id]["status"] = "LOST"
    
    # remove um peer da lista do cliente quando do BYE
    def removePeer(id, self):
        self.peersConnected[id]["status"] = "CLOSED"


async def main():
    setupLogger()

    # Abre o arquivo 'configs.json' para carregamento dos parâmetros e criação do cliente
    with open("config.json", "r") as config_file:
        configs = json.load(config_file)
        client = Client(configs["name"], configs["port"], configs["namespace"])
    
    # tenta fazer a conexão inicial do cliente com o rendezvous
    await registerPeer(client.name, client.namespace, client.port)

    # chama a tela inicial de comandos
    await initialScreen()

    # faz o loop do cliente de modo assíncrono com a espera de comandos do usuário
    asyncio.create_task(clientLoop(client))
    ans = 0
    while not ans:
        ans = await commandRedirection(client)


async def clientLoop(client):


    # faz o discover rotineiro dos peers conectados no rendezvous e atualiza a lista
    connectedPeers = await discoverPeers([])
    await updatePeerList(client, connectedPeers)

    # manda mensagens de HELLO para os clientes novos (EM ESPERA)
    for peer in client.peersConnected:
        if peer == f"{client.name}@{client.namespace}":
            continue
        reader, writer = await asyncio.open_connection(client.peersConnected[peer]["address"], client.peersConnected[peer]["port"])
        if client.peersConnected[peer]["status"] == "WAITING":
            await sendHello(client, reader, writer, peer)
            asyncio.create_task(listenToPeer(client, reader, peer, writer))

    # faz o PING para todos os clientes disponíveis (~PERDIDOS) na lista de peers do cliente
        elif client.peersConnected[peer]["status"] == "CONNECTED":
            await pingPeers(client, reader, writer)

async def commandRedirection(client):

    # faz o redirecionamento de rotinas para o comando digitado pelo usuário
    commands = await async_input("Enter command: ")
    commands = commands.split(" ")
    if commands[0] == "/peers":
        await showPeers(commands[1], client)

    elif commands[0] == "/msg":
        await sendMessage(commands[1], commands[2], client)

    elif commands[0] == "/pub":
        await pubMessage(commands[1], commands[2], client)

    elif commands[0] == "/conn":
        await showConns(client)

    elif commands[0] == "/reconnect":
        ''''''
        
    elif commands[0] == "/quit":
        await unregister(client.namespace, client.name, client.port)
        print("Terminando execução...")
        return 1
    
    elif commands[0] == "/help":
        await initialScreen()

    else:
        print("Comando inválido! Digite '/help' para saber comandos disponíveis.")
    return 0

async def async_input(prompt: str = "") -> str:

    # define a função para tratar do input assíncrono do usuário
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: input(prompt))

asyncio.run(main())