import asyncio

class Client:
    # definicção da classe 'Cliente' para uso no pyp2p (nome, porta, namespace, lista de peers, e métricas)
    def __init__(self, name, port, namespace):
        self.name = name
        self.port = port
        self.namespace = namespace
        self.peersConnected = {} 
        self.pending_acks = {}    
        self.inbound = set()      
        self.outbound = set()     
        self.backoffTimer = {}   
        self.rtt_table = {}
        self.rtt_lock = asyncio.Lock()
        self.ping_timestamps = {}  

    # funções de atualização da lista de peers quando da desconexão
    def removePeerPing(self, peer_id: str):
        if peer_id in self.peersConnected:
            self.peersConnected[peer_id]["status"] = "LOST"

    def removePeer(self, peer_id: str):
        if peer_id in self.peersConnected:
            self.peersConnected[peer_id]["status"] = "CLOSED"
