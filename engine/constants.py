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

fen = None
randomColour = random.randint(0, 1) # Randomises what colour the player starts as
botColour = black if randomColour else white
playerTimeStart = 0
playerTotalTime = 0 # The total time the player has taken in making moves
abortSearch = False
premoves = []
timeLimit = 3 # How long the bot has to search for a move each turn

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

# Dictionary of the red and green overlays that are used to show legal move, highlights and whether the king is in check

overlays = {
    "red": pygame.transform.scale(pygame.image.load("images/redOverlay.png").convert_alpha(), (positionSize, positionSize)),
    "green": pygame.transform.scale(pygame.image.load("images/greenOverlay.png").convert_alpha(), (positionSize, positionSize)),
    "orange": pygame.transform.scale(pygame.image.load("images/orangeOverlay.png").convert_alpha(), (positionSize, positionSize))
}

# Dictionary of the different sounds that can play

sounds = {
    "move": pygame.mixer.Sound("sounds/Move.mp3"),
    "capture": pygame.mixer.Sound("sounds/Capture.mp3"),
    "check": pygame.mixer.Sound("sounds/Check.mp3"),
    "checkmate": pygame.mixer.Sound("sounds/Checkmate.mp3"),
}

# Arrays of each move each piece can do stored as tuples (offset x, offset y)

knightMoves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
kingMoves = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]
rookDirections = [(1,0), (-1,0), (0,1), (0,-1)]
bishopDirections = [(1,1), (1,-1), (-1,1), (-1,-1)]
queenDirections = rookDirections + bishopDirections

# Creates an array of each square a piece type can move to from each square (when the board is empty). Used for O(1) lookup time instead of calculating each turn (for kings and knights. sliding moves are too complicated to precompute)

def createAttackTable(offsets):
    table = [0] * 64 # empty mask for each square
    for square in range(64):
        row, column = square // 8, square % 8 # row and column of specific square in for loop
        mask = 0
        for rowChange, columnChange in offsets: # knight and king have offsets from the square they are on to the square they move. loops through the offsets
            newRow, newColumn = row + rowChange, column + columnChange # calculated the row and column the piece would move to with specific offsets
            if 0 <= newRow < 8 and 0 <= newColumn < 8:
                mask |= 1 << (newRow * 8 + newColumn) # left shifts bit to the correct index the piece would move to and make bit 1. Do this for every offset. Makes a masks of 0s and 1s where 1s represent where the piece can move to. 
        table[square] = mask # adds mask that contains where the piece could move to from each square for every single sqaure. mask is just a binary number where 1 represents where piece can move
    return table # returns table of masks

# this is only used for premove options and acts as if board is empty. too difficult to precompute where each piece could move from each square for every combination of pieces on the board

def createSlidingAttackTable(directions):
    table = [0] * 64 # empty table of masks
    for square in range(64):
        row, column = square // 8, square % 8 # row and column of specific square in for loop
        mask = 0
        for rowChange, columnChange in directions: # sliding pieces show directions they move in as tuple (e.g: (0, 1) would be 0 up and 1 across)
            newRow, newColumn = row + rowChange, column + columnChange # new row and column after moving 1 square in direction
            while 0 <= newRow < 8 and 0 <= newColumn < 8: # since board is empty all that would stop the piece is the edge of the board
                mask |= 1 << (newRow * 8 + newColumn) # left shifts 1 to correct index and makes that bit a 1 to show piece can move there
                newRow += rowChange # move across by same amount again 
                newColumn += columnChange # move up / down by same amount again
        table[square] = mask # saves mask of where piece can move from this square. Repeats for next square
    return table # return table of masks

# Creates array for king and knight of where they can move from each location. Creates array for bishop, rook and queen for where they could move if board was empty. used for premove options

knightAtk = createAttackTable(knightMoves)
kingAtk = createAttackTable(kingMoves)
rookAtk = createSlidingAttackTable(rookDirections)
bishopAtk = createSlidingAttackTable(bishopDirections)
queenAtk = createSlidingAttackTable(queenDirections)

random.seed(1149) # Used to ensure that using random generates the same result for each input so that zobrist hashing can be used

zobristKeys = {} # Dictionary of each piece and unique value for each square they could be on

for colour in [white, black]: # for both colours
    for pieceType in [pawn, knight, bishop, rook, queen, king]: # for every piece type
        fullPiece = colour | pieceType
        zobristKeys[fullPiece] = [] # creates key in dictionary of piece

        for index in range(64): # For each square of the board
            zobristKeys[fullPiece].append(random.getrandbits(64)) # Unique code for each piece on each square of the board

zobristTurn = random.getrandbits(64) # Unique turn key that gets XORed to toggle on and off

zobristCastling = [] # array of each combination of castling rights

for i in range(16): # 4 bits gets to max value of 15
    key = random.getrandbits(64) # unique value for each combination of castling rights
    zobristCastling.append(key)

zobristEnPassant = []

for column in range(8): # Only 8 places en passant can happen (only 8 columns)
    zobristEnPassant.append(random.getrandbits(64)) # unique value for each en passant column