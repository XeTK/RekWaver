import logging

DESTINATION = '/Volumes/KINGSTON/wavs'

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def set_verbose(enabled: bool):
    if enabled:
        logging.getLogger().setLevel(logging.DEBUG)


def set_log_file(path: str, level: str = 'INFO'):
    """Attach a file handler that logs at the given level to the specified path."""
    levelno = getattr(logging, level.upper(), logging.INFO)
    fh = logging.FileHandler(path)
    fh.setLevel(levelno)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    fh.setFormatter(formatter)
    logging.getLogger().addHandler(fh)
