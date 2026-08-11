from bot.modules import material, positions
import engine.constants as constants
from engine.constants import white, black, empty

aspirationWindow = 50
exact = 0
upper = 1
lower = 2
tableSize = 1500007
transpositionTable = [None] * tableSize

def storeEvaluation(hash, depth, score, flag, bestMove):
    transpositionTable[hash % tableSize] = {
        "hash": hash,
        "depth": depth,
        "score": score,
        "flag": flag,
        "bestMove": bestMove
    }

def getEvaluation(hash, depth, alpha, beta):
    index = hash % tableSize
    position = transpositionTable[index]
    if position is not None and position["hash"] == hash:
        if position["depth"] >= depth:
            score = position["score"]
            flag = position["flag"]
            if flag == exact:
                return score, position["bestMove"]
            elif flag == upper and score <= alpha:
                return score, position["bestMove"]
            elif flag == lower and score >= beta:
                return score, position["bestMove"]
        return None, position["bestMove"]
    return None, None

def getAllPossibleMoves(board, colour):
    allMoves = []
    for piece, bitboard in board.piecePositions.items():
        if piece & colour:
            while bitboard:
                lsb = bitboard & -bitboard
                index = lsb.bit_length() - 1
                row = index // 8
                column = index % 8
                pieceMoves = board.calculateLegalMoves(row, column, True)
                for endRow, endColumn in pieceMoves:
                    allMoves.append((row, column, endRow, endColumn))
                bitboard &= bitboard - 1
    return allMoves

def totalScore(board):
    score = 0
    score += material.materialDif(board.piecePositions) * 5
    score += positions.evaluatePositions(board.piecePositions)

    return score

def scoreMove(board, move, previousBestMove=None):
    if move == previousBestMove:
        return 999999
    
    startRow, startCol, endRow, endCol = move
    targetPiece = board.squarePiece[endRow * 8 + endCol]
    score = 0
    
    if targetPiece != empty:
        targetType = targetPiece & 7
        score += material.pieceValues[targetType] * 10
        attacker = board.squarePiece[startRow * 8 + startCol]
        if attacker != empty:
            atkType = attacker & 7
            score -= material.pieceValues[atkType]
    return score

def minimax(board, depth, maximisingPlayer, alpha=-999999, beta=999999):
    if constants.abortSearch:
        return 0
    if depth == 0:
        return totalScore(board)
    if board.halfmoveClock >= 100 or board.positionHistory.count(board.zobristHash()) >= 3:
        return 0
    hash = board.zobristHash()
    score, bestMove = getEvaluation(hash, depth, alpha, beta)
    if score != None:
        return score
    initialAlpha = alpha
    initialBeta = beta
    currentColour = white if maximisingPlayer else black
    moves = getAllPossibleMoves(board, currentColour)
    bestScore = -999999 if maximisingPlayer else 999999
    moves.sort(key=lambda move: scoreMove(board, move, bestMove), reverse=True)

    legalMovesFound = False

    for move in moves:
        startRow, startCol, endRow, endCol = move
        board.makeMove(startRow, startCol, endRow, endCol, sound=False, simulation=True)
        if board.kingCheck(currentColour):
            board.previousMove(False, True)
            continue
        legalMovesFound = True
        score = minimax(board, depth - 1, not maximisingPlayer, alpha, beta)
        board.previousMove(sound=False, simulation=True)
        if maximisingPlayer:
            if score > bestScore:
                bestScore = score
                bestMove = move
            alpha = max(alpha, bestScore)
        else:
            if score < bestScore:
                bestScore = score
                bestMove = move
            beta = min(beta, bestScore)
        if beta <= alpha:
            break

    if not legalMovesFound:
        if board.kingCheck(currentColour):
            return (-999999 + depth) if maximisingPlayer else (999999 - depth)
        else:
            return 0

    if bestScore <= initialAlpha:
        flag = upper
    elif bestScore >= initialBeta:
        flag = lower
    else:
        flag = exact

    storeEvaluation(hash, depth, bestScore, flag, bestMove)

    return bestScore

def findBestMove(board, depth, botColour):
    if constants.abortSearch:
        return None
    playerMaximising = (botColour == white)
    alpha = -999999
    beta = 999999
    bestMove = None
    
    moves = sorted(getAllPossibleMoves(board, botColour), key=lambda move: scoreMove(board, move, bestMove), reverse=True)

    savedRedo = board.redoHistory.copy()
    savedMoves = board.moveHistory.copy()
    savedPositions = board.positionHistory.copy()
    savedGameOver = board.gameOverMessage
    prevScore = 0
    
    for currentDepth in range(1, depth + 1):
        if currentDepth >= 4:
            initialAlpha = prevScore - aspirationWindow
            initialBeta = prevScore + aspirationWindow
        else:
            initialAlpha = -999999
            initialBeta = 999999

        alpha = initialAlpha
        beta = initialBeta

        currentBestScore = -999999 if playerMaximising else 999999
        currentBestMove = bestMove

        for move in moves:
            startRow, startCol, endRow, endCol = move
            board.makeMove(startRow, startCol, endRow, endCol, sound=False, simulation=True)
            if board.kingCheck(botColour):
                board.previousMove(False, True)
                continue
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

        if currentDepth >= 4 and (currentBestScore <= initialAlpha or currentBestScore >= initialBeta):
            alpha = -999999
            beta = 999999
            currentBestScore = -999999 if playerMaximising else 999999
            
            for move in moves:
                startRow, startCol, endRow, endCol = move
                board.makeMove(startRow, startCol, endRow, endCol, sound=False, simulation=True)
                if board.kingCheck(botColour):
                    board.previousMove(False, True)
                    continue
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