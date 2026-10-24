from engine.constants import white, black, pawn, knight, bishop, rook, queen, king, empty

# how much each piece is valued respective to one another

pieceValues = {
    pawn: 10,
    bishop: 40,
    knight: 45,
    rook: 70,
    queen: 130,
    king: 99999 # very big number so that no amount of score gained could ever be worth letting a king get captured
}

# 64 element arrays for each piece that add a bonus if good positioning or punishment if bad positioning

knightPositionScores = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,  -5,   5,   5,  -5, -20, -40,
    -30,   5,  10,  15,  15,  10,   5, -30,
    -30,   0,  15,  20,  20,  15,   0, -30,
    -30,   5,  15,  20,  20,  15,   5, -30,
    -30,   0,  10,  15,  15,  10,   0, -30,
    -40, -20,   0,   0,   0,   0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50
]

pawnPositionScores = [
    50, 50, 50, 50, 50, 50, 50, 50,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0, 10, 20, 20, 10,  0,  0,
     5,  5, 5,  10,  10, 5,  5,  5,
     5, 20, 10, 10, 10, 10, 20,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

bishopPositionScores = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,  10,  10,   5,   0, -10,
    -10,   5,   5,  10,  10,   5,   5, -10,
    -10,   0,  10,  10,  10,  10,   0, -10,
    -10,  10,  10,  10,  10,  10,  10, -10,
    -10,   5,   0,   0,   0,   0,   5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20
]

rookPositionScores = [
      0,   0,   0,   0,   0,   0,   0,   0,
      5,  10,  10,  10,  10,  10,  10,   5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
      0,   0,   0,   5,   5,   0,   0,   0
]

queenPositionScores = [
    -20, -10, -10,  -5,  -5, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,   5,   5,   5,   0, -10,
     -5,   0,   5,   5,   5,   5,   0,  -5,
      0,   0,   5,   5,   5,   5,   0,  -5,
    -10,   5,   5,   5,   5,   5,   0, -10,
    -10,   0,   5,   0,   0,   0,   0, -10,
    -20, -10, -10,  -5,  -5, -10, -10, -20
]

kingPositionScores = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
     20,  20,   0,   0,   0,   0,  20,  20,
     20,  40,  20,   0,   0,  20,  40,  20
]

kingEndgamePositionScores = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10,   0,   0, -10, -20, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -30,   0,   0,   0,   0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50
]

# Dictionary so that getPieceScore can use same code for different pieces

positionTables = {
    pawn: pawnPositionScores,
    bishop: bishopPositionScores,
    knight: knightPositionScores,
    rook: rookPositionScores,
    queen: queenPositionScores,
}

def isEndgame(board):
    wQ = board.piecePositions[white | queen].bit_count() # Number of white queens
    bQ = board.piecePositions[black | queen].bit_count() # Number of black queens
    wP = board.piecePositions[white | pawn].bit_count() # Number of white pawns
    bP = board.piecePositions[black | pawn].bit_count() # Number of black pawns
    # if ((neither side has more than 2 queen) and less than 16 pieces in total) or less than 5 non pawn pieces
    if ((wQ <= 2 and bQ <= 2) and board.totalPieces < 16) or (board.totalPieces - (wP + bP)) < 5:
        return True
    return False

def getPieceScore(piece, index, endgame=False):
    if piece == empty: # Safety check but will never be true
        return 0
    
    colour = piece & 24 # First 2 digits of binary number
    pieceType = piece & 7 # last 3 digits of binary number
    score = 0
    score += (pieceValues[pieceType] * 5) # Weighted how much each piece is worth based off of value alone (not position)

    if colour == black:
        index = index ^ 56 # Flips the bits. Index is a 6 bit binary number (0 to 63). 56 is a 6 bit binary number of half 1s and half 0s. Flips the first 3 bits which flips the row 7 -> 1, 6 -> 2 but leaves the columns correct. Allows position bonus tables to work for both colours
        
    if pieceType == king:
        if endgame: # Seperate position based tables based off endgame or not. Rewards king positioning in endgame (where the king is a bital piece)
            score += kingEndgamePositionScores[index]
        else: # Rewards safe king positioning in early and midgame (where the king can easily get checkmated)
            score += kingPositionScores[index]
    else:
        score += positionTables[pieceType][index] # For other pieces goes to piece specific position bonus table -> specific square to get value

    if colour == white:
        return score # White wants highest score possible
    else:
        return -score # Negative score since black want's lowest score possible