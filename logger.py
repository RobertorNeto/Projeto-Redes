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

logLevels = ["INFO"]

class GlobalLevelFilter(logging.Filter):
    def filter(self, record):
        return record.levelname in logLevels

def removeLevel(level: str):
    level_upper = level.upper().strip()
    
    if level_upper in logLevels:
        logLevels.remove(level_upper)
        print(f"[-] Nível de log removido: {level_upper}")
    else:
        print(f"Nível {level_upper} não estava ativo.")

def addLevel(level: str):
    level_upper = level.upper().strip()
    valid_levels = LOG_PATHS.keys()
    
    if level_upper not in valid_levels:
        print(f"Nível inválido: {level_upper}. Use: {list(valid_levels)}")
        return

    if level_upper not in logLevels:
        logLevels.append(level_upper)
        print(f"[+] Nível de log adicionado: {level_upper}")
    else:
        print(f"Nível {level_upper} já está ativo.")

def setupLogger():
    for path in LOG_PATHS.values():
        os.makedirs(path, exist_ok=True)

    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG) 
    
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    
    level_filter = GlobalLevelFilter()

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    console.addFilter(level_filter)
    logger.addHandler(console)

    for level, path in LOG_PATHS.items():
        handler = logging.FileHandler(
            os.path.join(path, f"app_{TODAY}.log"),
            encoding="utf-8"
        )
        handler.setLevel(getattr(logging, level))
        handler.addFilter(lambda record, lvl=level: record.levelname == lvl)
        handler.addFilter(level_filter)
        handler.setFormatter(formatter)

        logger.addHandler(handler)

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