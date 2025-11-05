from logger import *
from cli import *
from message_router import *
from p2p_transport import *
from rendezvous_client import *
from state import *

def main():
    ans = 0
    initialScreen()
    while not ans:
        ans = commandRedirection()


def commandRedirection():
    commands = str(input()).split(' ')
    if commands[0] == "/peers":
        showPeers()
    elif commands[0] == "/connect":
        connectPeers(commands[1])
    elif commands[0] == "/msg":
        commands.remove("/msg")
        sendMessage(commands)
    elif commands[0] == "/watch":
        logEnable()
    elif commands[0] == "/quit":
        print("Terminando execução...")
        return 1
    elif commands[0] == "/help":
        initialScreen()
    else:
        print("Comando inválido! Digite '/help' para saber comandos disponíveis.")
    return 0

main()