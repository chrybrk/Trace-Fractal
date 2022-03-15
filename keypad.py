import pygame

__all__ = ("KeyPad",)


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
