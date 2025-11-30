import asyncio

class Client:

    def __init__(self, name, port, namespace):
        self.name = name
        self.port = port
        self.namespace = namespace
        self.peersConnected = {}  # peer_id -> {address, port, status, writer?}
        self.pending_acks = {}    # msg_id -> Future
        self.inbound = set()      # peers que iniciaram conexão conosco
        self.outbound = set()     # peers que iniciamos conexão
        self.backoffTimer = {}    # peer_id -> [tentativas, proximo_delay]
        self.rtt_table = {}
        self.rtt_lock = asyncio.Lock()
        self.ping_timestamps = {}  # Níveis de log habilitados

    def removePeerPing(self, peer_id: str):
        """Marca peer como perdido após falha de PING."""
        if peer_id in self.peersConnected:
            self.peersConnected[peer_id]["status"] = "LOST"

    def removePeer(self, peer_id: str):
        """Marca peer como encerrado (BYE)."""
        if peer_id in self.peersConnected:
            self.peersConnected[peer_id]["status"] = "CLOSED"
