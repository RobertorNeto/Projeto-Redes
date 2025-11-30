import asyncio
import json
import functools  # Necessário para passar argumentos no callback do servidor
from logger import *
from cli import *
from message_router import *
from peer_connection import * # Certifique-se que handle_incoming_connection está aqui
from p2p_client import *
from peer_list import *
from state import *
from client import Client

async def main():
    # 1. Carregamento de Configurações
    setupLogger()
    
    try:
        with open("config.json", "r") as config_file:
            configs = json.load(config_file)
            # Instancia o cliente com os dados do JSON
            client = Client(configs["name"], configs["port"], configs["namespace"]) # Atualiza o logger com a instância do cliente
    except FileNotFoundError:
        logger.critical("Arquivo 'config.json' não encontrado!")
        return
    except json.JSONDecodeError:
        logger.critical("Arquivo 'config.json' mal formatado!")
        return

    # 2. INICIALIZAÇÃO DO SERVIDOR (CORREÇÃO CRÍTICA)
    # Sem isso, ninguém consegue conectar em você (Connection Refused)
    try:
        # Usamos partial para injetar a instância 'client' na função que trata conexões recebidas
        server_callback = functools.partial(handle_incoming_connection, client=client)
        
        server = await asyncio.start_server(
            server_callback, 
            '0.0.0.0', 
            client.port
        )
        loggerInfo(f"Servidor P2P iniciado. Escutando na porta {client.port}...")
        
        # Mantém o servidor rodando em background enquanto o app estiver vivo
        asyncio.create_task(server.serve_forever())
        
    except OSError as e:
        logger.critical(f"Falha ao abrir porta {client.port}. Verifique se já está em uso.", exc_info=True)
        return

    # 3. Registro no Rendezvous
    loggerInfo("Registrando no servidor Rendezvous...")
    registered = await registerPeer(client.name, client.namespace, client.port)
    
    if not registered:
        loggerError("Falha ao registrar no Rendezvous. O programa continuará, mas talvez não seja visível.")
    else:
        loggerInfo("Registrado com sucesso!")

    # 4. Interface Inicial
    await initialScreen()

    # 5. Inicia o Loop de Descoberta e Conexão Ativa (Background)
    # Guardamos a referência da task para poder cancelar se necessário (opcional)
    discovery_task = asyncio.create_task(clientLoop(client))

    # 6. Loop Principal de Comandos (Bloqueia até o usuário digitar /quit)
    ans = 0
    try:
        while not ans:
            # commandRedirection agora retorna 1 para sair, 0 para continuar
            ans = await commandRedirection(client)
    except KeyboardInterrupt:
        print("\nInterrupção forçada detectada.")
    finally:
        # 7. Encerramento Gracioso
        print("Saindo da rede...")
        discovery_task.cancel() # Para o loop de descoberta
        
        # Tenta desregistrar do servidor
        await unregister(client.namespace, client.name, client.port)
        
        # Fecha o servidor de escuta
        server.close()
        await server.wait_closed()
        print("Aplicação encerrada.")

async def clientLoop(client):
    """
    Loop infinito que periodicamente:
    1. Descobre peers no servidor Rendezvous
    2. Atualiza a lista local
    3. Tenta conectar ativamente aos peers desconectados
    """
    while True: # <--- CORREÇÃO: Loop Infinito
        try:
            # Faz o discover rotineiro dos peers conectados no rendezvous
            # Passando [] para descobrir todos do namespace padrão (ou ajuste conforme sua lógica de discover)
            connectedPeers = await discoverPeers([]) 
            
            if connectedPeers:
                # Atualiza a lista, mantendo conexões ativas
                await updatePeerList(client, connectedPeers)

            # Itera sobre a lista de peers (Cópia da lista para evitar erro de runtime)
            for peer in list(client.peersConnected): 
                
                # Ignora a si mesmo
                if peer == f"{client.name}@{client.namespace}":
                    continue
                
                peer_data = client.peersConnected[peer]

                # Se já estiver conectado, faz o PING (Manutenção)
                if peer_data["status"] == "CONNECTED":
                    if "writer" in peer_data:
                        # Implementação sugerida para o Ping: passar o peer_id ou data
                        await pingPeers(client) 
                    continue

                # Se estiver esperando conexão (WAITING), tenta conectar
                if peer_data["status"] == "WAITING":
                    try:
                        loggerInfo(f"Tentando conectar ativamente a {peer} ({peer_data['address']}:{peer_data['port']})...")
                        
                        # Adiciona timeout para não travar
                        reader, writer = await asyncio.wait_for(
                            asyncio.open_connection(peer_data["address"], peer_data["port"]),
                            timeout=5.0 
                        )

                        # Salva o writer imediatamente
                        client.peersConnected[peer]["writer"] = writer
                        client.outbound.add(peer) # Marca que nós iniciamos essa conexão
                        
                        # Inicia o Handshake (Envia HELLO)
                        await sendHello(client, reader, writer, peer)
                        
                        # Cria a task para escutar esse peer continuamente
                        asyncio.create_task(listenToPeer(client, reader, peer, writer))
                    
                    except (OSError, asyncio.TimeoutError) as e:
                        # Falha na conexão (peer offline, NAT, firewall)
                        # Usar exc_info=True se quiser debug detalhado
                        loggerWarning(f"Falha ao conectar com {peer}: {e}")
                        
                        # Backoff simples ou marcar tentativa (opcional)
                        
                    except Exception as e:
                        loggerError(f"Erro inesperado ao conectar com {peer}", exc_info=True)

        except Exception as e:
            loggerError("Erro crítico no loop do cliente (Discover/Connect)", exc_info=True)

        # Espera antes da próxima rodada de descoberta (evita flood no servidor)
        await asyncio.sleep(5) 


async def commandRedirection(client):
    """
    Gerencia a entrada do usuário e execução de comandos.
    Retorna 1 se o comando for sair, 0 caso contrário.
    """
    try:
        commands = await async_input("Digite o comando: ")
        
        # Previne erro se usuário der Enter vazio
        if not commands.strip():
            return 0
            
        commands = commands.split(" ")
        cmd = commands[0].lower() # Normaliza para minúsculo

        if cmd == "/peers":
            # Se não houver argumento, assume '*' (todos)
            arg = commands[1] if len(commands) > 1 else '*'
            await showPeers(arg, client)

        elif cmd == "/msg":
            if len(commands) < 3:
                print("Uso: /msg <peer_id> <mensagem>")
            else:
                target = commands[1]
                msg_content = ' '.join(commands[2:])
                await sendMessage(target, msg_content, client)

        elif cmd == "/pub":
            if len(commands) < 3:
                print("Uso: /pub <* | #namespace> <mensagem>")
            else:
                target = commands[1]
                msg_content = ' '.join(commands[2:])
                await pubMessage(target, msg_content, client)

        elif cmd == "/conn":
            await showConns(client)
            
        elif cmd == "/logon":
            level = commands[1].upper()
            if level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                print("Nível de log inválido! Use: DEBUG, INFO, WARNING, ERROR, CRITICAL")
            else:
                addLevel(level)

        elif cmd == "/logoff":
            level = commands[1].upper()
            if level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                print("Nível de log inválido! Use: DEBUG, INFO, WARNING, ERROR, CRITICAL")
            else:
                removeLevel(level)

        elif cmd == "/reconnect":
            await reconnectPeers(client)
            
        elif cmd == "/rtt":
            await showRtt(client)
        elif cmd == "/quit":
            await unregister(client.namespace, client.name, client.port)
            return 1
        
        elif cmd == "/help":
            await initialScreen()

        else:
            print("Comando inválido! Digite '/help' para ver comandos disponíveis.")
            
    except EOFError:
        # Captura Ctrl+D ou fim de stream
        return 1
    except Exception as e:
        loggerError("Erro processando comando", e)
        
    return 0

async def async_input(prompt: str = "") -> str:
    # define a função para tratar do input assíncrono do usuário
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: input(prompt))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass