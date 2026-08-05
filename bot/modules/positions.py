knightPositionScores = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50
]

pawnPositionScores = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, 20, 20, 10, 10, 5,
    5, 5, 10, 10, 10, 10, 5, 5,
    0, 0, 10, 20, 20, 10, 0, 0,
    5, 5, 10, 25, 25, 10, 5, 5,
    10, 10, 20, 30, 30, 20, 10, 10,
    20, 20, 30, 40, 40, 30, 20, 20,
    50, 50, 50, 50, 50, 50, 50, 50
]

bishopPositionScores = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -10, -10, -10, -10, -20
]

rookPositionScores = [
    0, 0, 5, 5, 5, 5, 0, 0,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0
]

queenPositionScores = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 5, 0, 0, 0, 0, -10,
    -10, 5, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    0, 0, 5, 5, 5, 5, 0, -5,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20
]

kingPositionScores = [
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10
]

kingEndgamePositionScores = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50
]

def isEndgame(board):
    totalPieces = 0
    for bitboard in board.values():
        totalPieces += bitboard.bit_count()
        
    wQ = board["wQ"]
    bQ = board["bQ"]

    if (wQ == 0 and bQ == 0) or totalPieces < 10:
        return True
        
    return False

def evaluatePositions(board):
    score = 0
    for piece, bitboard in board.items():
        bb = int(bitboard)
        colour = piece[0]
        pType = piece[1]
        while bb:
            lsb = bb & -bb
            index = lsb.bit_length() - 1
            if colour == "w":
                index = index ^ 56
            else:
                index = index
            value = 0
            if pType == "H":
                value = knightPositionScores[index]
            elif pType == "P":
                value = pawnPositionScores[index]
            elif pType == "B":
                value = bishopPositionScores[index]
            elif pType == "R":
                value = rookPositionScores[index]
            elif pType == "Q":
                value = queenPositionScores[index]
            elif pType == "K":
                if isEndgame(board):
                    value = kingEndgamePositionScores[index]
                else:
                    value = kingPositionScores[index]
            if colour == "w":
                score += value
            else:
                score -= value
            bb &= bb - 1
    return score
