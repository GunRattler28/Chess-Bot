import pygame
import pygame.freetype
import math
from engine.constants import windowSize, positionSize, pieces, overlays, botColour

pygame.init()
pygame.mixer.init()
pygame.font.init()

redraw = True
screen = pygame.display.set_mode((windowSize, windowSize))
pygame.display.set_caption("Gun's Chess Bot")
icon = pygame.image.load('images/icon.png')
pygame.display.set_icon(icon)

clock = pygame.time.Clock()
try:
    gameFont = pygame.freetype.SysFont("dynapuffregular", 64, bold=True) 
except:
    gameFont = pygame.freetype.SysFont("arial", 64, bold=True)

promotionActive = False
activeOutline = None
activeSquare = None
moveIndicator = []
possibleMoves = []
lines = []
rightClickStart = None
temporaryLine = None
strategyCircles = []
lastMove = None

def getDrawPos(row, col):
    if botColour == "w":
        return 7 - row, 7 - col
    return row, col

def drawBoard(board):
    global lastMove
    for column in range(0, 8):
        for row in range(0, 8):
            drawRow, drawCol = getDrawPos(row, column)
            color = "#ffffff" if ((row + column) % 2 == 0) else "#0088ff"
            if lastMove:
                startColumn, startRow, endColumn, endRow = lastMove
                if column == startColumn and row == startRow:
                    color = "#97C997"
                elif column == endColumn and row == endRow:
                    color = "#8DCE8D"
            pygame.draw.rect(screen, color, (drawCol * positionSize, drawRow * positionSize, positionSize, positionSize))
            piece = board.getPiece(row, column)
            if piece != "":
                screen.blit(pieces[piece], (drawCol * positionSize, drawRow * positionSize))

def blurSurface(surface, scaleFactor=3):
    if scaleFactor <= 1: return surface.copy()
    width = max(1, int(surface.get_width() / scaleFactor))
    height = max(1, int(surface.get_height() / scaleFactor))
    scaled = pygame.transform.smoothscale(surface, (width, height))
    return pygame.transform.smoothscale(scaled, surface.get_size())

def choosePromotion(colour):
    global promotionActive
    promotionActive = True
    piecesToChoose = ["Q", "H", "R", "B"]
    
    menuWidth = positionSize * 4
    menuX = (windowSize - menuWidth) // 2
    menuY = (windowSize - positionSize) // 2

    background = screen.copy()
    blurredBackground = blurSurface(background, 3)
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 90))
    
    chosenPiece = None
    
    while promotionActive:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouseX, mouseY = event.pos
                if menuY < mouseY < menuY + positionSize and menuX < mouseX < menuX + menuWidth:
                    index = int((mouseX - menuX) // positionSize)
                    chosenPiece = colour + piecesToChoose[index]
                    promotionActive = False

        screen.blit(blurredBackground, (0, 0))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (255, 255, 255), (menuX, menuY, menuWidth, positionSize))
        pygame.draw.rect(screen, (0, 0, 0), (menuX, menuY, menuWidth, positionSize), 4)
        
        for i, piece in enumerate(piecesToChoose):
            screen.blit(pieces[colour + piece], (menuX + (i * positionSize), menuY))
            
        pygame.display.flip()
        clock.tick(60)
        
    return chosenPiece

def drawHighlights(board):
    if activeSquare:
        row, column = activeSquare
        drawR, drawC = getDrawPos(row, column)
        pygame.draw.rect(screen, (0, 255, 0), (drawC * positionSize, drawR * positionSize, positionSize, positionSize), 4)

    for moveRow, moveColumn in possibleMoves:
        drawR, drawC = getDrawPos(moveRow, moveColumn)
        x, y = drawC * positionSize, drawR * positionSize
        if board.getPiece(moveRow, moveColumn) != "":
            screen.blit(overlays["red"], (x, y))
        else:
            screen.blit(overlays["green"], (x, y))

    if board.kingCheck(board.turnColour):
        king = board.findKing(board.turnColour)
        if king:
            drawR, drawC = getDrawPos(king[0], king[1])
            screen.blit(overlays["red"], (drawC * positionSize, drawR * positionSize))

def squareCenter(square):
    row, column = square
    drawRow, drawColumn = getDrawPos(row, column)
    offset = positionSize / 2
    return (drawColumn * positionSize + offset, drawRow * positionSize + offset)

def drawArrow(surface, color, start, end, thickness=25, arrowSize=50):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    if length == 0: return

    direction = (dx / length, dy / length)
    perpendicular = (-direction[1], direction[0])
    shaftEnd = (end[0] - direction[0] * (arrowSize * 0.6), end[1] - direction[1] * (arrowSize * 0.6))
    radius = thickness / 2

    pSA = (start[0] + perpendicular[0] * radius, start[1] + perpendicular[1] * radius)
    pSB = (start[0] - perpendicular[0] * radius, start[1] - perpendicular[1] * radius)
    pEA = (shaftEnd[0] + perpendicular[0] * radius, shaftEnd[1] + perpendicular[1] * radius)
    pEB = (shaftEnd[0] - perpendicular[0] * radius, shaftEnd[1] - perpendicular[1] * radius)

    pygame.draw.circle(surface, color, start, radius)
    pygame.draw.polygon(surface, color, [pSA, pEA, pEB, pSB])

    rotation = math.atan2(dy, dx)
    p1 = (end[0] - arrowSize * math.cos(rotation + math.pi / 4), end[1] - arrowSize * math.sin(rotation + math.pi / 4))
    p2 = (end[0] - arrowSize * math.cos(rotation - math.pi / 4), end[1] - arrowSize * math.sin(rotation - math.pi / 4))
    pygame.draw.polygon(surface, color, [end, p1, p2])

def drawArrows():
    for row, column in strategyCircles:
        drawR, drawC = getDrawPos(row, column)
        screen.blit(overlays["green"], (drawC * positionSize, drawR * positionSize))

    arrowSurf = pygame.Surface((windowSize, windowSize), pygame.SRCALPHA)
    arrowColor = (0, 255, 0, 150)

    for startSquare, endSquare in lines:
        drawArrow(arrowSurf, arrowColor, squareCenter(startSquare), squareCenter(endSquare))

    if rightClickStart and temporaryLine:
        drawArrow(arrowSurf, (0, 187, 0, 150), squareCenter(rightClickStart), temporaryLine)

    screen.blit(arrowSurf, (0, 0))