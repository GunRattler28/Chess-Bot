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
        pieceType = piece[1]
        quantity = bitboard.bit_count()
        value = quantity * pieceValues[pieceType]
        if colour == "w":
            score += value
        else:
            score -= value
    return score