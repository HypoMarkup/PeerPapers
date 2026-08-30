import logging
import sys


def setup_logger(name: str = "peerpapers", level: int = logging.INFO) -> logging.Logger:
    """Creates and configures a standard logger instance."""

    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(level)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)


    return logger


# Default global logger instance
logger = setup_logger()


def get_logger(module_name: str) -> logging.Logger:
    """Returns a child logger scoped to a specific module."""

    return setup_logger(f"peerpapers.{module_name}")
