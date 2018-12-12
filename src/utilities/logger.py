import logging
import os
import sys
from datatypes import AppSettings
from datetime import datetime
from pathlib import Path


def setup_custom_logger(name):
    app_settings = AppSettings()
    log_path = os.path.join(Path(app_settings.default_project_dir).parent, "logs")
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    date = datetime.now().strftime("%Y-%b-%d_%H-%M")
    log_name = os.path.join(log_path, f"log_hermes_{date}.log")
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-s [%(name)-s] %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler(log_name, mode="w")
    # handler = logging.handlers.TimedRotatingFileHandler(log_name, when="d", interval=1, backupCount=90)
    handler.setFormatter(formatter)
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.addHandler(screen_handler)
    return logger
