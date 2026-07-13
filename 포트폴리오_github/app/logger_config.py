import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logger(name: str = "ai-agent-quality") -> logging.Logger:
    """콘솔 로거. 운영에서는 파일/수집기 핸들러로 확장한다."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
