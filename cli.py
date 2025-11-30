####    Interface, parsing de comandos  ####

# 1. Implementação da Interface
#   a) '/peers' : mostra lista dos peers ativos
#   b) '/connect <peer_id>' : conexão direta
#   c) '/msg @<peer> <mensagem>' : mensagem direta
#   d) '/msg #<namespace> <mensagem>' : mensagem para o namespace
#   e) '/msg * <mensagem>' : mensagem de broadcast
#   f) '/watch' : habilitar log
#   g) '/quit' : sair do cliente

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
