import datetime
import logging

from .config import config

logger = logging.getLogger("mc-router-dns-manager")
logger.setLevel(config["logging_level"])

logging_handler = logging.StreamHandler()
logging_formatter = logging.Formatter(
    fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logging_handler.setFormatter(logging_formatter)
logger.addHandler(logging_handler)


if config["logging_level"] != "DEBUG":

    class DuplicateFilter(logging.Filter):
        def filter(self, record: logging.LogRecord):
            hour = datetime.datetime.now().hour
            current_log = (record.module, record.levelno, record.msg, hour)
            if current_log != getattr(self, "last_log", None):
                self.last_log = current_log
                return True
            return False

    logger.addFilter(DuplicateFilter())
