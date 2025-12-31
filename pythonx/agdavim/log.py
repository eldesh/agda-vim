import logging

def init_logging(level: int = logging.WARNING):
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=level)

    root.setLevel(level=level)

def set_logging_level(level: int):
    logging.getLogger().setLevel(level=level)
