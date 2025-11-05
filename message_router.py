####    Roteamento das mensagens (PUB, SUB, SEND)    ####

# 1. Funcionamento da conexão entre peers
#   a) Envio de mensagens ponto-a-ponto (unicast)
#   b) Envio de mensagens para os peers de um <namespace>
#   c) Envio de mensagens para todos os peers da rede (broadcast)

# 2. Detalhes de implementação
#   a) PONG a cada 30s
#   b) Desconexão se 3s sem um PONG de resposta
#   c) ttl das mensagens fixo em 1, com mensagem de erro caso contrário
#   d) Tamanho das mensagens fixo em 32kb, com mensagem de erro caso contrário

#   e) Quando do uso do SEND, deve-se
#       - Ter um campo 'require_ack' na solicitação do emissor, que exige um 'ack' do receptor
#       - Receptor deve enviar um 'ack' com o mesmo msg_id da requisição inicial (único)
#       - Caso não haja recebimento desse 'ack', a mensagem é considerada como não entregue

#   f) Sobre o msg_id (escolher 1 das opções de geração)
#       - Timestamp + número aleatório de n bits no fim (geração de id aleatório)
#       - Geração de um id com nome do emissor + número incrementado sequencialmente
#       - Todo peer deve guardar, sem repetição, os msg_ids já recebidos (evitar duplicatas)

def sendMessage(command):
    if command[0] == '*':
        return
    elif command[0][0] == '#':
        return
    elif command[0][0] == '@':
        return
    else:
        print("Formato de mensagem inválido! Digite '/help' para ver o uso correto.")