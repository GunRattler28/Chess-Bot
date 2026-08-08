from engine.constants import pawn, bishop, knight, rook, queen, king, white, empty

pieceValues = {
    pawn: 10,
    bishop: 40,
    knight: 45,
    rook: 70,
    queen: 130,
    king: 99999
}

def materialDif(board):
    score = 0
    for piece, bitboard in board.items():
        if piece == empty:
            continue
        isWhite = piece & white
        pieceType = piece & 7
        quantity = bitboard.bit_count()
        value = quantity * pieceValues[pieceType]
        if isWhite:
            score += value
        else:
            score -= value
    return score