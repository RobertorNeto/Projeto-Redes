from logger import *
from cli import *
from message_router import *
from peer_connection import *
from p2p_client import *
from peer_list import *
from state import *
import asyncio
from client import Client

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
    if connectedPeers:
        await updatePeerList(client, connectedPeers)

    # itera sobre a lista de peers
    # DICA: Use list(client.peersConnected) para evitar erro de mudança de tamanho do dict durante iteração
    for peer in list(client.peersConnected): 
        if peer == f"{client.name}@{client.namespace}":
            continue
        
        peer_data = client.peersConnected[peer]

        # Se já estiver conectado, faz o PING
        if peer_data["status"] == "CONNECTED":
            # (Opcional) Você pode passar reader/writer aqui se já tiver salvo
            # mas cuidado para não abrir conexão nova se já existe uma
            if "writer" in peer_data:
                await pingPeers(client, None, None) # Ajuste seus argumentos do PING conforme sua implementação
            continue

        # Se estiver esperando conexão (WAITING), tenta conectar
        if peer_data["status"] == "WAITING":
            try:
                # <--- A CORREÇÃO PRINCIPAL COMEÇA AQUI --->
                logger.info(f"Tentando conectar a {peer} ({peer_data['address']}:{peer_data['port']})...")
                
                # Adicione um timeout para não ficar travado para sempre no Windows
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(peer_data["address"], peer_data["port"]),
                    timeout=5.0 # Timeout de 5 segundos
                )

                # Salva o writer
                client.peersConnected[peer]["writer"] = writer
                
                # Inicia o Handshake
                await sendHello(client, reader, writer, peer)
                
                # Cria a task para escutar esse peer
                asyncio.create_task(listenToPeer(client, reader, peer, writer))
            
            except (OSError, asyncio.TimeoutError) as e:
                # Se der erro (timeout, recusado, semáforo expirou), a gente captura e não cracha o programa
                logger.warning(f"Falha ao conectar com {peer}: {e}")
                # Opcional: Marcar como LOST ou remover da lista
                # client.removePeerPing(peer, client) 
            except Exception as e:
                logger.error(f"Erro inesperado ao conectar com {peer}: {e}")

async def commandRedirection(client):

    # faz o redirecionamento de rotinas para o comando digitado pelo usuário
    commands = await async_input("Enter command: ")
    commands = commands.split(" ")
    if commands[0] == "/peers":
        # Se não houver argumento, assume '*' (todos)
        arg = commands[1] if len(commands) > 1 else '*'
        await showPeers(arg, client)

    elif commands[0] == "/msg":
        if len(commands) < 3:
            print("Uso: /msg <peer_id> <mensagem>")
        else:
            await sendMessage(commands[1], ' '.join(commands[2:]), client)

    elif commands[0] == "/pub":
        if len(commands) < 3:
            print("Uso: /pub <* | #namespace> <mensagem>")
        else:
            await pubMessage(commands[1], ' '.join(commands[2:]), client)

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