import logging
import sys
from contextlib import contextmanager


class Log:
    logger = logging.getLogger()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )
    prefixes = []

    @classmethod
    def _format_msg(cls, msg):
        return " ".join([*cls.prefixes, str(msg)])

    @classmethod
    def init(cls):
        cls.logger.setLevel(logging.DEBUG)

        default_handler = logging.StreamHandler(sys.stdout)
        default_handler.setFormatter(cls.formatter)

        cls.logger.addHandler(default_handler)

    @classmethod
    def add_handler(cls, handler):
        handler.setFormatter(cls.formatter)
        cls.logger.addHandler(handler)

    @classmethod
    def debug(cls, msg, *args, **kw):
        cls.logger.debug(cls._format_msg(msg), *args, **kw)

    @classmethod
    def info(cls, msg, *args, **kw):
        cls.logger.info(cls._format_msg(msg), *args, **kw)

    @classmethod
    def warning(cls, msg, *args, **kw):
        cls.logger.warning(cls._format_msg(msg), *args, **kw)

    @classmethod
    def error(cls, msg, *args, **kw):
        cls.logger.error(cls._format_msg(msg), *args, **kw)

    @classmethod
    def critical(cls, msg, *args, **kw):
        cls.logger.critical(cls._format_msg(msg), *args, **kw)

    @classmethod
    def exception(cls, error, *args, **kw):
        cls.logger.debug(f"Error: {error}", exc_info=True)

    @classmethod
    def flush(cls):
        for handler in cls.logger.handlers:
            handler.flush()

    @classmethod
    @contextmanager
    def prefix(cls, text):
        cls.prefixes.append(text)
        yield
        cls.prefixes.pop()


debug = Log.debug
info = Log.info
warning = Log.warning
error = Log.error
critical = Log.critical
exception = Log.exception
flush = Log.flush
prefix = Log.prefix
