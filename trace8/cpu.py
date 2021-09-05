import random
from collections import deque

import pygame

from .utils import FONTS, Logger

__all__ = ("CPU",)
pygame.init()


class CPU:

    __slots__ = (
        "_log",
        "_memory",
        "_display_buffer",
        "_logflag",
        "V",
        "pc",
        "I",
        "st",
        "dt",
        "stack",
        "opcode",
        "keymap",
        "draw_flag",
    )

    def __init__(self, *, log: bool = True) -> None:

        self.keymap = [0] * 16  # 16 available keys

        self.arm_registers()
        self.arm_memory_units()
        self.load_fonts()

        self.opcode: int = 0
        self.draw_flag = False

        self._log = Logger(__name__)
        self._logflag = log

    @property
    def _vx(self):
        """
        lower 4 bits of the high byte of the instruction.
        """
        return (self.opcode & 0x0F00) >> 8

    @property
    def _vy(self):
        """
        upper 4 bits of the low byte of the instruction.
        """
        return (self.opcode & 0x00F0) >> 4

    @property
    def _kk(self):
        """
        lowest 8 bit of instructions.
        """
        return self.opcode & 0x00FF

    @property
    def _nn(self):
        """
        lowest 4 bits of instructions.
        """
        return self.opcode & 0x000F

    @property
    def _nnn(self):
        """
        lowest 12 bits of the instructions.
        """
        return self.opcode & 0x0FFF

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

    def arm_keyboard(self):
        """
        Initializes keyboard.
        """
        k_inps = pygame.key.get_pressed()

        self.keymap[0] = k_inps[pygame.K_1]
        self.keymap[1] = k_inps[pygame.K_2]
        self.keymap[2] = k_inps[pygame.K_3]
        self.keymap[3] = k_inps[pygame.K_4]
        self.keymap[4] = k_inps[pygame.K_q]
        self.keymap[5] = k_inps[pygame.K_w]
        self.keymap[6] = k_inps[pygame.K_e]
        self.keymap[7] = k_inps[pygame.K_r]
        self.keymap[8] = k_inps[pygame.K_a]
        self.keymap[9] = k_inps[pygame.K_s]
        self.keymap[10] = k_inps[pygame.K_d]
        self.keymap[11] = k_inps[pygame.K_f]
        self.keymap[12] = k_inps[pygame.K_z]
        self.keymap[13] = k_inps[pygame.K_x]
        self.keymap[14] = k_inps[pygame.K_c]
        self.keymap[15] = k_inps[pygame.K_v]

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
                    i + self.pc
                ] = bnry  # loading ROM in locations after fontset.

    def debugworks(self) -> None:
        """
        Writes debug log.
        """
        lgr = self._log.create_logger()
        lgr.debug(self._log.generate_log(self))

    def op_CLS(self):
        """
        0x00E0 - Cleans the screen
        """
        ...

    def op_LD_Vx_byte(self):
        """
        0x6000 - Loads kk on the registers.
        """
        self.V[self._vx] = self._kk

    def op_LD_I_ADDR(self):
        """
        0xa000 - Loads index register.
        """
        self.I = self._nnn  # noqa E741

    def op_DRW_Vx_Vy_nibble(self):
        """
        0xd000 - Draws Vx and Vy on screen.
        """
        ...

    def op_CALL_ADDR(self):
        """
        0x2000 - Call subroutine at nnn.
        """
        self.stack.append(self.pc)
        self.pc = self._nnn

    def op_CALL_F(self):
        """
        0xF000 - switches to Fx opcodes.
        """
        exop = self.opcode & 0xF0FF
        self._opmap[exop]()

    def op_LD_B_Vx(self):
        """
        0xF033 - Store BCD representation of Vx in memory locations I, I+1, and I+2.
        """
        vx = self.V[self._vx]
        idx = self.I

        self._memory[idx] = vx // 100
        self._memory[idx + 1] = (vx % 100) // 10
        self._memory[idx + 2] = vx % 10

    def op_LD_Vx_I(self):
        """
        0xF065 - Fills registers V0 through Vx from memory starting at location I.
        """
        for i in range(self._vx):
            self.V[i] = self._memory[self.I + i]
        self.I += (self._vx) + 1  # noqa E741

    def op_LD_F_Vx(self):
        """
        0xf029 - Set I = location of sprite for digit Vx.
        """
        self.I = (5 * (self.V[self._vx])) & 0xFFF  # noqa E741

    def op_ADD_Vx_byte(self):
        """
        0x7000 - Set Vx = Vx + kk.
        """
        self.V[self._vx] += self.opcode & 0xFF

    def op_SYS_addr(self):
        """
        0x0000 - Jump to a machine code routine at nnn.
        """
        extracted_op = self.opcode & 0xF0FF
        self._opmap[extracted_op]()

    def op_RET(self):
        """
        0x000EE - Return from a subroutine.
        """
        self.pc = self.stack.pop()

    def op_LD_DT_Vx(self):
        """
        0xFO15 - Set delay timer = Vx.
        """
        self.dt = self.V[self._vx]

    def op_LD_Vx_DT(self):
        """
        0xF007 - Set Vx = delay timer value.
        """
        self.V[self._vx] = self.dt

    def op_SE_Vx_byte(self):
        """
        0x3000 - Skip next instruction if Vx = kk.
        """
        if self.V[self._vx] == self._kk:
            self.pc += 2

    def op_JP_addr(self):
        """
        0x1000 - Jump to location nnn.
        """
        self.pc = self._nnn

    def op_RND_Vx_byte(self):
        """
        0xC000 - Set Vx = random byte AND kk.
        """
        rnum = random.randrange(0, 256) & self._kk
        self.V[self._vx] = rnum

    def op_CALL_E(self):
        """
        0xE000 - Switches to Ex opcodes.
        """
        exop = self.opcode & 0xF00F
        self._opmap[exop]()

    def op_SKNP_Vx(self):
        """
        0xE001 - Skip next instruction if key with the value of Vx is not pressed.
        """
        if not self.keymap[self.V[self._vx]]:
            self.pc += 2

    def op_CALL_8(self):
        """
        0x8000 - switches to 8x opcodes.
        """
        exop = (self.opcode & 0xF00F) + 0xFF0

        self._opmap[exop]()

    def op_AND_Vx_Vy(self):
        """
        0x8ff2 - Set Vx = Vx AND Vy.
        """
        self.V[self._vx] &= self.V[self._vy]
        self.V[self._vx] &= 0xFF

    def op_ADD_Vx_Vy(self):
        """
        0x8ff4 - Set Vx = Vx + Vy, set VF = carry.
        """
        op = self.V[self._vx] + self.V[self._vy]
        self.V[0xF] = 1 if op > 0xFF else 0
        op &= 0xFF
        self.V[self._vx] = op

    def op_SNE_Vx_byte(self):
        """
        0x4000 - Skip next instruction if Vx != kk.
        """
        if self.V[self._vx] != self._kk:
            self.pc += 2

    def op_LD_Vx_Vy(self):
        """
        0x8ff0 - Set Vx = Vy.
        """
        self.V[self._vx] = self.V[self._vy]
        self.V[self._vx] &= 0xFF

    def op_SUB_Vx_Vy(self):
        """
        0x8ff5 - Set Vx = Vx - Vy, set VF = NOT borrow.
        """
        if self.V[self._vx] > self.V[self._vy]:
            self.V[0xF] = 1
        else:
            self.V[0xF] = 0
        self.V[self._vx] -= self.V[self._vy]
        self.V[self._vx] &= 0xFF

    def op_LD_ST_Vx(self):
        """
        0xf018 - Set sound timer = Vx.
        """
        self.st = self.V[self._vx]

    @property
    def _opmap(self):
        """
        property for storing subroutines.
        """
        opmap = {
            0x00E0: self.op_CLS,
            0x6000: self.op_LD_Vx_byte,
            0xA000: self.op_LD_I_ADDR,
            0xD000: self.op_DRW_Vx_Vy_nibble,
            0x2000: self.op_CALL_ADDR,
            0xF000: self.op_CALL_F,
            0xF033: self.op_LD_B_Vx,
            0xF065: self.op_LD_Vx_I,
            0xF029: self.op_LD_F_Vx,
            0x7000: self.op_ADD_Vx_byte,
            0x0000: self.op_SYS_addr,
            0x00EE: self.op_RET,
            0xF015: self.op_LD_DT_Vx,
            0xF007: self.op_LD_Vx_DT,
            0x3000: self.op_SE_Vx_byte,
            0x1000: self.op_JP_addr,
            0xC000: self.op_RND_Vx_byte,
            0xE000: self.op_CALL_E,
            0xE001: self.op_SKNP_Vx,
            0x8000: self.op_CALL_8,
            0x8FF2: self.op_AND_Vx_Vy,
            0x8FF4: self.op_ADD_Vx_Vy,
            0x4000: self.op_SNE_Vx_byte,
            0x8FF0: self.op_LD_Vx_Vy,
            0x8FF5: self.op_SUB_Vx_Vy,
            0xF018: self.op_LD_ST_Vx,
        }
        return opmap

    def fetch_op(self):
        """
        Fetches the current opcode.
        """
        opcode = (self._memory[self.pc] << 8) | (self._memory[self.pc + 1])
        self.opcode = opcode

    def cycle(self):
        """
        The main execution cycle of cpu.
        """
        self.arm_keyboard()
        self.fetch_op()
        exop = self.opcode & 0xF000

        self._opmap[exop]()
        self.pc += 0 if exop in [0x2000, 0x00EE, 0x1000] else 2
    #    if self._logflag:
        #    self.debugworks()

        self.dt -= 1 if self.dt > 0 else 0
        if self.st > 0:
            print(self.st)
            self.st -= 1
            if self.st == 0:
                ...
