import pygame
import random

windowSize = 800
positionSize = windowSize / 8
botColour = "b"
randomColour = random.randint(0, 1)
botColour = "b" if randomColour else "w"

pieces = {
    "bQ": pygame.transform.scale(pygame.image.load("images/pieces/bqueen.png").convert_alpha(), (positionSize, positionSize)),
    "bK": pygame.transform.scale(pygame.image.load("images/pieces/bking.png").convert_alpha(), (positionSize, positionSize)),
    "bB": pygame.transform.scale(pygame.image.load("images/pieces/bbishop.png").convert_alpha(), (positionSize, positionSize)),
    "bH": pygame.transform.scale(pygame.image.load("images/pieces/bhorse.png").convert_alpha(), (positionSize, positionSize)),
    "bR": pygame.transform.scale(pygame.image.load("images/pieces/brook.png").convert_alpha(), (positionSize, positionSize)),
    "bP": pygame.transform.scale(pygame.image.load("images/pieces/bpawn.png").convert_alpha(), (positionSize, positionSize)),
    "wQ": pygame.transform.scale(pygame.image.load("images/pieces/wqueen.png").convert_alpha(), (positionSize, positionSize)), 
    "wK": pygame.transform.scale(pygame.image.load("images/pieces/wking.png").convert_alpha(), (positionSize, positionSize)),
    "wB": pygame.transform.scale(pygame.image.load("images/pieces/wbishop.png").convert_alpha(), (positionSize, positionSize)),
    "wH": pygame.transform.scale(pygame.image.load("images/pieces/whorse.png").convert_alpha(), (positionSize, positionSize)),
    "wR": pygame.transform.scale(pygame.image.load("images/pieces/wrook.png").convert_alpha(), (positionSize, positionSize)),
    "wP": pygame.transform.scale(pygame.image.load("images/pieces/wpawn.png").convert_alpha(), (positionSize, positionSize))
}

overlays = {
    "red": pygame.transform.scale(pygame.image.load("images/redOverlay.png").convert_alpha(), (positionSize, positionSize)),
    "green": pygame.transform.scale(pygame.image.load("images/greenOverlay.png").convert_alpha(), (positionSize, positionSize))
}

sounds = {
    "move": pygame.mixer.Sound("sounds/Move.mp3"),
    "capture": pygame.mixer.Sound("sounds/Capture.mp3"),
    "check": pygame.mixer.Sound("sounds/Check.mp3"),
    "checkmate": pygame.mixer.Sound("sounds/Checkmate.mp3"),
}

knightMoves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
kingMoves = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]
rookDirections = [(1,0), (-1,0), (0,1), (0,-1)]
bishopDirections = [(1,1), (1,-1), (-1,1), (-1,-1)]
queenDirections = rookDirections + bishopDirections

def createAttackTable(offsets):
    table = [0] * 64
    for square in range(64):
        row, column = square // 8, square % 8
        mask = 0
        for rowChange, columnChange in offsets:
            newRow, newColumn = row + rowChange, column + columnChange
            if 0 <= newRow < 8 and 0 <= newColumn < 8:
                mask |= 1 << (newRow * 8 + newColumn)
        table[square] = mask
    return table

knightAtk = createAttackTable(knightMoves)
kingAtk = createAttackTable(kingMoves)