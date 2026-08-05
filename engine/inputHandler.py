import pygame
from engine import visuals, constants
from bot.modules import material
from engine.constants import positionSize

def getBoardPos(x, y):
    row, col = int(y // positionSize), int(x // positionSize)
    if constants.botColour == "w":
        return 7 - row, 7 - col
    return row, col

def handleInputs(inputs, board):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            inputs.running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: 
                if not inputs.searching: 
                    onClick(event.pos[0], event.pos[1], board)
                else:
                    clearArrows()
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
            elif event.key == pygame.K_RIGHT:
                board.redoMove()
                inputs.botCooldownUntil = pygame.time.get_ticks() + 3000
                inputs.bestMove = None
                inputs.searching = False

def onClick(x, y, board):
    if visuals.promotionActive: 
        return
    if len(visuals.lines) > 0 or len(visuals.strategyCircles) > 0: 
        clearArrows()

    row, column = getBoardPos(x, y)

    if visuals.activeSquare is None:
        handleSelection(board, row, column)
        return

    startRow, startColumn = visuals.activeSquare
    if (row, column) in visuals.possibleMoves:
        board.makeMove(startRow, startColumn, row, column)
        board.gameState()
        print(f"Move: {board.moves} Material Difference: {material.materialDif(board.piecePositions)} Time: NULL")
    else:
        handleSelection(board, row, column)

def handleSelection(board, row, column):
    piece = board.squarePiece[row * 8 + column]
    if piece == "" or piece[0] != board.turnColour:
        visuals.activeSquare = visuals.activeOutline = None
        visuals.possibleMoves.clear()
        visuals.redraw = True
        return

    visuals.activeSquare = [row, column]
    visuals.possibleMoves = board.blockCheck(row, column)
    visuals.redraw = True

def clearArrows():
    visuals.strategyCircles.clear()
    visuals.lines.clear()
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