import pygame

__all__ = ("FONTS", "Display", "KeyPad")


_0 = (0, 0, 0)
_1 = (0, 255, 255)

# fmt: off
FONTS = [ 
        0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
        0x20, 0x60, 0x20, 0x20, 0x70, # 1
        0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
        0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
        0x90, 0x90, 0xF0, 0x10, 0x10, # 4
        0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
        0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
        0xF0, 0x10, 0x20, 0x40, 0x40, # 7
        0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
        0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
        0xF0, 0x90, 0xF0, 0x90, 0x90, # A
        0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
        0xF0, 0x80, 0x80, 0x80, 0xF0, # C
        0xE0, 0x90, 0x90, 0x90, 0xE0, # D
        0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
        0xF0, 0x80, 0xF0, 0x80, 0x80  # F
        ]
# fmt: on


class Display:
    def __init__(self, rows: int, columns: int) -> None:
        self.rows = rows
        self.columns = columns

        self.extendby = 10
        self.screen = pygame.display.set_mode(
            (columns * self.extendby, rows * self.extendby), pygame.RESIZABLE
        )
        self.screen.fill(_0)
        pygame.display.flip()

        self.display_buffer = bytearray(rows * columns)

    def draw(self, xpos: int, ypos: int) -> bool:
        if 0 > xpos:
            xpos += self.columns
        xpos -= self.columns if xpos > self.columns else 0

        if 0 > ypos:
            ypos += self.rows
        ypos -= self.rows if ypos > self.rows else 0

        loc = xpos + (ypos * self.columns)
        try:
            self.display_buffer[loc] ^= 1
            return not self.display_buffer[loc]
        except IndexError:
            return 0

    def clear(self) -> None:
        self.display_buffer = [0] * self.rows * self.columns

    def render(self) -> None:
        self.screen.fill(_0)

        for i in range(self.columns * self.rows):

            x = (i % self.columns) * self.extendby
            y = (i // self.columns) * self.extendby

            if self.display_buffer[i]:
                pygame.draw.rect(
                    self.screen, _1, pygame.Rect(x, y, self.extendby, self.extendby)
                )
        pygame.display.update()


class KeyPad:
    def __init__(self) -> None:
        self.keys = [0] * 16
        self.keymap = {
            pygame.K_1: 1,
            pygame.K_2: 2,
            pygame.K_3: 3,
            pygame.K_4: 12,
            pygame.K_q: 4,
            pygame.K_w: 5,
            pygame.K_e: 6,
            pygame.K_r: 13,
            pygame.K_a: 7,
            pygame.K_s: 8,
            pygame.K_d: 9,
            pygame.K_f: 14,
            pygame.K_z: 10,
            pygame.K_x: 0,
            pygame.K_b: 11,
            pygame.K_v: 15,
        }
