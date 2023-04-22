import logging
import sys


class Log:
    logger = logging.getLogger()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
    )

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
    def debug(cls, *args, **kw):
        cls.logger.debug(*args, **kw)

    @classmethod
    def info(cls, *args, **kw):
        cls.logger.info(*args, **kw)

    @classmethod
    def warning(cls, *args, **kw):
        cls.logger.warning(*args, **kw)

    @classmethod
    def error(cls, *args, **kw):
        cls.logger.error(*args, **kw)

    @classmethod
    def critical(cls, *args, **kw):
        cls.logger.critical(*args, **kw)

    @classmethod
    def exception(cls, error, *args, **kw):
        cls.logger.debug(f"Error: {error}", exc_info=True)

    @classmethod
    def flush(cls):
        for handler in cls.logger.handlers:
            handler.flush()


def debug(*args, **kw):
    Log.debug(*args, **kw)


def info(*args, **kw):
    Log.info(*args, **kw)


def warning(*args, **kw):
    Log.warning(*args, **kw)


def error(*args, **kw):
    Log.error(*args, **kw)


def critical(*args, **kw):
    Log.critical(*args, **kw)


def exception(*args, **kw):
    Log.exception(*args, **kw)


def flush(*args, **kw):
    Log.flush(*args, **kw)
