#### Critérios de correção / Checklist ####
# - [X] CLI com `/peers`, `/connect`, `/msg` (`@peer`, `#namespace`, `*`), `/routes`, `/watch`.  
# - [X] `REGISTER/DISCOVER/UNREGISTER` + atualização automática da lista.  
# - [ ] Servidor e cliente TCP entre peers; `HELLO/HELLO_OK`; `PING/PONG`.  
# - [ ] Envio `SEND` (unicast) com **ACK obrigatório**.  
# - [ ] `PUB` para `#namespace` e `*` com TTL + deduplicação.    
# - [ ] Tratamento de **erros** conforme tabela.  
# - [ ] Logs e `/routes` com vizinhos/rotas/RTT.  