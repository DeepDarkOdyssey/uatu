import logging

def get_logger():
    logger = logging.getLogger(__name__)
    formatter = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s:%(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger