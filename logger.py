import logging
import os
from datetime import datetime

LOG_DIR = "logs"
TODAY = datetime.now().strftime("%Y%m%d")

LOG_PATHS = {
    "INFO": os.path.join(LOG_DIR, "info"),
    "ERROR": os.path.join(LOG_DIR, "error"),
    "DEBUG": os.path.join(LOG_DIR, "debug"),
    "WARNING": os.path.join(LOG_DIR, "warning"),
}

# Definimos a lista globalmente
logLevels = []

# --- CLASSE DE FILTRO PERSONALIZADO ---
class GlobalLevelFilter(logging.Filter):
    """
    Filtro dinâmico: ele consulta a lista global 'logLevels'
    toda vez que um log tenta passar.
    """
    def filter(self, record):
        # Verifica se o nível da mensagem está na lista global atual
        return record.levelname in logLevels

# --- FUNÇÕES DE CONTROLE (MODIFICADAS) ---

def removeLevel(level: str):
    """Remove um nível da configuração global de log."""
    level_upper = level.upper().strip() # Garante formato correto (ex: "info " -> "INFO")
    
    if level_upper in logLevels:
        logLevels.remove(level_upper)
        print(f"[-] Nível de log removido: {level_upper}")
    else:
        print(f"Nível {level_upper} não estava ativo.")

def addLevel(level: str):
    """Adiciona um nível à configuração global de log."""
    level_upper = level.upper().strip()
    
    # Validamos se é um nível conhecido para evitar lixo na lista
    valid_levels = LOG_PATHS.keys()
    
    if level_upper not in valid_levels:
        print(f"Nível inválido: {level_upper}. Use: {list(valid_levels)}")
        return

    if level_upper not in logLevels:
        logLevels.append(level_upper)
        print(f"[+] Nível de log adicionado: {level_upper}")
    else:
        print(f"Nível {level_upper} já está ativo.")

# --- SETUP ---

def setupLogger():
    for path in LOG_PATHS.values():
        os.makedirs(path, exist_ok=True)

    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG) 
    
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    
    # Instancia nosso filtro
    level_filter = GlobalLevelFilter()

    # --- CONFIGURAÇÃO DO CONSOLE (TELA) ---
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    console.addFilter(level_filter) # Aplica o filtro dinâmico
    logger.addHandler(console)

    # --- CONFIGURAÇÃO DOS ARQUIVOS ---
    for level, path in LOG_PATHS.items():
        handler = logging.FileHandler(
            os.path.join(path, f"app_{TODAY}.log"),
            encoding="utf-8"
        )
        handler.setLevel(getattr(logging, level))
        
        # Filtro 1: Garante pureza do arquivo (arquivo de info só tem info)
        handler.addFilter(lambda record, lvl=level: record.levelname == lvl)
        
        # Filtro 2: Verifica se o usuário quer esse log no momento
        handler.addFilter(level_filter) 

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Log inicial para provar que funciona
    # loggerInfo("Logger inicializado.") # Comentei para não poluir se INFO estiver off

# Inicializa o logger globalmente
logger = logging.getLogger("app")

def loggerInfo(msg: str):
    logger.info(msg)

def loggerWarning(msg: str):
    logger.warning(msg)

def loggerError(msg: str, exception: Exception | None = None):
    if exception:
        logger.error(f"{msg}: {exception}", exc_info=True)
    else:
        logger.error(msg)

def loggerDebug(msg: str):
    logger.debug(msg)