####    Registro de logs / erros    ####

# 1. Diagnóstico / Estatísticas
#   Logs obrigatórios: conexões estabelecidas, mensagens enviadas/recebidas, erros.  

# 2. Níveis de Log
#   a) Informações Gerais -> logger.info(...)
#       - `client_started`
#       - `client_stopped`
#       - `peer_connected`
#       - `peer_disconnected`
#       - `message_sent`
#       - `message_received`


#   b) Sobre Tratamento de erros -> logger.error(...)
#       - `bad_format`
#       - `p2p_unknown_command`
#       - `internal_error`
#       - `ack_timeout`
#       - `message_too_large`

import logging
import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d')}.log")

def setupLogger():
    """Inicializa e configura o logger principal."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

    logging.info("Logger inicializado.")

logger = logging.getLogger("app")

def info(msg: str):
    """Utilizado para logar informações gerais"""
    logger.info(msg)

def warning(msg: str):
    """Utilizado para logar avisos (não necessariamente erros, mas pontos de atenção)"""
    logger.warning(msg)

def error(msg: str, exception: Exception | None = None):
    """Utilizado para erros ou erros + exception"""
    if exception:
        logger.error(f"{msg}: {exception}", exc_info=True)
    else:
        logger.error(msg)

def debug(msg: str):
    """Utilizado para debugs"""
    logger.debug(msg)