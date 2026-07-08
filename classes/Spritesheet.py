import pygame

from core.log import get_logger

log = get_logger(__name__)


class Spritesheet(object):
    def __init__(self, filename):
        try:
            raw = pygame.image.load(filename)
            self.has_alpha = raw.get_masks()[3] != 0
            self.sheet = raw.convert_alpha()
            if not self.has_alpha:
                self.sheet.set_colorkey((0, 0, 0))
        except pygame.error:
            log.error("Nao foi possivel carregar spritesheet: %s", filename)
            raise

    def image_at(self, x, y, scalingfactor, colorkey=None, ignoreTileSize=False,
                 xTileSize=16, yTileSize=16):
        if ignoreTileSize:
            rect = pygame.Rect((x, y, xTileSize, yTileSize))
        else:
            rect = pygame.Rect((x * xTileSize, y * yTileSize, xTileSize, yTileSize))
        image = pygame.Surface(rect.size, pygame.SRCALPHA)
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is not None and not self.has_alpha:
            if colorkey == -1:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        return pygame.transform.scale(
            image, (xTileSize * scalingfactor, yTileSize * scalingfactor)
        )
