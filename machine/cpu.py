from __future__ import annotations

import os
import random
import time
import typing as t

import pygame

from devices import FONTS, Display, KeyPad

pygame.init()
pygame.display.set_caption("Trace-Fractal")

if t.TYPE_CHECKING:
    from io import FileIO


class CPU:
    def __init__(self, speed=5, window_size=(32, 64)) -> None:
        self.display = Display(*window_size)
        self.keypad = KeyPad()

        self.memory = bytearray(4096)
        self.stack = [0] * 16

        self.pc = 0x200
        self.gpio = [0] * 16
        self.stack_pointer = 0
        self.I = 0
        self.st = 0
        self.dt = 0

        self.opcode = 0

        self.now = time.time()
        self.speed = speed
        self.FPS = 20

        self.halt = False
        self.draw_flag = False

    # VARIABLES

    @property
    def nnn(self) -> int:
        """
        lowest 12 bits of the instructions.
        """
        return self.opcode & 0xFFF

    @property
    def nn(self) -> int:
        """
        lowest 4 bits of instructions.
        """
        return self.opcode & 0x000F

    @property
    def kk(self) -> int:
        """
        lowest 8 bit of instructions.
        """
        return self.opcode & 0x00FF

    @property
    def Vx(self) -> int:
        """
        lower 4 bits of the high byte of the instruction.
        """
        return (self.opcode & 0x0F00) >> 8

    @property
    def Vy(self) -> int:
        """
        upper 4 bits of the low byte of the instruction.
        """
        return (self.opcode & 0x00F0) >> 4

    # STANDARD OPERATIONS
    # TODO: Add Super C8 operations.

    def SYS_addr(self) -> None:
        """
        0x0000 - Jump to a machine code routine at nnn.
        """
        match self.opcode:
            case 0x0:
                pass
            case 0xE0:
                self.CLS()
            case _:
                decode = self.opcode & 0xF00F

                try:
                    self.functions[decode]()
                except KeyError:
                    self.pc += 2

    def CLS(self) -> None:
        """
        0x00E0 - Cleans the screen
        """
        self.draw_flag = True
        self.display.clear()
        self.pc += 2

    def RET(self) -> None:
        """
        0x000EE - Return from a subroutine.
        """
        self.pc = self.stack[self.stack_pointer] + 2
        self.stack_pointer -= 1

    def JP_addr(self) -> None:
        """
        0x1000 - Jump to location nnn.
        """
        self.pc = self.opcode & 0xFFF

    def CALL_addr(self) -> None:
        """
        0x2000 - Call subroutine at nnn.
        """
        self.stack_pointer += 1
        self.stack[self.stack_pointer] = self.pc
        self.pc = self.nnn

    def SE_Vx_byte(self) -> None:
        """
        0x3000 - Skip next instruction if Vx = kk.
        """
        if self.gpio[self.Vx] == self.kk:
            self.pc += 4
        else:
            self.pc += 2

    def SNE_Vx_byte(self) -> None:
        """
        0x4000 - Skip next instruction if Vx != kk.
        """
        if self.gpio[self.Vx] != self.kk:
            self.pc += 4
        else:
            self.pc += 2

    def SE_Vx_Vy(self) -> None:
        """
        0x5000 - Skip next instruction if Vx = Vy.
        """
        if self.gpio[self.Vx] == self.gpio[self.Vy]:
            self.pc += 4
        else:
            self.pc += 2

    def LD_Vx_byte(self) -> None:
        """
        0x6000 - Set Vx = kk.
        """
        self.gpio[self.Vx] = self.kk
        self.pc += 2

    def ADD_Vx_byte(self) -> None:
        """
        0x7000 - Set Vx = Vx + kk.
        """
        self.gpio[self.Vx] += self.kk
        self.gpio[self.Vx] &= 0xFF
        self.pc += 2

    def CALL_8(self) -> None:
        """
        0x8000 - switches to 8x opcodes.
        """
        match self.nn:
            case 0x0:
                self.LD_Vx_Vy()
            case _:
                decode = self.opcode & 0xF00F
                try:
                    self.functions[decode]()
                except KeyError:
                    self.pc += 2

    def LD_Vx_Vy(self) -> None:
        """
        0x8000 - Set Vx = Vy.
        """
        self.gpio[self.Vx] = self.gpio[self.Vy]
        self.gpio[self.Vx] &= 0xFF
        self.pc += 2

    def OR_Vx_Vy(self) -> None:
        """
        0x8001 - Set Vx = Vx OR Vy.
        """
        self.gpio[self.Vx] |= self.gpio[self.Vy]
        self.gpio[self.Vx] &= 0xFF
        self.pc += 2

    def AND_Vx_Vy(self) -> None:
        """
        0x8002 - Set Vx = Vx AND Vy.
        """
        self.gpio[self.Vx] &= self.gpio[self.Vy]
        self.gpio[self.Vx] &= 0xFF
        self.pc += 2

    def XOR_Vx_Vy(self) -> None:
        """
        0x8003 - Set Vx = Vx XOR Vy.
        """
        self.gpio[self.Vx] ^= self.gpio[self.Vy]
        self.gpio[self.Vx] &= 0xFF
        self.pc += 2

    def ADD_Vx_Vy(self) -> None:
        """
        0x8004 - Set Vx = Vx + Vy, set VF = carry.
        """
        value = self.gpio[self.Vx] + self.gpio[self.Vy]

        if value > 0xFF:
            self.gpio[0xF] = 1
        else:
            self.gpio[0xF] = 0

        self.gpio[self.Vx] = value
        self.gpio[self.Vx] &= 0xFF
        self.pc += 2

    def SUB_Vx_Vy(self) -> None:
        """
        0x8005 - Set Vx = Vx - Vy, set VF = NOT borrow.
        """
        if self.gpio[self.Vx] < self.gpio[self.Vy]:
            self.gpio[0xF] = 0
        else:
            self.gpio[0xF] = 1

        self.gpio[self.Vx] -= self.gpio[self.Vy]
        self.gpio[self.Vx] &= 0xFF
        self.pc += 2

    def SHR_Vx_Vy(self) -> None:
        """
        0x8006 - Set Vx = Vx SHR 1.
        """
        self.gpio[0xF] = self.gpio[self.Vx] & 0x1
        self.gpio[self.Vx] = self.gpio[self.Vx] >> 1
        self.gpio[self.Vx] &= 0xFF
        self.pc += 2

    def SUBN_Vx_Vy(self) -> None:
        """
        0x8007 - Set Vx = Vy - Vx, set VF = NOT borrow.
        """
        if self.gpio[self.Vx] > self.gpio[self.Vy]:
            self.gpio[0xF] = 0
        else:
            self.gpio[0xF] = 1

        self.gpio[self.Vx] = self.gpio[self.Vy] - self.gpio[self.Vx]
        self.gpio[self.Vx] &= 0xFF
        self.pc += 2

    def SHL_Vx_Vy(self) -> None:
        """
        0x800E - Set Vx = Vx SHL 1.
        """
        self.gpio[0xF] = self.gpio[self.Vx] >> 7
        self.gpio[self.Vx] = self.gpio[self.Vx] << 1
        self.pc += 2

    def SNE_Vx_Vy(self) -> None:
        """
        0x9000 - Skip next instruction if Vx != Vy.
        """
        if self.gpio[self.Vx] != self.gpio[self.Vy]:
            self.pc += 4
        else:
            self.pc += 2

    def LD_I_addr(self) -> None:
        """
        0xA000 - Set I = nnn.
        """
        self.I = self.nnn
        self.pc += 2

    def JP_V0_addr(self) -> None:
        """
        0xB000 - Jump to location nnn + V0.
        """
        self.pc = self.nnn + self.gpio[0x0]

    def RND_Vx_byte(self) -> None:
        """
        0xC000 - Set Vx = random byte AND kk.
        """
        self.gpio[self.Vx] = random.randint(0, 255) & self.kk
        self.pc += 2

    def DRW_Vx_Vy_nibble(self) -> None:
        """
        0xD000 - Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision.
        """
        width = 8
        height = self.opcode & 0xF
        self.gpio[0xF] = 0

        for r in range(height):
            px = self.memory[self.I + r]

            for c in range(width):
                if (px & 0x80) > 0:
                    erased = self.display.draw(
                        self.gpio[self.Vx] + c, self.gpio[self.Vy] + r
                    )
                    if erased:
                        self.gpio[0xF] = 1
                px <<= 1

        self.draw_flag = True
        self.pc += 2

    def CALL_E(self) -> None:
        """
        0xE000 - Execute subroutine at Ex.
        """
        try:
            self.functions[self.opcode & 0xF00F]()
        except KeyError:
            self.pc += 2

    def SKP_Vx(self) -> None:
        """
        0xE00E - Skip next instruction if key with the value of Vx is pressed.
        """
        if self.keypad.keys[self.gpio[self.Vx] & 0xF] != 0:
            self.pc += 4
        else:
            self.pc += 2

    def SKNP_Vx(self) -> None:
        """
        0xE0A1 - Skip next instruction if key with the value of Vx is not pressed.
        """
        if self.keypad.keys[self.gpio[self.Vx] & 0xF] == 0:
            self.pc += 4
        else:
            self.pc += 2

    def CALL_F(self) -> None:
        """
        0xF000 - Execute subroutine at Fx.
        """
        try:
            self.functions[self.opcode & 0xF0FF]()
        except KeyError:
            self.pc += 2

    def LD_Vx_DT(self) -> None:
        """
        0xF007 - Set Vx = delay timer value.
        """
        self.gpio[self.Vx] = self.dt
        self.pc += 2

    def LD_Vx_K(self) -> None:
        """
        0xF00A - Wait for a key press, store the value of the key in Vx.
        """
        self.halt = True

        while self.halt:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN:
                if event.key in self.keypad.keymap:
                    self.keypad.keys[self.keypad.keymap[event.key]] = 1
                    self.gpio[self.Vx] = self.keypad.keymap[event.key]

                    self.halt = False

        self.pc += 2

    def LD_DT_Vx(self) -> None:
        """
        0xF015 - Set delay timer = Vx.
        """
        self.dt = self.gpio[self.Vx]
        self.pc += 2

    def LD_ST_Vx(self) -> None:
        """
        0xF018 - Set sound timer = Vx.
        """
        self.st = self.gpio[self.Vx]
        self.pc += 2

    def ADD_I_Vx(self) -> None:
        """
        0xF01E - Set I = I + Vx.
        """
        self.I += self.gpio[self.Vx]
        self.pc += 2

    def LD_F_Vx(self) -> None:
        """
        0xF029 - Set I = location of sprite for digit Vx.
        """
        self.I = (self.gpio[self.Vx] * 5) & 0x0FFF
        self.pc += 2

    def LD_B_Vx(self) -> None:
        """
        0xF033 - Store BCD representation of Vx in memory locations I, I+1, and I+2.
        """
        self.memory[self.I] = self.gpio[self.Vx] // 100
        self.memory[self.I + 1] = (self.gpio[self.Vx] % 100) // 10
        self.memory[self.I + 2] = self.gpio[self.Vx] % 10

        self.pc += 2

    def LD_I_Vx(self) -> None:
        """
        0xF055 - Store registers V0 through Vx in memory starting at location I.
        """
        for i in range(self.Vx + 1):
            self.memory[self.I + i] = self.gpio[i]
        self.pc += 2

    def LD_Vx_I(self) -> None:
        """
        0xF065 - Read registers V0 through Vx from memory starting at location I.
        """
        for i in range(self.Vx + 1):
            self.gpio[i] = self.memory[self.I + i]
        self.pc += 2

    @property
    def functions(self) -> t.Callable[..., None]:
        """
        A dictionary of functions that can be called by the opcode.

        TODO: Add Super Chip-8 specific functions.
        """
        return {
            0x0000: self.SYS_addr,
            0x00E0: self.CLS,
            0x000E: self.RET,
            0x1000: self.JP_addr,
            0x2000: self.CALL_addr,
            0x3000: self.SE_Vx_byte,
            0x4000: self.SNE_Vx_byte,
            0x5000: self.SE_Vx_Vy,
            0x6000: self.LD_Vx_byte,
            0x7000: self.ADD_Vx_byte,
            0x8000: self.CALL_8,
            0x8001: self.LD_Vx_Vy,
            0x8002: self.AND_Vx_Vy,
            0x8003: self.XOR_Vx_Vy,
            0x8004: self.ADD_Vx_Vy,
            0x8005: self.SUB_Vx_Vy,
            0x8006: self.SHR_Vx_Vy,
            0x8007: self.SUBN_Vx_Vy,
            0x800E: self.SHL_Vx_Vy,
            0x9000: self.SNE_Vx_Vy,
            0xA000: self.LD_I_addr,
            0xB000: self.JP_V0_addr,
            0xC000: self.RND_Vx_byte,
            0xD000: self.DRW_Vx_Vy_nibble,
            0xE000: self.CALL_E,
            0xE00E: self.SKP_Vx,
            0xE001: self.SKNP_Vx,
            0xF000: self.CALL_F,
            0xF007: self.LD_Vx_DT,
            0xF00A: self.LD_Vx_K,
            0xF015: self.LD_DT_Vx,
            0xF018: self.LD_ST_Vx,
            0xF01E: self.ADD_I_Vx,
            0xF029: self.LD_F_Vx,
            0xF033: self.LD_B_Vx,
            0xF055: self.LD_I_Vx,
            0xF065: self.LD_Vx_I,
        }

    def load_fonts(self) -> None:
        """
        loads fonts onto memory starting at 0x0.
        """
        for loc, sprite in enumerate(FONTS):
            self.memory[loc] = sprite

    def load_rom(self, file: FileIO) -> None:
        """
        loads a rom into memory starting at 0x200.
        """
        for i, data in enumerate(file.read()):
            self.memory[0x200 + i] = data

    def beep(self) -> None:
        """
        Make a beep sound.
        """
        os.system("play -q -n synth .1 sin 1000")

    def cycle(self) -> None:
        """
        This method implements a single cycle of the CPU.
        """
        for _ in range(self.speed):
            self.opcode = (self.memory[self.pc] << 8) | (self.memory[self.pc + 1])
            decode = self.opcode & 0xF000

            try:
                self.functions[decode]()
            except KeyError:
                self.pc += 2

        if not self.halt:
            if self.dt > 0:
                self.dt -= 1

            if self.st > 0:
                self.st -= 1
                # sound is probably broken so don't uncomment this.
                # self.beep()

    def run(self) -> None:
        """
        Main looper for the CPU that runs until the program is halted or closed.
        """
        self.load_fonts()
        is_running = True

        while is_running:
            print("EXECUTING: ", hex(self.opcode & 0xF000))
            print("PC: ", hex(self.pc))
            print("I: ", hex(self.I))
            print("gpio: ", self.gpio)
            print("KEY", self.keypad.keys)
            print("----------------------------------------")

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key in self.keypad.keymap:
                        self.keypad.keys[self.keypad.keymap[event.key]] = 1

                if event.type == pygame.KEYUP:
                    if event.key in self.keypad.keymap:
                        self.keypad.keys[self.keypad.keymap[event.key]] = 0

                if event.type == pygame.QUIT:
                    is_running = False

            if (time.time() - self.now) > (self.FPS / 1000):
                self.cycle()

            if self.draw_flag:
                self.display.render()


if __name__ == "__main__":
    cpu = CPU()

    # Edit the path with the location of your ROM in case you want to run it on your machine.
    cpu.load_rom(open("./roms/Space Invaders [David Winter].ch8", "rb"))
    cpu.run()
