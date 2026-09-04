import pygame
import pygame.freetype
import math
from engine import constants
from engine.constants import windowSize, positionSize, piecesTextures, overlays, botColour, empty, white, knight, bishop, rook, queen

pygame.init()
pygame.mixer.init()
pygame.font.init()
pygame.freetype.init()

redraw = True
screen = pygame.display.get_surface()
pygame.display.set_caption("Gun's Chess Bot")
icon = pygame.image.load('images/icon.png')
pygame.display.set_icon(icon)

clock = pygame.time.Clock()
try:
    gameFont = pygame.freetype.SysFont("dynapuffregular", 64, bold=True) 
except:
    gameFont = pygame.freetype.SysFont(None, 64, bold=True)

promotionActive = False
activeSquare = None
possibleMoves = []
lines = []
rightClickStart = None
temporaryLine = None
strategyCircles = []
lastMove = None

def getDrawPos(row, col):
    if botColour == white:
        return 7 - row, 7 - col
    return row, col

def drawBoard(board):
    global lastMove
    for column in range(0, 8):
        for row in range(0, 8):
            drawRow, drawCol = getDrawPos(row, column)
            color = "#ffffff" if ((row + column) % 2 == 0) else "#0088ff"
            if lastMove:
                startRow, startColumn, endRow, endColumn = lastMove
                if column == startColumn and row == startRow:
                    color = "#97C997"
                    piecePremove = True
                elif column == endColumn and row == endRow:
                    color = "#8DCE8D"
                    premoveDestination = board.squarePiece[move[0] * 8 + move[1]]

            for move in constants.premoves:
                startRow, startColumn, endRow, endColumn = move
                if column == startColumn and row == startRow:
                    color = "#DD9048"
                elif column == endColumn and row == endRow:
                    color = "#DFAD63"

            pygame.draw.rect(screen, color, (drawCol * positionSize, drawRow * positionSize, positionSize, positionSize))

            piece = board.squarePiece[row * 8 + column]

            if piece != empty and not piecePremove and not premoveDestination:
                screen.blit(piecesTextures[piece], (drawCol * positionSize, drawRow * positionSize))

            if premoveDestination != empty:
                texture = piecesTextures[premoveDestination].copy()
                texture.set_alpha(150)
                screen.blit(texture, (drawCol * positionSize, drawRow * positionSize))

def blurSurface(surface, scaleFactor=3):
    if scaleFactor <= 1: return surface.copy()
    width = max(1, surface.get_width() // scaleFactor)
    height = max(1, surface.get_height() // scaleFactor)
    scaled = pygame.transform.smoothscale(surface, (width, height))
    return pygame.transform.smoothscale(scaled, surface.get_size())

def choosePromotion(colour):
    global promotionActive
    promotionActive = True
    piecesToChoose = [queen, knight, rook, bishop]
    
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
                    index = (mouseX - menuX) // positionSize
                    chosenPiece = colour | piecesToChoose[index]
                    promotionActive = False

        screen.blit(blurredBackground, (0, 0))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (255, 255, 255), (menuX, menuY, menuWidth, positionSize))
        pygame.draw.rect(screen, (0, 0, 0), (menuX, menuY, menuWidth, positionSize), 4)
        
        for i, piece in enumerate(piecesToChoose):
            screen.blit(piecesTextures[colour | piece], (menuX + (i * positionSize), menuY))
            
        pygame.display.flip()
        clock.tick(60)
        
    return chosenPiece

def drawHighlights(board):
    if activeSquare:
        row, column = activeSquare
        drawRow, drawColumn = getDrawPos(row, column)
        pygame.draw.rect(screen, (0, 255, 0), (drawColumn * positionSize, drawRow * positionSize, positionSize, positionSize), 4)

    for moveRow, moveColumn in possibleMoves:
        drawRow, drawColumn = getDrawPos(moveRow, moveColumn)
        x, y = drawColumn * positionSize, drawRow * positionSize
        if board.squarePiece[moveRow * 8 + moveColumn] != empty:
            screen.blit(overlays["red"], (x, y))
        else:
            if board.turnColour != botColour:
                screen.blit(overlays["green"], (x, y))
            else:
                screen.blit(overlays["orange"], (x, y))

    if board.kingCheck(board.turnColour):
        king = board.findKing(board.turnColour)
        if king:
            drawRow, drawColumn = getDrawPos(king[0], king[1])
            screen.blit(overlays["red"], (drawColumn * positionSize, drawRow * positionSize))

def squareCentre(square):
    row, column = square
    drawRow, drawColumn = getDrawPos(row, column)
    offset = positionSize / 2
    return (drawColumn * positionSize + offset, drawRow * positionSize + offset)

def drawKnightArrow(surface, color, startSquare, endSquare, thickness=25, arrowSize=50):
    startRow, startCol = startSquare
    endRow, endCol = endSquare
    
    if abs(startRow - endRow) == 2:
        corner = (endRow, startCol)
    else:
        corner = (startRow, endCol)
        
    startCentre = squareCentre(startSquare)
    cornerCentre = squareCentre(corner)
    endCentre = squareCentre(endSquare)
    
    radius = thickness / 2
    
    dx = cornerCentre[0] - startCentre[0]
    dy = cornerCentre[1] - startCentre[1]
    length = math.hypot(dx, dy)
    
    if length > 0:
        dir_x, dir_y = dx / length, dy / length
        perp_x, perp_y = -dir_y, dir_x
        
        p1 = (startCentre[0] + perp_x * radius, startCentre[1] + perp_y * radius)
        p2 = (startCentre[0] - perp_x * radius, startCentre[1] - perp_y * radius)
        p3 = (cornerCentre[0] - perp_x * radius, cornerCentre[1] - perp_y * radius)
        p4 = (cornerCentre[0] + perp_x * radius, cornerCentre[1] + perp_y * radius)
        
        pygame.draw.circle(surface, color, startCentre, radius)
        pygame.draw.polygon(surface, color, [p1, p2, p3, p4])
        
    drawArrow(surface, color, cornerCentre, endCentre, thickness, arrowSize)

def drawArrow(surface, color, start, end, thickness=25, arrowSize=50):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    if length == 0: 
        return

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
        drawRow, drawColumn = getDrawPos(row, column)
        screen.blit(overlays["green"], (drawColumn * positionSize, drawRow * positionSize))

    arrowSurf = pygame.Surface((windowSize, windowSize), pygame.SRCALPHA)
    
    arrowColor = (0, 255, 0, 255)
    dragColor = (0, 187, 0, 255)

    for startSquare, endSquare in lines:
        dr = abs(startSquare[0] - endSquare[0])
        dc = abs(startSquare[1] - endSquare[1])
        
        if (dr == 2 and dc == 1) or (dr == 1 and dc == 2):
            drawKnightArrow(arrowSurf, arrowColor, startSquare, endSquare)
        else:
            drawArrow(arrowSurf, arrowColor, squareCentre(startSquare), squareCentre(endSquare))

    if rightClickStart and temporaryLine:
        drawCol = temporaryLine[0] // positionSize
        drawRow = temporaryLine[1] // positionSize
        endSquare = (7 - drawRow, 7 - drawCol) if botColour == white else (drawRow, drawCol)
            
        dr = abs(rightClickStart[0] - endSquare[0])
        dc = abs(rightClickStart[1] - endSquare[1])
        
        if (dr == 2 and dc == 1) or (dr == 1 and dc == 2):
            drawKnightArrow(arrowSurf, dragColor, rightClickStart, endSquare)
        else:
            drawArrow(arrowSurf, dragColor, squareCentre(rightClickStart), temporaryLine)

    arrowSurf.fill((255, 255, 255, 150), special_flags=pygame.BLEND_RGBA_MULT)

    screen.blit(arrowSurf, (0, 0))