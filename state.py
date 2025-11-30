import asyncio
import time
from logger import *

MAX_RTT_HISTORY = 50

async def showPeers(arg, client):
    peers = {}

    if not hasattr(client, "peersConnected") or not client.peersConnected:
        print("Nenhuma informação de peers disponível.")
        return
    target_ns = None
    if arg and arg not in ["*", "all"]:
        target_ns = arg.lstrip("#")

    found_any = False
    
    for peer_id, data in client.peersConnected.items():
        try:
            name, namespace = peer_id.split("@", 1)
            
            if target_ns and namespace != target_ns:
                continue
                
            if namespace not in peers:
                peers[namespace] = []
            
            peers[namespace].append((name, data["status"], data["address"], data["port"]))
            found_any = True
        except ValueError:
            continue

    if not found_any:
        print("Nenhum peer encontrado para a consulta.")
        return

    print(f"\n--- Peers Conhecidos ({len(client.peersConnected)}) ---")
    for nspace, peer_list in peers.items():
        print(f"# {nspace}")
        for p in peer_list:
            status_icon = "🟢" if p[1] == "CONNECTED" else "🟡"
            print(f"\t{status_icon} {p[0]} [{p[2]}:{p[3]}] ({p[1]})")
    print("-----------------------------------\n")


async def showConns(client):
    """
    Mostra detalhes técnicos das conexões TCP (Sockets).
    """
    inbound = getattr(client, "inbound", set())
    outbound = getattr(client, "outbound", set())

    print(f"\n--- Conexões Ativas ---")
    print(f"⬇️  Inbound (Recebidas): {len(inbound)}")
    for i in inbound:
        print(f"\t- {i}")

    print(f"⬆️  Outbound (Iniciadas): {len(outbound)}")
    for o in outbound:
        print(f"\t- {o}")
    print("-----------------------\n")


async def updateRttTable(rtt_ms, peerPair, client):
    if not isinstance(peerPair, (list, tuple)) or len(peerPair) != 2:
        loggerWarning(f"RTT ignorado: Formato de par inválido: {peerPair}")
        return False

    a, b = str(peerPair[0]).strip(), str(peerPair[1]).strip()

    if not a or not b:
        loggerWarning("RTT ignorado: IDs de peer vazios.")
        return False

    key = tuple(sorted([a, b]))

    lock = getattr(client, "rtt_lock", None)
    if lock is None:
        client.rtt_lock = asyncio.Lock()
        lock = client.rtt_lock

    async with lock:
        table = getattr(client, "rtt_table", None)
        if table is None:
            client.rtt_table = {}
            table = client.rtt_table

        if key not in table:
            table[key] = {
                "history": [],
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "last_seen": 0,
                "count": 0
            }
        
        entry = table[key]
        now = time.time()

        try:
            val = float(rtt_ms)
            if val < 0: val = 0.0
        except ValueError:
            loggerError(f"Valor de RTT inválido: {rtt_ms}")
            return False

        entry["history"].append(val)
        
        if len(entry["history"]) > MAX_RTT_HISTORY:
            entry["history"].pop(0)

        entry["count"] = len(entry["history"])
        entry["avg"] = sum(entry["history"]) / entry["count"]
        entry["min"] = min(entry["history"])
        entry["max"] = max(entry["history"])
        entry["last_seen"] = now
    return True


async def showRtt(client):
    table = getattr(client, "rtt_table", None)
    
    if not table:
        print("\n🚫 Nenhum dado de latência (RTT) coletado ainda.")
        print("Certifique-se de estar conectado a outros peers e aguarde alguns segundos.\n")
        return

    lock = getattr(client, "rtt_lock", asyncio.Lock())
    async with lock:
        snapshot = {k: v.copy() for k, v in table.items()}

    if not snapshot:
        print("\n🚫 Tabela de RTT vazia.")
        return

    print(f"\n📊 Estatísticas de Latência (RTT) - {len(snapshot)} conexões")
    print(f"{'PAR DE PEERS':<50} | {'MÉDIA':<10} | {'MIN':<10} | {'MAX':<10} | {'ÚLTIMO'}")
    print("-" * 110)

    for key, v in snapshot.items():
        peer_a, peer_b = key
        pair_str = f"{peer_a} <-> {peer_b}"
        
        if len(pair_str) > 48:
            pair_str = pair_str[:45] + "..."

        avg = f"{v['avg']:.2f}ms"
        mn = f"{v['min']:.2f}ms"
        mx = f"{v['max']:.2f}ms"
        
        last_seen = time.strftime("%H:%M:%S", time.localtime(v['last_seen']))
        
        print(f"{pair_str:<50} | {avg:<10} | {mn:<10} | {mx:<10} | {last_seen}")
    
    print("-" * 110 + "\n")