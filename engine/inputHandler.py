import pygame
from engine import visuals, logic
from bot.modules import material
from engine.constants import positionSize

def handleInputs(inputs, board):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            inputs.running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and not inputs.searching: onClick(event.pos[0], event.pos[1], board) 
            elif event.button == 3: onRightClick(event.pos[0], event.pos[1])
                
        elif event.type == pygame.MOUSEMOTION:
            if visuals.rightClickStart: onRightDrag(event.pos[0], event.pos[1])
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3: onRightRelease(event.pos[0], event.pos[1])
                
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
    if visuals.promotionActive: return
    if len(visuals.lines) > 0 or len(visuals.strategyCircles) > 0: clearArrows()

    row, column = int(y // positionSize), int(x // positionSize)

    if visuals.activeSquare is None:
        handleSelection(board, row, column)
        return

    startRow, startColumn = visuals.activeSquare
    if (row, column) in visuals.possibleMoves:
        board.makeMove(startRow, startColumn, row, column)
        board.gameState()
        print(f"Move: {board.moves} Material Difference: {material.materialDif(board.piecePositions)}")
    else:
        handleSelection(board, row, column)

def handleSelection(board, row, column):
    piece = board.getPiece(row, column)
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
    if visuals.promotionActive: return
    visuals.rightClickStart = (int(y // positionSize), int(x // positionSize))

def onRightDrag(x, y):
    if visuals.rightClickStart:
        visuals.temporaryLine = visuals.squareCenter((int(y // positionSize), int(x // positionSize)))
    visuals.redraw = True

def onRightRelease(x, y):
    if not visuals.rightClickStart: return

    endRow, endColumn = int(y // positionSize), int(x // positionSize)
    startRow, startColumn = visuals.rightClickStart
    
    if 0 <= endRow < 8 and 0 <= endColumn < 8:
        if (startRow, startColumn) == (endRow, endColumn):
            if (startRow, startColumn) in visuals.strategyCircles:
                visuals.strategyCircles.remove((endRow, endColumn))
            else:
                visuals.strategyCircles.append((endRow, endColumn))
        else:
            visuals.lines.append(((startRow, startColumn), (endRow, endColumn)))

    visuals.rightClickStart = visuals.temporaryLine = None
    visuals.redraw = True