from .conf import FONTS

__all__ = ("CPU", )


class CPU:

    __slots__ = ("log", "memory", "display_buffer")

    def __init__(self, *, log=True):
        self.log = log

        self.arm_memory_units()
        self.load_fonts()

    def arm_memory_units(self):
        """
        Initializes memory and Regen Buffer
        """
        # 4 KBs of RAM as per standard limit for CHIP8 module.
        # Using 0 to represent an empty mem loc.
        self.memory = [0] * 4096

        # Display Buffer/Memory as per standard limit for CHIP8.
        # For storing the pixel state on the display.
        self.display_buffer = [0] * 64 * 32

    def load_fonts(self):
        """
        Loads fonts in the memory.
        """
        for i, item in enumerate(FONTS):
            self.memory[i] = item
