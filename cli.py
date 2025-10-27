####    Interface, parsing de comandos  ####

# 1. Implementação da Interface
#   a) '/peers' : mostra lista dos peers ativos
#   b) '/connect <peer_id>' : conexão direta
#   c) '/msg @<peer> <mensagem>' : mensagem direta
#   d) '/msg #<namespace> <mensagem>' : mensagem no namespace
#   e) '/msg *<mensagem>' : broadcast
#   f) '/watch' : habilitar log
#   g) '/quit' : sair do cliente