pieceValues = {
    "P": 10,
    "B": 40,
    "H": 45,
    "R": 70,
    "Q": 130,
    "K": 99999
}

def materialDif(board):
    score = 0
    for piece, bitboard in board.items():
        colour = piece[0]
        pType = piece[1]
        quantity = int(bitboard).bit_count()
        value = quantity * pieceValues[pType]
        if colour == "w":
            score += value
        else:
            score -= value
    return score