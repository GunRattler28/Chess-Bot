gameOverMessage = None
moves = 0
halfmoveClock = 0
turnColour = "w"
moveHistory = []
redoHistory = []
positionHistory = []
squarePiece = [""] * 64
enPassantTarget = None

piecePositions = {
    "bQ": 0x0000000000000008,
    "bK": 0x0000000000000010, 
    "bB": 0x0000000000000024,
    "bH": 0x0000000000000042, 
    "bR": 0x0000000000000081, 
    "bP": 0x000000000000FF00,
    "wQ": 0x0800000000000000, 
    "wK": 0x1000000000000000, 
    "wB": 0x2400000000000000, 
    "wH": 0x4200000000000000, 
    "wR": 0x8100000000000000, 
    "wP": 0x00FF000000000000
}

castleRights = {
    "wKl": True, "wK": True, "wKr": True,
    "bKl": True, "bK": True, "bKr": True,
}

def getPiece(row, column):
    if not (0 <= row < 8 and 0 <= column < 8):
        return ""
    return squarePiece[row * 8 + column]

def setPiece(row, column, piece):
    if not (0 <= row < 8 and 0 <= column < 8):
        return
    squarePiece[row * 8 + column] = piece

def getPieceFromBitboards(row, column):
    if not (0 <= row < 8 and 0 <= column < 8):
        return ""
    bit = 1 << (row * 8 + column)
    for piece, bitboard in piecePositions.items():
        if bitboard & bit:
            return piece
    return ""

def updateSquareTable():
    global squarePiece
    squarePiece = [""] * 64
    for piece, bitboard in piecePositions.items():
        board = int(bitboard)
        while board:
            lsb = board & -board
            index = lsb.bit_length() - 1
            squarePiece[index] = piece
            board &= board - 1

def getOccupied():
    whiteOccupied = 0
    blackOccupied = 0
    for name, bitboard in piecePositions.items():
        if name[0] == "w":
            whiteOccupied |= bitboard
        else:
            blackOccupied |= bitboard
    occupied = whiteOccupied | blackOccupied
    return (whiteOccupied, blackOccupied, occupied)

def hashBoard():
    return hash((tuple(piecePositions.values()), turnColour, tuple(castleRights.values()), enPassantTarget))