import logging

from collections import deque

from .utils import FONTS, Logger

__all__ = ("CPU",)


class CPU:

    __slots__ = (
        "_log",
        "_memory",
        "_display_buffer",
        "V",
        "pc",
        "I",
        "st",
        "dt",
        "stack",
        "opcode",
    )

    def __init__(self, *, log: bool = True) -> None:

        self.arm_registers()
        self.arm_memory_units()
        self.load_fonts()

        self.opcode: int = 0

        self._log = Logger(__name__)

        if log:
            self.debugworks()

    def arm_memory_units(self) -> None:
        """
        Initializes memory and Regen Buffer
        """
        # 4 KBs of RAM as per standard limit for CHIP8 module.
        # Using 0 to represent an empty mem loc.
        self._memory = [0] * 4096

        # Display Buffer/Memory as per standard limit for CHIP8.
        # For storing the pixel state on the display.
        self._display_buffer = [0] * 64 * 32

    def arm_registers(self):
        """
        Initializes registers.
        """
        self.V = [0] * 16  # 16 general purpose registers.
        self.pc = 0x200  # program counter starting at 0x200'th (or 512'th) mem loc.

        # Index counter for storing memory addresses.
        self.I = 0  # noqa E741

        # CPU interupts.
        self.st = 0
        self.dt = 0

        # A stack for storing program counter states.
        self.stack: deque = deque()

    def load_fonts(self) -> None:
        """
        Loads fonts in the memory.
        """
        for i, item in enumerate(FONTS):
            self._memory[i] = item

    def load_rom(self, path: str) -> None:
        """
        loads ROM in memory.
        """
        with open(path, "rb") as rom:
            for i, bnry in enumerate(rom.read()):
                self._memory[
                    i + 0x200
                ] = bnry  # loading ROM in locations after fontset.

    def debugworks(self) -> None:
        """
        Writes debug log.
        """
        lgr = self._log.create_logger()
        lgr.debug(self._log.generate_log(self))
