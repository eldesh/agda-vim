import logging

def init_logging(level=logging.WARNING):
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=level)

    root.setLevel(level=level)

def set_logging_level(level):
    logging.getLogger().setLevel(level=level)
