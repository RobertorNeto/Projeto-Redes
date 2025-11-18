import logging
import os
from datetime import datetime

LOG_DIR = "logs"
TODAY = datetime.now().strftime("%Y%m%d")

# pastas por nível
LOG_PATHS = {
    "INFO": os.path.join(LOG_DIR, "info"),
    "ERROR": os.path.join(LOG_DIR, "error"),
    "DEBUG": os.path.join(LOG_DIR, "debug"),
    "WARNING": os.path.join(LOG_DIR, "warning"),
}

def setupLogger():
    for path in LOG_PATHS.values():
        os.makedirs(path, exist_ok=True)

    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)

    # cria handlers separados por nível
    for level, path in LOG_PATHS.items():
        handler = logging.FileHandler(
            os.path.join(path, f"app_{TODAY}.log"),
            encoding="utf-8"
        )
        handler.setLevel(getattr(logging, level))
        handler.addFilter(lambda record, lvl=level: record.levelname == lvl)

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.addHandler(console)
    logger.info("Logger inicializado.")

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