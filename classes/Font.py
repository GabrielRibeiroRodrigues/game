import pygame


class Font:
    def __init__(self, filePath=None, size=None):
        self._fontCache = {}

    def _getFont(self, size):
        if size not in self._fontCache:
            self._fontCache[size] = pygame.font.SysFont("arial", size, bold=True)
        return self._fontCache[size]

    def drawText(self, text, x, y, size, color=(255, 255, 255)):
        surface = self._getFont(size).render(str(text), True, color)
        self.screen.blit(surface, (x, y))
