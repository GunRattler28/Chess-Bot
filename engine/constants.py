import pygame
import random

# How each piece and colour is represented in binary

empty = 0b00000
pawn = 0b00001
knight = 0b00010
bishop = 0b00011
rook = 0b00100
queen = 0b00101
king = 0b00110
white = 0b01000
black = 0b10000

windowSize = 800
positionSize = windowSize // 8 # Size of the piece textures

randomColour = random.randint(0, 1) # Randomises what colour the player starts as
botColour = black if randomColour else white
playerTimeStart = 0
playerTotalTime = 0 # The total time the player has taken in making moves
abortSearch = False
timeLimit = 1.5 # How long the bot has to search for a move each turn

# Dictionary of each colour + piece binary code as the keys and the textures as the values

piecesTextures = {
    (black | queen): pygame.transform.scale(pygame.image.load("images/pieces/bqueen.png").convert_alpha(), (positionSize, positionSize)),
    (black | king): pygame.transform.scale(pygame.image.load("images/pieces/bking.png").convert_alpha(), (positionSize, positionSize)),
    (black | bishop): pygame.transform.scale(pygame.image.load("images/pieces/bbishop.png").convert_alpha(), (positionSize, positionSize)),
    (black | knight): pygame.transform.scale(pygame.image.load("images/pieces/bhorse.png").convert_alpha(), (positionSize, positionSize)),
    (black | rook): pygame.transform.scale(pygame.image.load("images/pieces/brook.png").convert_alpha(), (positionSize, positionSize)),
    (black | pawn): pygame.transform.scale(pygame.image.load("images/pieces/bpawn.png").convert_alpha(), (positionSize, positionSize)),
    (white | queen): pygame.transform.scale(pygame.image.load("images/pieces/wqueen.png").convert_alpha(), (positionSize, positionSize)), 
    (white | king): pygame.transform.scale(pygame.image.load("images/pieces/wking.png").convert_alpha(), (positionSize, positionSize)),
    (white | bishop): pygame.transform.scale(pygame.image.load("images/pieces/wbishop.png").convert_alpha(), (positionSize, positionSize)),
    (white | knight): pygame.transform.scale(pygame.image.load("images/pieces/whorse.png").convert_alpha(), (positionSize, positionSize)),
    (white | rook): pygame.transform.scale(pygame.image.load("images/pieces/wrook.png").convert_alpha(), (positionSize, positionSize)),
    (white | pawn): pygame.transform.scale(pygame.image.load("images/pieces/wpawn.png").convert_alpha(), (positionSize, positionSize))
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

random.seed(1149)

zobristKeys = {}

for colour in [white, black]:
    for pieceType in [pawn, knight, bishop, rook, queen, king]:
        fullPiece = colour | pieceType
        zobristKeys[fullPiece] = []

        for index in range(64):
            zobristKeys[fullPiece].append(random.getrandbits(64))

zobristTurn = random.getrandbits(64)

zobristCastling = []

for i in range(16):
    key = random.getrandbits(64)
    zobristCastling.append(key)

zobristEnPassant = []

for column in range(8):
    zobristEnPassant.append(random.getrandbits(64))