import updateBoard
import moveGeneration
import moveExecution

pieceValues = {
    "P": 10,
    "B": 40,
    "H": 45,
    "R": 70,
    "Q": 130,
    "K": 99999
}

def materialDif():
    score = 0
    for piece, bitboard in updateBoard.piecePositions.items():
        colour = piece[0]
        pType = piece[1]
        quantity = int(bitboard).bit_count()
        value = quantity * pieceValues[pType]
        if colour == "w":
            score += value
        else:
            score -= value
    return score

def getAllPossibleMoves(colour):
    allMoves = []
    for piece, bitboard in updateBoard.piecePositions.items():
        if piece[0] == colour:
            board = int(bitboard)
            while board:
                lsb = board & -board
                index = lsb.bit_length() - 1
                row = index // 8
                column = index % 8
                pieceMoves = moveGeneration.blockCheck(row, column)
                for endRow, endColumn in pieceMoves:
                    allMoves.append((row, column, endRow, endColumn))
                board &= board - 1
    return allMoves

def scoreMove(move):
    startRow, startCol, endRow, endCol = move
    targetPiece = updateBoard.getPiece(endRow, endCol)
    score = 0
    if targetPiece != "":
        targetType = targetPiece[1]
        score += pieceValues[targetType] * 10
        attacker = updateBoard.getPiece(startRow, startCol)
        if attacker != "":
            atkType = attacker[1]
            score -= pieceValues[atkType]
    return score

def minimax(depth, maxMaterial, alpha=-999999, beta=999999):
    if depth == 0:
        return materialDif()

    bestScore = -999999 if maxMaterial else 999999
    currentColour = "w" if maxMaterial else "b"
    
    moves = sorted(getAllPossibleMoves(currentColour), key=scoreMove, reverse=True)
    
    for move in moves:
        startRow, startCol, endRow, endCol = move
        moveExecution.makeMove(startRow, startCol, endRow, endCol, sound=False, simulation=True)
        
        score = minimax(depth - 1, not maxMaterial, alpha, beta)
        
        moveExecution.previousMove(sound=False, simulation=True)
        
        if maxMaterial:
            bestScore = max(bestScore, score)
            alpha = max(alpha, score)
        else:
            bestScore = min(bestScore, score)
            beta = min(beta, score)

        if beta <= alpha:
            break
        
    return bestScore

def findBestMove(depth, botColour):
    bestScore = -999999 if botColour == "w" else 999999
    
    alpha = -999999
    beta = 999999
    
    moves = sorted(getAllPossibleMoves(botColour), key=scoreMove, reverse=True)

    savedRedo = updateBoard.redoHistory.copy()
    savedMoves = updateBoard.moveHistory.copy()
    savedPositions = updateBoard.positionHistory.copy()
    savedGameOver = updateBoard.gameOverMessage
    
    for move in moves:
        startRow, startCol, endRow, endCol = move
        moveExecution.makeMove(startRow, startCol, endRow, endCol, sound=False, simulation=True)
        
        score = minimax(depth - 1, not (botColour == "w"), alpha, beta)
        
        moveExecution.previousMove(sound=False, simulation=True)
        
        if botColour == "w":
            if score >= bestScore:
                bestScore = score
                bestMove = move
            alpha = max(alpha, score)
        else:
            if score <= bestScore:
                bestScore = score
                bestMove = move
            beta = min(beta, score)
            
        if beta <= alpha:
            break
                
    updateBoard.redoHistory = savedRedo
    updateBoard.moveHistory = savedMoves
    updateBoard.positionHistory = savedPositions
    updateBoard.gameOverMessage = savedGameOver
    
    return bestMove