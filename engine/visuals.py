import pygame
import pygame.freetype
import math
from engine.constants import windowSize, positionSize, pieces, overlays

pygame.init()
pygame.mixer.init()
pygame.font.init()

redraw = True
screen = pygame.display.set_mode((windowSize, windowSize))
pygame.display.set_caption("Gun's Chess Bot")

try:
    icon = pygame.image.load('images/icon.png')
    pygame.display.set_icon(icon)
except:
    pass

clock = pygame.time.Clock()
# gameFont = pygame.freetype.SysFont("dynapuffregular", 64, bold=True) 

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

def drawBoard(board):
    global lastMove
    for column in range(0, 8):
        for row in range(0, 8):
            color = "#ffffff" if ((row + column) % 2 == 0) else "#0088ff"
            if lastMove:
                startColumn, startRow, endColumn, endRow = lastMove
                if column == startColumn and row == startRow:
                    color = "#97C997"
                elif column == endColumn and row == endRow:
                    color = "#8DCE8D"
            pygame.draw.rect(screen, color, (column * positionSize, row * positionSize, positionSize, positionSize))
            piece = board.getPiece(row, column)
            if piece != "":
                screen.blit(pieces[piece], (column * positionSize, row * positionSize))

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
        r, c = activeSquare
        pygame.draw.rect(screen, (0, 255, 0), (c * positionSize, r * positionSize, positionSize, positionSize), 4)

    for moveRow, moveColumn in possibleMoves:
        x, y = moveColumn * positionSize, moveRow * positionSize
        if board.getPiece(moveRow, moveColumn) != "":
            screen.blit(overlays["red"], (x, y))
        else:
            screen.blit(overlays["green"], (x, y))

    if board.kingCheck(board.turnColour):
        king = board.findKing(board.turnColour)
        if king:
            screen.blit(overlays["red"], (king[1] * positionSize, king[0] * positionSize))

def squareCenter(square):
    row, column = square
    offset = positionSize / 2
    return (column * positionSize + offset, row * positionSize + offset)

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
        screen.blit(overlays["green"], (column * positionSize, row * positionSize))

    arrowSurf = pygame.Surface((windowSize, windowSize), pygame.SRCALPHA)
    arrowColor = (0, 255, 0, 150)

    for startSquare, endSquare in lines:
        drawArrow(arrowSurf, arrowColor, squareCenter(startSquare), squareCenter(endSquare))

    if rightClickStart and temporaryLine:
        drawArrow(arrowSurf, (0, 187, 0, 150), squareCenter(rightClickStart), temporaryLine)

    screen.blit(arrowSurf, (0, 0))