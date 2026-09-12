import pygame
from engine import visuals, constants
from engine.constants import positionSize, white, empty, botColour, sounds
import bot.evaluation

def getBoardPos(x, y):
    column = x // positionSize
    row = y // positionSize
    if constants.botColour == white:
        return ((7 - row), (7 - column))
    return row, column

def handleInputs(inputs, board):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            inputs.running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                onClick(event.pos[0], event.pos[1], board)
            elif event.button == 2:
                onMiddleClick(event.pos[0], event.pos[1], board)
            elif event.button == 3: 
                onRightClick(event.pos[0], event.pos[1])
                
        elif event.type == pygame.MOUSEMOTION:
            if visuals.rightClickStart: 
                onRightDrag(event.pos[0], event.pos[1])
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3: 
                onRightRelease(event.pos[0], event.pos[1])
                
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                board.previousMove()
                inputs.botCooldownUntil = pygame.time.get_ticks() + 3000
                inputs.bestMove = None
                inputs.searching = False
                constants.abortSearch = True
            elif event.key == pygame.K_RIGHT:
                board.redoMove()
                inputs.botCooldownUntil = pygame.time.get_ticks() + 3000
                inputs.bestMove = None
                inputs.searching = False
                constants.abortSearch = True

def onClick(x, y, board):
    if visuals.promotionActive: 
        return

    row, column = getBoardPos(x, y)

    if not (0 <= row < 8 and 0 <= column < 8):
        return

    if visuals.premoveSquare:
        visuals.premoveSquare = None

    if board.turnColour == botColour:
        futureBoard = board.clone()
        for premove in constants.premoves:
            preRow, preColumn, endRow, endColumn = premove
            futureBoard.makeMove(preRow, preColumn, endRow, endColumn, True)
        piece = futureBoard.squarePiece[row * 8 + column]
        if visuals.activeSquare == None:
            if piece == empty or (piece & 24) != botColour:
                if piece != empty:
                    visuals.activeSquare = [row, column]
                visuals.possibleMoves = getEmptyPieceMoves(piece, row, column)
                visuals.redraw = True
        else:
            startRow, startColumn = visuals.activeSquare
            if (row, column) != (startRow , startColumn):
                move = (startRow, startColumn, row, column)
                if piece != empty:
                    sounds["capture"].play()
                else:
                    sounds["move"].play()
                constants.premoves.append(move)
            visuals.activeSquare = None
            visuals.possibleMoves.clear()
            visuals.redraw = True
        return

    if visuals.activeSquare == None:
        handleSelection(board, row, column)
        return

    startRow, startColumn = visuals.activeSquare
    if (row, column) in visuals.possibleMoves:
        board.makeMove(startRow, startColumn, row, column)
        board.gameState()
        time = pygame.time.get_ticks() - constants.playerTimeStart
        print(f"Move: {board.moves:>3} | Evaluation Score: {board.evaluationScore:>5} | Time: {time / 1000:>6.2f} seconds | Depth: N/A | Endgame: {str(bot.evaluation.isEndgame(board)):>5} | Total pieces: {board.totalPieces:>2}")
        constants.playerTotalTime += time
    else:
        handleSelection(board, row, column)

def handleSelection(board, row, column):
    piece = board.squarePiece[row * 8 + column]
    if piece == empty or (piece & 24) != board.turnColour or board.turnColour == constants.botColour:
        visuals.activeSquare = None
        visuals.possibleMoves.clear()
        visuals.redraw = True
        return

    visuals.activeSquare = [row, column]
    visuals.possibleMoves = board.fullyLegalMove(row, column)
    visuals.redraw = True

def clearArrows():
    visuals.strategyCircles.clear()
    visuals.lines.clear()
    visuals.redraw = True

def onMiddleClick(x, y, board):
    if visuals.promotionActive: 
        return

    row, column = getBoardPos(x, y)

    if not (0 <= row < 8 and 0 <= column < 8):
        return 

    piece = board.squarePiece[row * 8 + column]

    if piece == empty and visuals.premoveSquare == None:
        if len(visuals.lines) > 0 or len(visuals.strategyCircles) > 0: 
            clearArrows()

        if len(constants.premoves) > 0:
            constants.premoves.clear()
            visuals.redraw = True
    
    if visuals.premoveSquare == None:
        visuals.premoveSquare = [row, column]
    else:
        startRow, startColumn = visuals.premoveSquare
        move = (startRow, startColumn, row, column)
        if move in constants.premoves:
            constants.premoves.remove(move)
        visuals.premoveSquare = None
    visuals.redraw = True

def onRightClick(x, y):
    if visuals.promotionActive: 
        return
    
    visuals.rightClickStart = getBoardPos(x, y)

def onRightDrag(x, y):
    if visuals.rightClickStart:
        visuals.temporaryLine = visuals.squareCentre(getBoardPos(x, y))
    visuals.redraw = True

def onRightRelease(x, y):
    if not visuals.rightClickStart: return

    endRow, endColumn = getBoardPos(x, y)
    startRow, startColumn = visuals.rightClickStart
    
    if 0 <= endRow < 8 and 0 <= endColumn < 8:
        if (startRow, startColumn) == (endRow, endColumn):
            if (startRow, startColumn) in visuals.strategyCircles:
                visuals.strategyCircles.remove((endRow, endColumn))
            else:
                visuals.strategyCircles.append((endRow, endColumn))
        else:
            line = ((startRow, startColumn), (endRow, endColumn))
            if line in visuals.lines:
                visuals.lines.remove(line)
            else:
                visuals.lines.append(line)

    visuals.rightClickStart = visuals.temporaryLine = None
    visuals.redraw = True

def getEmptyPieceMoves(piece, row, column):
    moves = []
    pieceType = piece & 7
    pieceColour = piece & 24
    index = row * 8 + column
    mask = 0
    if pieceType == constants.knight:
        mask = constants.knightAtk[index]
    elif pieceType == constants.king:
        mask = constants.kingAtk[index]
    elif pieceType == constants.rook:
        mask = constants.rookAtk[index]
    elif pieceType == constants.bishop:
        mask = constants.bishopAtk[index]
    elif pieceType == constants.queen:
        mask = constants.queenAtk[index]

    while mask:
        lsb = mask & -mask
        square = lsb.bit_length() - 1
        moves.append((square // 8, square % 8))
        mask &= (mask - 1)

    if pieceType == constants.pawn:
        direction = -1 if pieceColour == constants.white else 1
        potRow = row + direction
        if 0 <= potRow < 8:
            moves.append((potRow, column))
            if pieceColour == constants.white and row == 6: 
                moves.append((potRow - 1, column))
            elif pieceColour == constants.black and row == 1: 
                moves.append((potRow + 1, column))
        for colChange in [-1, 1]:
            if 0 <= potRow < 8 and 0 <= column + colChange < 8:
                moves.append((potRow, column + colChange))

    return moves