import logging

from .config import config


class DuplicateFilter(logging.Filter):
    def filter(self, record: logging.LogRecord):
        current_log = (record.module, record.levelno, record.msg)
        if current_log != getattr(self, "last_log", None):
            self.last_log = current_log
            return True
        return False


logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=config["logging_level"],
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger()
logger.addFilter(DuplicateFilter())
