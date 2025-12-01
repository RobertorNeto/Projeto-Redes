####    Interface, parsing de comandos  ####

# printa a tela inicial com os comandos possíveis
async def initialScreen():
    print("\nBem-vindo ao pyp2p! Veja os comandos possíveis")
    print("")
    print("'/peers [* | #namespace]' : mostra lista dos peers ativos")
    print("'/reconnect' : tenta reconexão")
    print("'/conn' : mostra as conexões disponíveis")
    print("'/msg <peer_id> <mensagem>' : mensagem direta")
    print("'/pub #<namespace> <mensagem>' : mensagem para o namespace")
    print("'/pub * <mensagem>' : mensagem de broadcast")
    print("'/rtt' : mostra latências (RTT) para peers conectados")
    print("'/logon <nivel>' : habilitar log")
    print("'/logoff <nivel>' : desabilitar log")
    print("'/quit' : sair do cliente")
    print("'/help' : visualizar os comandos novamente\n")

def clearOSScreen():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')
