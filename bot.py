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
        type = piece[1]
        quantity = int(bitboard).bit_count()
        value = quantity * pieceValues[type]
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

def minimax(depth, forColour):
    if depth == 0:
        return materialDif()

    if forColour:
        bestScore = -999999
        moves = getAllPossibleMoves("w")
        
        for move in moves:
            startRow, startCol, endRow, endCol = move
            
            moveExecution.makeMove(startRow, startCol, endRow, endCol, sound=False, simulation=True)
            score = minimax(depth - 1, False)
            moveExecution.previousMove(sound=False, simulation=True)
            bestScore = max(bestScore, score)
            
        return bestScore
        
    else:
        bestScore = 999999
        moves = getAllPossibleMoves("b")
        
        for move in moves:
            startRow, startCol, endRow, endCol = move
            
            moveExecution.makeMove(startRow, startCol, endRow, endCol, sound=False, simulation=True)
            score = minimax(depth - 1, True)
            moveExecution.previousMove(sound=False, simulation=True)
            bestScore = min(bestScore, score)
            
        return bestScore

def findBestMove(depth, botColour):
    bestMove = None
    isMaximizing = (botColour == "w")
    bestScore = -999999 if isMaximizing else 999999
    
    moves = getAllPossibleMoves(botColour)
    
    savedRedo = updateBoard.redoHistory.copy()
    savedMoves = updateBoard.moveHistory.copy()
    savedPositions = updateBoard.positionHistory.copy()
    savedGameOver = updateBoard.gameOverMessage
    
    for move in moves:
        startRow, startCol, endRow, endCol = move
        moveExecution.makeMove(startRow, startCol, endRow, endCol, sound=False, simulation=True)
        score = minimax(depth - 1, not isMaximizing)
        moveExecution.previousMove(sound=False, simulation=True)
        
        if isMaximizing:
            if score >= bestScore:
                bestScore = score
                bestMove = move
        else:
            if score <= bestScore:
                bestScore = score
                bestMove = move
                
    updateBoard.redoHistory = savedRedo
    updateBoard.moveHistory = savedMoves
    updateBoard.positionHistory = savedPositions
    updateBoard.gameOverMessage = savedGameOver
    
    return bestMove