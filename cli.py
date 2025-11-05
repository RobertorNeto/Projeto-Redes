####    Interface, parsing de comandos  ####

# 1. Implementação da Interface
#   a) '/peers' : mostra lista dos peers ativos
#   b) '/connect <peer_id>' : conexão direta
#   c) '/msg @<peer> <mensagem>' : mensagem direta
#   d) '/msg #<namespace> <mensagem>' : mensagem para o namespace
#   e) '/msg * <mensagem>' : mensagem de broadcast
#   f) '/watch' : habilitar log
#   g) '/quit' : sair do cliente

def initialScreen():
    print("\nBem-vindo ao pyp2p! Veja os comandos possíveis")
    print("")
    print("'/peers' : mostra lista dos peers ativos")
    print("'/connect <peer_id>' : conexão direta")
    print("'/msg @<peer> <mensagem>' : mensagem direta")
    print("'/msg #<namespace> <mensagem>' : mensagem para o namespace")
    print("'/msg * <mensagem>' : mensagem de broadcast")
    print("'/watch' : habilitar log")
    print("'/quit' : sair do cliente")
    print("'/help' : visualizar os comandos novamente\n")
