"""Utilitaries for logging in package."""

import logging
from colorama import Fore, Style


def init_logger(log_level: int, package_name: str) -> logging.Logger:
    logging.basicConfig(level=logging.INFO, filename=f"{package_name}.log")
    logger = logging.getLogger(package_name)
    logger.setLevel(log_level)

    stream_formater = logging.Formatter(
        "%(asctime)s|%(levelname)s| %(pathname)s#%(lineno)d: > %(message)s",
        datefmt="%H:%M:%S",
    )
    stream_handler = CustomHandler(package_name=package_name)
    stream_handler.setFormatter(stream_formater)
    logger.addHandler(stream_handler)
    if log_level <= logging.DEBUG:
        print(f"{Fore.GREEN:-<15}DEBUG MODE{'':-<15} {Style.RESET_ALL}")
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get the logger for the current module given it's name.
    Args:
        name (str): Name of the module usualy obtained using '__name__'
    Returns:
        logging.Logger: Logger for the given module name.
    Example:
        >>> LOGGER = get_logger(__name__)
    """
    return logging.getLogger(name)


class CustomHandler(logging.StreamHandler):

    """Custom logging handler for colored console."""

    COLOR_BY_LEVEL = {
        "DEBUG": Fore.GREEN,
        "INFO": Fore.BLUE,
        "WARNING": Fore.YELLOW,
        "WARN": Fore.YELLOW,
        "ERROR": Fore.RED,
        "FATAL": Fore.RED,
        "CRITICAL": Fore.RED,
    }

    def __init__(self, *args, **kwargs):
        self.package_name = kwargs.pop("package_name", "root")
        super().__init__(*args, **kwargs)

    def emit(self, record: logging.LogRecord):
        record.pathname = (
            self.package_name + record.pathname.split(self.package_name)[-1]
        )

        level_color = self.COLOR_BY_LEVEL.get(record.levelname)
        record.levelname = f"{record.levelname: <8}"
        if level_color:
            record.levelname = level_color + record.levelname + Style.RESET_ALL
        return super().emit(record)
