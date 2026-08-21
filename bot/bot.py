import pygame
from engine import constants
from engine.constants import white, black, empty, pawn, king
from bot import evaluation

aspirationWindow = 50
exact = 0
upper = 1
lower = 2
tableSize = 1048576
transpositionTable = [None] * tableSize
historyTable = [0] * 4096   # All moves. From every square to every other square. 64 * 64
pruneMoves = []
minimumDepth = 3 # The depth the bot has to be at before it can use null move pruning. The earlier it is used (higher value) the more safer it is as the opponent has more time to capitalise. The later is is used (lower value) the higher the gain and risk
for i in range(50):
    pruneMoves.append([None, None])

def storeEvaluation(hash, depth, score, flag, bestMove):
    transpositionTable[hash & (tableSize - 1)] = (
        hash,
        depth,
        score,
        flag,
        bestMove
    )

def getEvaluation(hash, depth, alpha, beta):
    index = hash & (tableSize - 1)
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

def scoreMove(board, move, ply, previousBestMove=None):
    if move == previousBestMove:
        return 1000000
    
    startRow, startColumn, endRow, endColumn = move
    startIndex = startRow * 8 + startColumn
    endIndex = endRow * 8 + endColumn
    movingPiece = board.squarePiece[startRow * 8 + startColumn]
    movingType = movingPiece & 7
    movingColour = movingPiece & 24
    targetPiece = board.squarePiece[endRow * 8 + endColumn]
    score = 0

    if movingColour == black:
        endIndex = endIndex ^ 56
            
    if movingType == king:
        if board.endgame:
            score += evaluation.kingEndgamePositionScores[endIndex] * 10
        else:
            score += evaluation.kingPositionScores[endIndex] * 10
    else:
        score += evaluation.positionTables[movingType][endIndex]

    promotionRow = 0 if (movingPiece & 24) == white else 7

    if (movingType == pawn) and (endRow == promotionRow):
        score += 100000

    if targetPiece != empty:
        score += 10000
        targetType = targetPiece & 7
        score += evaluation.pieceValues[targetType] * 10
        score -= evaluation.pieceValues[movingType]
        return score
    elif ply < len(pruneMoves) and move == pruneMoves[ply][0]:
        score += 9000    
        return score
    elif ply < len(pruneMoves) and move == pruneMoves[ply][1]:
        score += 8000
        return score
    
    historyTableIndex = startIndex * 64 + endIndex
    score += min(historyTable[historyTableIndex], 7000) # To make sure that the other stuff are evaluated before this

    return score

def minimax(board, depth, ply, maximisingPlayer, startTime, timeLimit, alpha=-999999, beta=999999, allowNull=True):
    if constants.abortSearch:
        return 0
    if (pygame.time.get_ticks() - startTime) > timeLimit:
        constants.abortSearch = True
        return 0
    if depth <= 0:
        return quiescentSearch(board, alpha, beta, maximisingPlayer, ply, startTime, timeLimit)
    if board.halfmoveClock >= 100 or board.positionCounts.get(board.hash, 0) >= 3:
        return 0
    hash = board.hash
    score, bestMove = getEvaluation(hash, depth, alpha, beta)
    if score is not None:
        return score
    initialAlpha = alpha
    initialBeta = beta
    currentColour = white if maximisingPlayer else black
    if allowNull and depth >= minimumDepth and not board.kingCheck(currentColour) and not board.endgame:
        depthSkip = (depth // 6) + 2 # Reduced evaluation depth during null move pruning. Calculated by some random ahh formula that gives a depth skip based off of current depth.
        savedEnPassant = board.enPassantTarget
        board.setEnPassantTarget(None)
        board.switchTurn()
        score = minimax(board, depth - depthSkip, ply + 1, not maximisingPlayer, startTime, timeLimit, alpha, beta, False)
        board.switchTurn()
        board.setEnPassantTarget(savedEnPassant)
        if maximisingPlayer and score >= beta:
            return beta
        elif not maximisingPlayer and score <= alpha:
            return alpha 

    bestScore = -999999 if maximisingPlayer else 999999
    moves = getAllPossibleMoves(board, currentColour)
    moveScores = {}
    for move in moves:
        moveScores[move] = scoreMove(board, move, ply, bestMove) # Dictionary containing each move and their priority based off of scoreMove()
    moves.sort(key=moveScores.get, reverse=True) # Sort by values in moveScores
    legalMovesFound = False

    for move in moves:
        startRow, startColumn, endRow, endColumn = move
        undoInfo = board.makeMove(startRow, startColumn, endRow, endColumn, simulation=True)
        if board.kingCheck(currentColour):        
            board.unmakeMove(undoInfo)
            continue

        legalMovesFound = True

        if depth >= 3 and (moveScores[move] < 7000):
            reduced = (depth // 6) + 2
            score = minimax(board, depth - 1 - reduced, ply + 1, not maximisingPlayer, startTime, timeLimit, alpha, beta)
            if (maximisingPlayer and score > alpha) or (not maximisingPlayer and score < beta):
                score = minimax(board, depth - 1, ply + 1, not maximisingPlayer, startTime, timeLimit, alpha, beta)
        else:
            score = minimax(board, depth - 1, ply + 1, not maximisingPlayer, startTime, timeLimit, alpha, beta)

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
            targetPiece = board.squarePiece[endRow * 8 + endColumn]
            if targetPiece == empty and ply < len(pruneMoves):
                if move != pruneMoves[ply][0]:
                    pruneMoves[ply][1] = pruneMoves[ply][0]
                    pruneMoves[ply][0] = move
                startIndex = startRow * 8 + startColumn
                endIndex = endRow * 8 + endColumn
                historyTable[startIndex * 64 + endIndex] += (depth * depth) # Higher the depth closer to the start of search since minimax counts down to 0. Higher depths prune more moves than lower depths
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

def quiescentSearch(board, alpha, beta, maximisingPlayer, ply, startTime, timeLimit):
    if constants.abortSearch:
        return board.evaluationScore

    if (pygame.time.get_ticks() - startTime) > timeLimit:
        constants.abortSearch = True
        return board.evaluationScore

    score, bestMove = getEvaluation(board.hash, 0, alpha, beta)
    if score != None:
        return score

    initialAlpha = alpha
    initialBeta = beta
    bestScore = board.evaluationScore

    # If the current score isn't the best score so far no need to evaluate further as there is already a better path

    if maximisingPlayer:
        if bestScore >= beta:
            return beta
        alpha = max(alpha, bestScore)
    else:
        if bestScore <= alpha:
            return alpha
        beta = min(beta, bestScore) # If it is better than their current best guaranteed outcome update beta to score

    currentColour = white if maximisingPlayer else black
    moves = getAllPossibleMoves(board, currentColour)
    captures = []
    for move in moves:
        startRow, startColumn, endRow, endColumn = move
        movingPiece = board.squarePiece[startRow * 8 + startColumn]
        target = board.squarePiece[endRow * 8 + endColumn] # If target isn't empty then it is a capture
        if (target != empty) or ((movingPiece & 7) == pawn and (startColumn != endColumn)): # If the moving piece is a pawn and it changes column it must be an en passant
            captures.append(move)

    # Sort captures

    moveScores = {}
    for move in captures:
        moveScores[move] = scoreMove(board, move, ply) # Dictionary containing each move and their priority based off of scoreMove()
    captures.sort(key=moveScores.get, reverse=True) # Sort by values in moveScores

    for move in captures:
        if constants.abortSearch:
            return bestScore
        
        startRow, startColumn, endRow, endColumn = move
        undoInfo = board.makeMove(startRow, startColumn, endRow, endColumn, simulation=True)
        if board.kingCheck(currentColour): # If move is illegal as it puts king in check
            board.unmakeMove(undoInfo)
            continue # Continue skips to next iteration

        score = quiescentSearch(board, alpha, beta, not maximisingPlayer, ply + 1, startTime, timeLimit)
        board.unmakeMove(undoInfo)

        if maximisingPlayer:
            if score > bestScore:
                bestScore = score
                bestMove = move
            alpha = max (alpha, bestScore)
        else:
            if score < bestScore:
                bestScore = score
                bestMove = move
            beta = min(beta, bestScore)

        if beta <= alpha:
            break

    if bestScore <= initialAlpha:
        flag = upper
    elif bestScore >= initialBeta:
        flag = lower
    else:
        flag = exact

    if not constants.abortSearch:
        storeEvaluation(board.hash, 0, bestScore, flag, bestMove)

    return bestScore

def searchMovesAtDepth(board, moves, depth, ply, alpha, beta, playerMaximising, botColour, startTime, timeLimit):
    if (pygame.time.get_ticks() - startTime) > timeLimit:
        return 0, None
    
    currentBestScore = -999999 if playerMaximising else 999999
    currentBestMove = None
    
    for move in moves:
        if constants.abortSearch:
            break
        startRow, startColumn, endRow, endColumn = move
        moveScore = scoreMove(board, move, ply, currentBestMove)
        undoInfo = board.makeMove(startRow, startColumn, endRow, endColumn, simulation=True)
        
        if board.kingCheck(botColour):
            board.unmakeMove(undoInfo)
            continue
        
        if depth >= 3 and (moveScore < 7000):
            reduced = (depth // 6) + 2
            score = minimax(board, depth - 1 - reduced, ply + 1, not playerMaximising, startTime, timeLimit, alpha, beta)
            if (playerMaximising and score > alpha) or (not playerMaximising and score < beta):
                score = minimax(board, depth - 1, ply + 1, not playerMaximising, startTime, timeLimit, alpha, beta)
        else:
            score = minimax(board, depth - 1, ply + 1, not playerMaximising, startTime, timeLimit, alpha, beta)

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
            targetPiece = board.squarePiece[endRow * 8 + endColumn]
            if targetPiece == empty and ply < len(pruneMoves):
                if move != pruneMoves[ply][0]:
                    pruneMoves[ply][1] = pruneMoves[ply][0]
                    pruneMoves[ply][0] = move
                startIndex = startRow * 8 + startColumn
                endIndex = endRow * 8 + endColumn
                historyTable[startIndex * 64 + endIndex] += (depth * depth) # Higher the depth closer to the start of search since minimax counts down to 0. Higher depths prune more moves than lower depths
            break
            
    return currentBestScore, currentBestMove

def findBestMove(board, depth, botColour, startTime, timeLimit):
    if constants.abortSearch:
        return None
    
    playerMaximising = (botColour == white)
    bestMove = None
    moves = getAllPossibleMoves(board, botColour)
    moveScores = {}
    for move in moves:
        moveScores[move] = scoreMove(board, move, 0, bestMove) # Dictionary containing each move and their priority based off of scoreMove()
    moves.sort(key=moveScores.get, reverse=True) # Sort by values in moveScores
    if not moves:
        return None, 0
    bestMove = moves[0]
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

        currentBestScore, currentBestMove = searchMovesAtDepth(board, moves, currentDepth, 0, initialAlpha, initialBeta, playerMaximising, botColour, startTime, timeLimit)
        if constants.abortSearch:
            break
        if currentDepth >= 4 and (currentBestScore <= initialAlpha or currentBestScore >= initialBeta):
            currentBestScore, currentBestMove = searchMovesAtDepth(board, moves, currentDepth, 0, -999999, 999999, playerMaximising, botColour, startTime, timeLimit)
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