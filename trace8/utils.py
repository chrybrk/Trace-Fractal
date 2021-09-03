import inspect
import logging


__all__ = ("FONTS", "Logger")


class Logger:

    __slots__ = "logger"

    def __init__(self, name: str) -> None:
        self.logger = logging.getLogger(name)

    def create_logger(self):
        """
        Creates a logger instance.
        """
        handler = logging.StreamHandler()

        formatter = logging.Formatter(
            "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
        )
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

        return self.logger

    @staticmethod
    def generate_log(obj) -> str:
        """
        Forms a log for obj.
        """
        attrs = [
            attr
            for attr in inspect.getmembers(obj)
            if not inspect.ismethod(attr[1])
            if not attr[0].startswith("_")
        ]
        fmt = "\n".join(f"{attr}={repr(value)}" for attr, value in attrs)
        return fmt


FONTS = [
    0xF0,
    0x90,
    0x90,
    0x90,
    0xF0,  # 0
    0x20,
    0x60,
    0x20,
    0x20,
    0x70,  # 1
    0xF0,
    0x10,
    0xF0,
    0x80,
    0xF0,  # 2
    0xF0,
    0x10,
    0xF0,
    0x10,
    0xF0,  # 3
    0x90,
    0x90,
    0xF0,
    0x10,
    0x10,  # 4
    0xF0,
    0x80,
    0xF0,
    0x10,
    0xF0,  # 5
    0xF0,
    0x80,
    0xF0,
    0x90,
    0xF0,  # 6
    0xF0,
    0x10,
    0x20,
    0x40,
    0x40,  # 7
    0xF0,
    0x90,
    0xF0,
    0x90,
    0xF0,  # 8
    0xF0,
    0x90,
    0xF0,
    0x10,
    0xF0,  # 9
    0xF0,
    0x90,
    0xF0,
    0x90,
    0x90,  # A
    0xE0,
    0x90,
    0xE0,
    0x90,
    0xE0,  # B
    0xF0,
    0x80,
    0x80,
    0x80,
    0xF0,  # C
    0xE0,
    0x90,
    0x90,
    0x90,
    0xE0,  # D
    0xF0,
    0x80,
    0xF0,
    0x80,
    0xF0,  # E
    0xF0,
    0x80,
    0xF0,
    0x80,
    0x80,
]  # F
