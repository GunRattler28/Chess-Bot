from engine import visuals, logic
from bot import bot
from engine.constants import positionSize

def onClick(x, y):
    if visuals.promotionActive: return
    if len(visuals.lines) > 0 or len(visuals.strategyCircles) > 0: clearArrows()

    row, column = int(y // positionSize), int(x // positionSize)

    if visuals.activeSquare is None:
        handleSelection(row, column)
        return

    startRow, startColumn = visuals.activeSquare
    if (row, column) in visuals.possibleMoves:
        logic.makeMove(startRow, startColumn, row, column)
        logic.gameState()
        print(f"Move: {logic.moves} Material Difference: {bot.materialDif()}")
    else:
        handleSelection(row, column)

def handleSelection(row, column):
    piece = logic.getPiece(row, column)
    if piece == "" or piece[0] != logic.turnColour:
        visuals.activeSquare = visuals.activeOutline = None
        visuals.possibleMoves.clear()
        visuals.redraw = True
        return

    visuals.activeSquare = [row, column]
    visuals.possibleMoves = logic.blockCheck(row, column)
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