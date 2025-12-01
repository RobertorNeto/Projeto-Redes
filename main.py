import asyncio
import json
import functools
from logger import *
from cli import *
from message_router import *
from peer_connection import *
from p2p_client import *
from peer_list import *
from state import *
from client import Client

async def main():
    setupLogger()
    
    try:
        # carrega o arquivo 'config.json', que mantém os parâmetros do cliente
        with open("config.json", "r") as config_file:
            configs = json.load(config_file)
            client = Client(configs["name"], configs["port"], configs["namespace"])

    except FileNotFoundError as e:
        loggerError("Arquivo 'config.json' não encontrado!", e)
        return
    except json.JSONDecodeError as e:
        loggerError("Arquivo 'config.json' mal formatado!", e)
        return

    try:
        # inicia o servidor P2P para aceitar conexões de outros peers
        server_callback = functools.partial(handle_incoming_connection, client=client)
        
        server = await asyncio.start_server(
            server_callback, 
            '0.0.0.0', 
            client.port
        )
        loggerInfo(f"Servidor P2P iniciado. Escutando na porta {client.port}...")
        
        # cria uma tarefa para o servidor aceitar conexões de forma assíncrona
        asyncio.create_task(server.serve_forever())
        
    except OSError as e:
        loggerError(f"Falha ao abrir porta {client.port}. Verifique se já está em uso.", e)
        return

    loggerInfo("Registrando no servidor Rendezvous...")

    # tenta registrar o peer no servidor Rendezvous
    registered = await registerPeer(client.name, client.namespace, client.port)
    
    if not registered:
        loggerError("Falha ao registrar no Rendezvous. O programa continuará, mas talvez não seja visível.")
    else:
        loggerInfo("Registrado com sucesso!")

    # chama a tela inicial do CLI
    await initialScreen()

    # roda o loop principal enquanto o usuário não digita o comando de saída
    discovery_task = asyncio.create_task(clientLoop(client))
    ans = 0
    try:
        while not ans:
            # lida do comando do usuário de modo assíncrono
            ans = await commandRedirection(client)

    except KeyboardInterrupt:
        print("\nInterrupção forçada detectada.")
    finally:
        print("Saindo da rede...")
        discovery_task.cancel()
        
        # faz a desconexão limpa do peer e fecha o cliente
        await unregister(client.namespace, client.name, client.port)
        
        server.close()
        await server.wait_closed()
        print("Aplicação encerrada.")

async def clientLoop(client):
    while True:
        try:
            # primeiro, faz o discover de peers no servidor Rendezvous
            connectedPeers = await discoverPeers([]) 
            
            if connectedPeers:
                # atualiza a lista de peers conhecidos
                await updatePeerList(client, connectedPeers)

            for peer in list(client.peersConnected): 
                
                # evita tentar conectar a si mesmo, e pega o peer_id de cada peer da tabela
                if peer == f"{client.name}@{client.namespace}":
                    continue
                
                peer_data = client.peersConnected[peer]

                # tenta pingar os peers conectados para atualizar RTTs
                await pingPeers(client) 

                if peer_data["status"] == "WAITING":
                    try:
                        # tenta estabelecer conexão com o peer por meio de HELLO / HELLO_OK
                        reader, writer = await asyncio.wait_for(
                            asyncio.open_connection(peer_data["address"], peer_data["port"]),
                            timeout=5.0 
                        )

                        # atualiza o 'writer' na tabela de peers conectados para comunicação futura, e adiciona conexão
                        client.peersConnected[peer]["writer"] = writer
                        client.outbound.add(peer)

                        # envia a mensagem HELLO para o peer e espera respostas
                        await sendHello(client, reader, writer, peer)
                        
                        asyncio.create_task(listenToPeer(client, reader, peer, writer))
                    
                    except (OSError, asyncio.TimeoutError) as e:
                        loggerError(f"Falha ao conectar com {peer}", e)
                        
                    except Exception as e:
                        loggerError(f"Erro inesperado ao conectar com {peer}", e)

        except Exception as e:
            loggerError("Erro crítico no loop do cliente (Discover/Connect)", e)

        await asyncio.sleep(5) 


async def commandRedirection(client):
    try:
        # rotina assíncrona para ler o comando do usuário, fazendo o clear da tela antes (clearOSScreen)
        commands = await async_input("Digite o comando: ")
        
        if not commands.strip():
            return 0
            
        commands = commands.split(" ")
        cmd = commands[0].lower()

        if cmd == "/peers":
            clearOSScreen()
            arg = commands[1] if len(commands) > 1 else '*'
            await showPeers(arg, client)

        elif cmd == "/msg":
            clearOSScreen()
            if len(commands) < 3:
                print("Uso: /msg <peer_id> <mensagem>")
            else:
                target = commands[1]
                msg_content = ' '.join(commands[2:])
                await sendMessage(target, msg_content, client)

        elif cmd == "/pub":
            clearOSScreen()
            if len(commands) < 3:
                print("Uso: /pub <* | #namespace> <mensagem>")
            else:
                target = commands[1]
                msg_content = ' '.join(commands[2:])
                await pubMessage(target, msg_content, client)

        elif cmd == "/conn":
            clearOSScreen()
            await showConns(client)
            
        elif cmd == "/logon":
            clearOSScreen()
            if len(commands) < 2:
                print("Uso: /logon <nivel>")
            else:
                level = commands[1].upper()
                if level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                    print("Nível de log inválido! Use: DEBUG, INFO, WARNING, ERROR, CRITICAL")
                else:
                    addLevel(level)

        elif cmd == "/logoff":
            clearOSScreen()
            if len(commands) < 2:
                print("Uso: /logoff <nivel>")
            else:
                level = commands[1].upper()
                if level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                    print("Nível de log inválido! Use: DEBUG, INFO, WARNING, ERROR, CRITICAL")
                else:
                    removeLevel(level)

        elif cmd == "/reconnect":
            clearOSScreen()
            await reconnectPeers(client)
            
        elif cmd == "/rtt":
            clearOSScreen()
            await showRtt(client)
        elif cmd == "/quit":
            clearOSScreen()
            await sendBye(client)
            await unregister(client.namespace, client.name, client.port)
            return 1
        
        elif cmd == "/help":
            clearOSScreen()
            await initialScreen()

        else:
            print("Comando inválido! Digite '/help' para ver comandos disponíveis.")
            
    except EOFError:
        await sendBye(client)
        await unregister(client.namespace, client.name, client.port)
        return 1
    except Exception as e:
        loggerError("Erro processando comando", e)
        
    return 0

async def async_input(prompt: str = "") -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: input(prompt))

if __name__ == "__main__":
    # inicia o loop principal do asyncio (boa prática para lidar com KeyboardInterrupt)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass