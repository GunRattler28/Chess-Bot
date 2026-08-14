import pygame
import engine.constants as constants
from engine.constants import white, black, empty
from bot import evaluation

aspirationWindow = 50
exact = 0
upper = 1
lower = 2
tableSize = 1500007
transpositionTable = [None] * tableSize

def storeEvaluation(hash, depth, score, flag, bestMove):
    transpositionTable[hash % tableSize] = (
        hash,
        depth,
        score,
        flag,
        bestMove
    )

def getEvaluation(hash, depth, alpha, beta):
    index = hash % tableSize
    position = transpositionTable[index]
    if position is not None and position[0] == hash:
        score = position[2]
        flag = position[3]
        bestMove = position[4]
        if position[1] >= depth:
            if flag == exact:
                return score, bestMove
            elif flag == upper and score <= alpha:
                return score, bestMove
            elif flag == lower and score >= beta:
                return score, bestMove
        return None, bestMove
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

def scoreMove(board, move, previousBestMove=None):
    if move == previousBestMove:
        return 999999
    
    startRow, startColumn, endRow, endColumn = move
    targetPiece = board.squarePiece[endRow * 8 + endColumn]
    score = 0
    
    if targetPiece != empty:
        targetType = targetPiece & 7
        score += evaluation.pieceValues[targetType] * 10
        attacker = board.squarePiece[startRow * 8 + startColumn]
        if attacker != empty:
            atkType = attacker & 7
            score -= evaluation.pieceValues[atkType]
    return score

def minimax(board, depth, maximisingPlayer, startTime, timeLimit, alpha=-999999, beta=999999):
    if constants.abortSearch:
        return 0
    if (pygame.time.get_ticks() - startTime) > timeLimit:
        constants.abortSearch = True
        return 0
    if depth == 0:
        return board.evaluationScore
    if board.halfmoveClock >= 100 or board.positionCounts.get(board.zobristHash(), 0) >= 3:
        return 0
    hash = board.zobristHash()
    score, bestMove = getEvaluation(hash, depth, alpha, beta)
    if score is not None:
        return score
    initialAlpha = alpha
    initialBeta = beta
    currentColour = white if maximisingPlayer else black
    moves = getAllPossibleMoves(board, currentColour)
    bestScore = -999999 if maximisingPlayer else 999999
    moves.sort(key=lambda move: scoreMove(board, move, bestMove), reverse=True)
    legalMovesFound = False

    for move in moves:
        startRow, startColumn, endRow, endColumn = move
        undoInfo = board.makeMove(startRow, startColumn, endRow, endColumn, simulation=True)
        if board.kingCheck(currentColour):        
            board.unmakeMove(undoInfo)
            continue

        legalMovesFound = True
        score = minimax(board, depth - 1, not maximisingPlayer, startTime, timeLimit, alpha, beta, )
        board.unmakeMove(undoInfo)
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
            return (-99999 - depth) if maximisingPlayer else (99999 + depth)
        else:
            return 0

    if bestScore <= initialAlpha:
        flag = upper
    elif bestScore >= initialBeta:
        flag = lower
    else:
        flag = exact

    if not constants.abortSearch:
        storeEvaluation(hash, depth, bestScore, flag, bestMove)
    return bestScore

def searchMovesAtDepth(board, moves, depth, alpha, beta, playerMaximising, botColour, startTime, timeLimit):
    if (pygame.time.get_ticks() - startTime) > timeLimit:
        return 0, None
    
    currentBestScore = -999999 if playerMaximising else 999999
    currentBestMove = None
    
    for move in moves:
        if constants.abortSearch:
            break
        startRow, startColumn, endRow, endColumn = move
        undoInfo = board.makeMove(startRow, startColumn, endRow, endColumn, simulation=True)
        
        if board.kingCheck(botColour):        
            board.unmakeMove(undoInfo)
            continue
            
        score = minimax(board, depth - 1, not playerMaximising, startTime, timeLimit, alpha, beta)
        board.unmakeMove(undoInfo)
        
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
            
    return currentBestScore, currentBestMove

def findBestMove(board, depth, botColour, startTime, timeLimit):
    if constants.abortSearch:
        return None
    
    playerMaximising = (botColour == white)
    bestMove = None
    moves = sorted(getAllPossibleMoves(board, botColour), key=lambda move: scoreMove(board, move, bestMove), reverse=True)
    savedRedo = board.redoHistory.copy()
    savedMoves = board.moveHistory.copy()
    savedPositions = board.positionHistory.copy()
    savedGameOver = board.gameOverMessage
    completedBestMove = None
    previousScore = 0
    
    for currentDepth in range(1, depth + 1):
        if constants.abortSearch:
            break
        if (pygame.time.get_ticks() - startTime) > timeLimit:
            break
        if currentDepth >= 4:
            initialAlpha = previousScore - aspirationWindow
            initialBeta = previousScore + aspirationWindow
        else:
            initialAlpha = -999999
            initialBeta = 999999

        currentBestScore, currentBestMove = searchMovesAtDepth(board, moves, currentDepth, initialAlpha, initialBeta, playerMaximising, botColour, startTime, timeLimit)
        if constants.abortSearch:
            break
        if currentDepth >= 4 and (currentBestScore <= initialAlpha or currentBestScore >= initialBeta):
            currentBestScore, currentBestMove = searchMovesAtDepth(board, moves, currentDepth, -999999, 999999, playerMaximising, botColour, startTime, timeLimit)
            if constants.abortSearch:
                        break
        previousScore = currentBestScore
        if currentBestMove:
            bestMove = currentBestMove
            completedBestMove = currentBestMove
            if bestMove in moves:
                moves.remove(bestMove)
                moves.insert(0, bestMove)

    board.redoHistory = savedRedo
    board.moveHistory = savedMoves
    board.positionHistory = savedPositions
    board.gameOverMessage = savedGameOver

    if completedBestMove:
        return completedBestMove, currentDepth
    else:
        return bestMove, depth