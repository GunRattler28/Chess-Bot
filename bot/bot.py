from bot.modules import material, positions

def getAllPossibleMoves(board, colour):
    allMoves = []
    for piece, bitboard in board.piecePositions.items():
        if piece[0] == colour:
            bb = int(bitboard)
            while bb:
                lsb = bb & -bb
                index = lsb.bit_length() - 1
                row = index // 8
                column = index % 8
                pieceMoves = board.blockCheck(row, column)
                for endRow, endColumn in pieceMoves:
                    allMoves.append((row, column, endRow, endColumn))
                bb &= bb - 1
    return allMoves

def totalScore(board):
    score = 0
    score += material.materialDif(board.piecePositions) * 5
    score += positions.evaluatePositions(board.piecePositions)

    return score

def scoreMove(board, move):
    startRow, startCol, endRow, endCol = move
    targetPiece = board.getPiece(endRow, endCol)
    score = 0
    if targetPiece != "":
        targetType = targetPiece[1]
        score += material.pieceValues[targetType] * 10
        attacker = board.getPiece(startRow, startCol)
        if attacker != "":
            atkType = attacker[1]
            score -= material.pieceValues[atkType]
    return score

def minimax(board, depth, maximisingPlayer, alpha=-999999, beta=999999):
    if depth == 0:
        return totalScore(board)

    currentColour = "w" if maximisingPlayer else "b"
    moves = sorted(getAllPossibleMoves(board, currentColour), key=lambda m: scoreMove(board, m), reverse=True)

    if not moves:
        if board.kingCheck(currentColour):
            return -999999 if maximisingPlayer else 999999
        else:
            return 0
    bestScore = -999999 if maximisingPlayer else 999999

    for move in moves:
        startRow, startCol, endRow, endCol = move
        board.makeMove(startRow, startCol, endRow, endCol, sound=False, simulation=True)
        score = minimax(board, depth - 1, not maximisingPlayer, alpha, beta)
        board.previousMove(sound=False, simulation=True)
        bestScore = max(bestScore, score) if maximisingPlayer else min(bestScore, score) 
        if maximisingPlayer:
            alpha = max(alpha, score)
        else:
            beta = min(beta, score)
        if beta <= alpha:
            break

    return bestScore

def findBestMove(board, depth, botColour):
    playerMaximising = (botColour == "w")
    alpha = -999999
    beta = 999999
    bestMove = None
    
    moves = sorted(getAllPossibleMoves(board, botColour), key=lambda m: scoreMove(board, m), reverse=True)

    if moves:
        bestMove = moves[0]

    savedRedo = board.redoHistory.copy()
    savedMoves = board.moveHistory.copy()
    savedPositions = board.positionHistory.copy()
    savedGameOver = board.gameOverMessage
    prevScore = 0
    window = 25
    
    for currentDepth in range(1, depth + 1):
        if currentDepth >= 4:
            alpha = prevScore - window
            beta = prevScore + window
        else:
            alpha = -999999
            beta = 999999

        currentBestScore = -999999 if playerMaximising else 999999
        currentBestMove = bestMove

        for move in moves:
            startRow, startCol, endRow, endCol = move
            board.makeMove(startRow, startCol, endRow, endCol, sound=False, simulation=True)
            score = minimax(board, currentDepth - 1, not playerMaximising, alpha, beta)
            board.previousMove(sound=False, simulation=True)
            
            if playerMaximising:
                if score > currentBestScore:
                    currentBestScore = score
                    currentBestMove = move
                alpha = max(alpha, score)
            else:
                if score < currentBestScore:
                    currentBestScore = score
                    currentBestMove = move
                beta = min(beta, score)
                
            if beta <= alpha:
                break

        if currentDepth >= 4 and (currentBestScore <= alpha or currentBestScore >= beta):
            alpha = -999999
            beta = 999999
            currentBestScore = -999999 if playerMaximising else 999999
            
            for move in moves:
                startRow, startCol, endRow, endCol = move
                board.makeMove(startRow, startCol, endRow, endCol, sound=False, simulation=True)
                score = minimax(board, currentDepth - 1, not playerMaximising, alpha, beta)
                board.previousMove(sound=False, simulation=True)
                
                if playerMaximising:
                    if score > currentBestScore:
                        currentBestScore = score
                        currentBestMove = move
                    alpha = max(alpha, score)
                else:
                    if score < currentBestScore:
                        currentBestScore = score
                        currentBestMove = move
                    beta = min(beta, score)
                    
                if beta <= alpha:
                    break

        prevScore = currentBestScore
        if currentBestMove:
            bestMove = currentBestMove
            if bestMove in moves:
                moves.remove(bestMove)
                moves.insert(0, bestMove)
            
    board.redoHistory = savedRedo
    board.moveHistory = savedMoves
    board.positionHistory = savedPositions
    board.gameOverMessage = savedGameOver
    
    return bestMove